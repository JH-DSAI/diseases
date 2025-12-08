# Data Flow Architecture

This document describes the data flow architecture for the disease dashboard, including the relationship between server APIs, frontend frameworks, and visualization components.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Browser                                                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ HTMX - Loads HTML partials from HTML API                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                 │
│  ┌────────────────────────▼────────────────────────────────────────────┐   │
│  │ Alpine.js - Page reactivity, state management                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                 │
│  ┌────────────────────────▼────────────────────────────────────────────┐   │
│  │ Components (Loader/Action/Render Pattern)                           │   │
│  │  - loader(): Transform embedded JSON (no fetch!)                    │   │
│  │  - action(): Query SQL API on interaction, return data              │   │
│  │  - render(): Pure function (data, dispatch) → SVGElement            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                            │
                            │ REST POST /api/query (SQL)
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Server (FastAPI)                                                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ HTML API: /api/html/disease/{slug}/...                              │   │
│  │  - Returns HTML partials with embedded JSON data                    │   │
│  │  - Loaded by HTMX on page load                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SQL API: /api/query                                                 │   │
│  │  - Accepts SQL queries from Mosaic coordinator                      │   │
│  │  - Returns JSON data for cross-filter interactions                  │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │ DuckDB (database.py)                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Two API Patterns

### HTML API (Initial Load)

The HTML API returns complete HTML partials with embedded JSON data:

- **Endpoint**: `/api/html/disease/{slug}/timeseries`
- **Returns**: HTML partial containing:
  - Chart container elements
  - `<script type="application/json">` with embedded data
- **Loaded by**: HTMX on page load
- **Purpose**: Fast initial render without additional network requests

### SQL API (Interactions)

The SQL API accepts SQL queries for cross-filtering:

- **Endpoint**: `/api/query`
- **Accepts**: `{ sql: string, type: "json" | "arrow" }`
- **Returns**: JSON query results
- **Called by**: Mosaic coordinator when user interacts with charts
- **Purpose**: Dynamic filtering without full page reload

## Component Pattern: Loader/Action/Render

Components follow a Remix-inspired pattern with colocated data handling:

```
┌───────────────────────────────────────────────────────────────────┐
│  component.js                                                     │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ loader(embeddedData, params)                               │   │
│  │  - Receives embedded JSON from HTML partial                │   │
│  │  - Transforms data for charts (no network fetch!)          │   │
│  │  - Initializes state (e.g., Mosaic selection)              │   │
│  │  - Returns: { data, state, originalData }                  │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ action(type, payload, context)                             │   │
│  │  - Handles user interactions (like Redux reducer)          │   │
│  │  - May query SQL API for filtered results                  │   │
│  │  - Returns updated data                                    │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ render(data, dispatch) → SVGElement                        │   │
│  │  - Pure function: data in → SVG out                        │   │
│  │  - Binds dispatch(type, payload) to event handlers         │   │
│  │  - No side effects, no state                               │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **HTMX loads partial** → HTML contains `<script type="application/json">` with embedded data
2. **loader()** transforms embedded JSON → no fetch, fast initial render
3. **render()** creates SVG → mounts to DOM (synchronous)
4. **User clicks** → dispatch('ACTION_TYPE', payload)
5. **action()** may query SQL API → returns updated data
6. **render()** updates SVG with new data

### Key Benefits

- **Fast initial render**: Uses embedded data, no network request
- **Lazy initialization**: Coordinator only created when first interaction occurs
- **Reset is fast**: Returns to original embedded data, no fetch needed
- **Pure render**: Components are testable, predictable

## File Conventions

### Templates ↔ Components Relationship

| Template Partial | Component File |
|------------------|----------------|
| `app/templates/partials/timeseries_chart.html` | `app/static/js/components/state-trend-chart.js` |
| `app/templates/partials/usa_map_chart.html` | `app/static/js/components/usa-map-chart.js` |
| `app/templates/partials/age_group_chart.html` | `app/static/js/components/age-group-chart.js` |

### Template Structure

```html
{# Embedded JSON from server #}
<script type="application/json" id="chart-data">{{ data | tojson }}</script>

{# Chart containers #}
<div id="chart-container"></div>

<script>
(function() {
    const { loader, action, render } = window.ChartComponent;

    // Parse embedded data
    const embeddedData = JSON.parse(
        document.getElementById('chart-data').textContent
    );

    // Initialize
    const context = loader(embeddedData, params);
    let data = context.data;

    // Dispatch handler
    const dispatch = async (type, payload) => {
        data = await action(type, payload, context);
        updateUI();
    };

    function updateUI() {
        const svg = render(data, dispatch);
        document.getElementById('chart-container').replaceChildren(svg);
    }

    updateUI();
})();
</script>
```

### Component Structure

```javascript
// component.js

/** Loader: Transform embedded JSON */
function loader(embeddedData, params) {
    // Transform data for charts
    // Initialize state
    return { data, state, originalData };
}

/** Action: Handle interactions */
async function action(type, payload, context) {
    switch (type) {
        case 'FILTER':
            // Query SQL API for filtered data
            return await fetchFiltered(context, payload);
        case 'CLEAR':
            // Return to original data (no fetch)
            return context.originalData;
    }
}

/** Render: Pure function, data → SVG */
function render(data, dispatch, options = {}) {
    const svg = d3.create("svg")...;
    // Bindinteractions to dispatch
    svg.on('click', (e, d) => dispatch('FILTER', { value: d.value }));
    return svg.node();
}

// Export for template
window.ChartComponent = { loader, action, render };
```

## Cross-Filtering with Mosaic

For interactive cross-filtering, components use the Mosaic coordinator:

1. **Mosaic Selection**: Manages filter state across multiple charts
2. **Mosaic Coordinator**: Routes SQL queries to the server
3. **REST Connector**: Sends queries to `/api/query` endpoint

```javascript
// Lazy coordinator initialization
let coordinator = null;
function getCoordinator() {
    if (!coordinator) {
        coordinator = new Mosaic.Coordinator();
        coordinator.databaseConnector(createRestConnector());
    }
    return coordinator;
}

// In action()
case 'SELECT_STATE':
    selection.update({ predicate: `state = '${payload.state}'` });
    return await getCoordinator().query(filteredQuery);
```

## Security Considerations

The SQL API validates queries:

1. **SELECT only**: Rejects mutations (INSERT, UPDATE, DELETE)
2. **Table whitelist**: Only allows queries on specific tables
3. **Query timeout**: Limits execution time
4. **Rate limiting**: Prevents abuse
