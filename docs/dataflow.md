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
│  │ Data API: /api/diseases, /api/timeseries/..., etc.                  │   │
│  │  - RESTful JSON endpoints for programmatic access                   │   │
│  │  - Typed responses with Pydantic models                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SQL API: /api/query                                                 │   │
│  │  - Accepts SQL queries from Mosaic coordinator                      │   │
│  │  - Returns JSON data for cross-filter interactions                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │ DuckDB (database.py)                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Three API Patterns

### HTML API (Initial Load)

The HTML API returns complete HTML partials with embedded JSON data:

- **Endpoint**: `/api/html/disease/{slug}/timeseries`
- **Returns**: HTML partial containing:
  - Chart container elements
  - `<script type="application/json">` with embedded data
- **Loaded by**: HTMX on page load
- **Purpose**: Fast initial render without additional network requests

### Data API (Programmatic Access)

The Data API provides structured JSON endpoints for external consumers:

- **Base path**: `/api/`
- **Endpoints**:
  - `GET /api/health` - Health check
  - `GET /api/diseases` - List all diseases with metadata
  - `GET /api/stats` - Summary statistics across all diseases
  - `GET /api/timeseries/national/{disease_slug}` - National time series
  - `GET /api/timeseries/states/{disease_slug}` - State-level time series
  - `GET /api/disease/{disease_slug}/stats` - Disease-specific statistics
  - `GET /api/disease/{disease_slug}/age-groups` - Age group distribution
  - `GET /api/disease/{disease_slug}/state-totals` - Case totals by state
- **Returns**: Typed JSON responses with Pydantic models
- **Purpose**: External integrations, data exports, programmatic access
- **Docs**: Available at `/docs` (Swagger UI) and `/redoc`

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

For interactive cross-filtering, components use the Mosaic coordinator and shared selections.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Shared State (mosaic-state.js)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ stateSelection = Mosaic.Selection()                      │   │
│  │ coordinator = Mosaic.Coordinator()                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────┐       ┌─────────────────────┐
│ State Trend Chart   │       │ USA Map             │
│ - Publishes to      │       │ - Subscribes to     │
│   stateSelection    │       │   stateSelection    │
└─────────────────────┘       └─────────────────────┘
```

### Key Concepts

1. **Mosaic Selection**: Shared filter state that multiple charts can subscribe to
2. **Mosaic Coordinator**: Routes SQL queries to the REST connector
3. **REST Connector**: Sends queries to `/api/query` endpoint
4. **Lazy Initialization**: Coordinator/Selection created on first use, not at page load

### Shared State Module

The `mosaic-state.js` module provides lazy-initialized shared state:

```javascript
// app/static/js/lib/mosaic-state.js
let coordinator = null;
let stateSelection = null;

function getCoordinator() {
    if (!coordinator) {
        coordinator = new window.Mosaic.Coordinator();
        coordinator.databaseConnector(window.createRestConnector());
    }
    return coordinator;
}

function getStateSelection() {
    if (!stateSelection) {
        stateSelection = new window.Mosaic.Selection();
    }
    return stateSelection;
}

// Exposed globally as window.MosaicState
```

### Local vs Shared State

| State Type | Scope | Example | Storage |
|------------|-------|---------|---------|
| **Shared** | Cross-chart | State selection, date range | Mosaic Selection |
| **Local** | Single component | Search filter, hover state | Component context |

- **Shared state** (via Mosaic Selection): When one chart's selection should update other charts
- **Local state** (in component context): UI-only state like search filters that don't affect other charts

### Usage in Components

```javascript
// In action()
case 'SELECT_STATE':
    // Update shared Mosaic selection (triggers other chart updates)
    const selection = window.MosaicState.getStateSelection();
    selection.update({ clauses: [{ state: payload.state }] });
    // Also update local state
    selectedStates.add(payload.state);
    return filterData(originalData, selectedStates);

case 'SEARCH_STATES':
    // Local UI state only - doesn't affect other charts
    setSearchFilter(payload.filter);
    return filterData(originalData, selectedStates);
```

## Security Considerations

The SQL API validates queries:

1. **SELECT only**: Rejects mutations (INSERT, UPDATE, DELETE)
2. **Table whitelist**: Only allows queries on specific tables
3. **Query timeout**: Limits execution time
4. **Rate limiting**: Prevents abuse
