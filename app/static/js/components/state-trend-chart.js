/**
 * State Trend Chart - Loader/Action/Render pattern
 *
 * This component displays disease case trends by state with cross-filtering support.
 * It uses the Remix-style loader/action/render pattern:
 * - loader: Transforms embedded JSON (no fetch on initial render)
 * - action: Handles user interactions via SQL API
 * - render: Pure function that returns SVG elements
 */

/**
 * Loader: Process embedded JSON data from HTML partial.
 * No network fetch - uses data already embedded by server.
 *
 * @param {Object} embeddedData - Data from <script type="application/json">
 * @param {string} diseaseSlug - Disease identifier for SQL queries
 * @returns {Object} Context with rowData, lineData, selection, diseaseSlug, originalData
 */
function loader(embeddedData, diseaseSlug) {
    // Transform embedded JSON for row chart (state totals)
    const rowData = Object.entries(embeddedData.states || {}).map(([state, points]) => ({
        state,
        total: points.reduce((sum, p) => sum + (p.cases || 0), 0)
    })).sort((a, b) => b.total - a.total);

    // Add National to row data
    if (embeddedData.national) {
        const nationalTotal = embeddedData.national.reduce((sum, p) => sum + (p.cases || 0), 0);
        rowData.unshift({ state: 'National', total: nationalTotal });
    }

    // Transform embedded JSON for line chart (time series)
    const lineData = [];
    for (const [state, points] of Object.entries(embeddedData.states || {})) {
        points.forEach(p => lineData.push({
            state,
            date: new Date(p.period),
            cases: p.cases || 0
        }));
    }

    // Add national data
    if (embeddedData.national) {
        embeddedData.national.forEach(p => lineData.push({
            state: 'National',
            date: new Date(p.period),
            cases: p.cases || 0
        }));
    }

    // Store current selection (for multi-select support)
    const selectedStates = new Set();

    return {
        rowData,
        lineData,
        selectedStates,
        diseaseSlug,
        originalData: { rowData, lineData }
    };
}

/**
 * Action: Handle user interactions.
 *
 * @param {string} type - Action type: 'SELECT_STATE', 'TOGGLE_STATE', 'CLEAR_FILTER'
 * @param {Object} payload - Action payload
 * @param {Object} context - Context from loader + coordinator
 * @returns {Object} Updated data { rowData, lineData }
 */
async function action(type, payload, context) {
    const { coordinator, selectedStates, diseaseSlug, originalData } = context;

    switch (type) {
        case 'SELECT_STATE': {
            // Single select (replace selection)
            selectedStates.clear();
            if (payload.state !== 'National') {
                selectedStates.add(payload.state);
            }
            return filterData(originalData, selectedStates);
        }

        case 'TOGGLE_STATE': {
            // Multi-select (shift+click)
            if (payload.state === 'National') {
                // Clicking National clears selection
                selectedStates.clear();
            } else if (selectedStates.has(payload.state)) {
                selectedStates.delete(payload.state);
            } else {
                selectedStates.add(payload.state);
            }
            return filterData(originalData, selectedStates);
        }

        case 'CLEAR_FILTER': {
            selectedStates.clear();
            return originalData;
        }

        default:
            throw new Error(`Unknown action: ${type}`);
    }
}

/**
 * Filter data based on selected states.
 * Uses client-side filtering of embedded data (no SQL API call).
 */
function filterData(originalData, selectedStates) {
    if (selectedStates.size === 0) {
        return originalData;
    }

    // Filter line data to show only selected states + National
    const filteredLineData = originalData.lineData.filter(d =>
        d.state === 'National' || selectedStates.has(d.state)
    );

    return {
        rowData: originalData.rowData,
        lineData: filteredLineData
    };
}

/**
 * Render: Pure function that creates SVG elements.
 *
 * @param {Object} data - { rowData, lineData }
 * @param {Function} dispatch - Dispatch function for actions
 * @param {Object} options - Render options { selectedStates }
 * @returns {Object} { rowSvg, lineSvg } - SVG element nodes
 */
function render(data, dispatch, options = {}) {
    const { rowData, lineData } = data;
    const { selectedStates = new Set() } = options;

    // Create row chart (state filter)
    const rowSvg = createRowChart(rowData, dispatch, selectedStates);

    // Create line chart (time series)
    const lineSvg = createLineChart(lineData, selectedStates);

    return { rowSvg, lineSvg };
}

/**
 * Create row chart for state filtering.
 */
function createRowChart(rowData, dispatch, selectedStates) {
    const width = 180;
    const barHeight = 18;
    const margin = { top: 10, right: 10, bottom: 20, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const height = Math.max(200, rowData.length * barHeight + margin.top + margin.bottom);

    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto")
        .style("max-height", "350px")
        .style("overflow-y", "auto");

    if (!rowData || rowData.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("No data");
        return svg.node();
    }

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // X scale (total cases)
    const maxTotal = d3.max(rowData, d => d.total);
    const x = d3.scaleLinear()
        .domain([0, maxTotal])
        .range([0, innerWidth]);

    // Y scale (states)
    const y = d3.scaleBand()
        .domain(rowData.map(d => d.state))
        .range([0, rowData.length * barHeight])
        .padding(0.1);

    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(rowData.map(d => d.state))
        .range(['#1f2937', '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
                '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#84cc16',
                '#a855f7', '#6366f1', '#22c55e', '#eab308', '#d946ef']);

    // Bars
    g.selectAll('.bar')
        .data(rowData)
        .enter()
        .append('rect')
        .attr('class', 'bar')
        .attr('x', 0)
        .attr('y', d => y(d.state))
        .attr('width', d => x(d.total))
        .attr('height', y.bandwidth())
        .attr('fill', d => colorScale(d.state))
        .attr('opacity', d => {
            if (selectedStates.size === 0) return 0.8;
            if (d.state === 'National') return 0.8;
            return selectedStates.has(d.state) ? 1 : 0.3;
        })
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
            if (event.shiftKey) {
                dispatch('TOGGLE_STATE', { state: d.state });
            } else {
                dispatch('SELECT_STATE', { state: d.state });
            }
        });

    // State labels (left side)
    g.selectAll('.label')
        .data(rowData)
        .enter()
        .append('text')
        .attr('class', 'label')
        .attr('x', -5)
        .attr('y', d => y(d.state) + y.bandwidth() / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'end')
        .style('font-size', '10px')
        .style('fill', '#374151')
        .text(d => d.state);

    // X axis
    g.append("g")
        .attr("transform", `translate(0,${rowData.length * barHeight})`)
        .call(d3.axisBottom(x).ticks(3).tickFormat(d3.format('.2s')))
        .selectAll("text")
        .style("font-size", "8px");

    return svg.node();
}

/**
 * Create multi-line chart for time series.
 */
function createLineChart(lineData, selectedStates) {
    const width = 600;
    const height = 380;
    const margin = { top: 20, right: 120, bottom: 50, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto");

    if (!lineData || lineData.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .text("No data available");
        return svg.node();
    }

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Group data by state
    const statesData = d3.groups(lineData, d => d.state)
        .map(([state, values]) => ({ state, values: values.sort((a, b) => a.date - b.date) }));

    // X scale (time)
    const x = d3.scaleTime()
        .domain(d3.extent(lineData, d => d.date))
        .range([0, innerWidth]);

    // Y scale (cases)
    const y = d3.scaleLinear()
        .domain([0, d3.max(lineData, d => d.cases)])
        .nice()
        .range([innerHeight, 0]);

    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(statesData.map(d => d.state))
        .range(['#1f2937', '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
                '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#84cc16',
                '#a855f7', '#6366f1', '#22c55e', '#eab308', '#d946ef']);

    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.cases))
        .curve(d3.curveMonotoneX);

    // X axis
    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat("%b %Y")))
        .selectAll("text")
        .style("font-size", "10px")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Y axis
    g.append("g")
        .call(d3.axisLeft(y).ticks(8))
        .selectAll("text")
        .style("font-size", "10px");

    // Y axis label
    g.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", -margin.left + 15)
        .attr("x", -innerHeight / 2)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "600")
        .text("Cases");

    // Lines
    const lines = g.selectAll(".state-line")
        .data(statesData)
        .enter()
        .append("g")
        .attr("class", "state-line");

    lines.append("path")
        .attr("fill", "none")
        .attr("stroke", d => colorScale(d.state))
        .attr("stroke-width", d => d.state === 'National' ? 3 : 2)
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("d", d => line(d.values))
        .style("opacity", d => {
            if (selectedStates.size === 0) return d.state === 'National' ? 1 : 0.7;
            if (d.state === 'National') return 1;
            return selectedStates.has(d.state) ? 1 : 0.2;
        });

    // Data points
    lines.selectAll(".point")
        .data(d => d.values.map(v => ({ ...v, state: d.state })))
        .enter()
        .append("circle")
        .attr("class", "point")
        .attr("cx", d => x(d.date))
        .attr("cy", d => y(d.cases))
        .attr("r", d => d.state === 'National' ? 3 : 2)
        .attr("fill", d => colorScale(d.state))
        .style("opacity", d => {
            if (selectedStates.size === 0) return d.state === 'National' ? 1 : 0.5;
            if (d.state === 'National') return 1;
            return selectedStates.has(d.state) ? 1 : 0.1;
        });

    // Legend
    const legend = g.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${innerWidth + 10}, 0)`);

    const legendItems = legend.selectAll(".legend-item")
        .data(statesData)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(0, ${i * 16})`);

    legendItems.append("line")
        .attr("x1", 0)
        .attr("x2", 15)
        .attr("stroke", d => colorScale(d.state))
        .attr("stroke-width", d => d.state === 'National' ? 3 : 2);

    legendItems.append("text")
        .attr("x", 20)
        .attr("dy", "0.35em")
        .style("font-size", d => d.state === 'National' ? "10px" : "9px")
        .style("font-weight", d => d.state === 'National' ? "600" : "400")
        .text(d => d.state);

    return svg.node();
}

// Export for template
window.StateTrendChart = { loader, action, render };
