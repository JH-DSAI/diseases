/**
 * State Trend Chart - Loader/Action/Render pattern
 *
 * Displays disease case trends by state as a multi-line chart.
 * Subscribes to MosaicState for cross-chart state filtering.
 */

/**
 * Loader: Process embedded JSON data from HTML partial.
 *
 * @param {Object} embeddedData - Data from <script type="application/json">
 * @param {string} diseaseSlug - Disease identifier
 * @returns {Object} Context with rowData, lineData, originalData
 */
function loader(embeddedData, diseaseSlug) {
    // Transform embedded JSON for row data (state totals) - used for color scale
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

    return {
        rowData,
        lineData,
        diseaseSlug,
        originalData: { rowData, lineData }
    };
}

/**
 * Filter line data based on selected states.
 */
function filterLineData(originalLineData, selectedStates) {
    if (selectedStates.size === 0) {
        return originalLineData;
    }
    return originalLineData.filter(d => selectedStates.has(d.state));
}

/**
 * Filter line data based on date range.
 */
function filterByDateRange(lineData, dateRange) {
    const { startDate, endDate } = dateRange;
    if (!startDate || !endDate) {
        return lineData;
    }
    return lineData.filter(d => d.date >= startDate && d.date <= endDate);
}

/**
 * Render: Create the line chart SVG.
 *
 * @param {Object} context - Context from loader
 * @param {Set} selectedStates - Currently selected states from MosaicState
 * @param {Object} dateRange - { startDate, endDate } from MosaicState
 * @returns {SVGElement} Line chart SVG element
 */
function render(context, selectedStates = new Set(), dateRange = {}) {
    const { rowData, originalData } = context;
    let lineData = filterLineData(originalData.lineData, selectedStates);
    lineData = filterByDateRange(lineData, dateRange);

    return createLineChart(lineData, selectedStates, rowData);
}

/**
 * Create multi-line chart for time series.
 */
function createLineChart(lineData, selectedStates, rowData) {
    const width = 700;
    const height = 400;
    const margin = { top: 20, right: 140, bottom: 50, left: 60 };
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
            .style("fill", "#6b7280")
            .text(selectedStates.size > 0 ? "Select states above to view trends" : "No data available");
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

    // Color scale - use shared StateColors for consistency with state selector
    const colorScale = window.StateColors.createStateColorScale(
        statesData.map(d => d.state)
    );

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
        .attr("d", d => line(d.values));

    // Data points
    lines.selectAll(".point")
        .data(d => d.values.map(v => ({ ...v, state: d.state })))
        .enter()
        .append("circle")
        .attr("class", "point")
        .attr("cx", d => x(d.date))
        .attr("cy", d => y(d.cases))
        .attr("r", d => d.state === 'National' ? 3 : 2)
        .attr("fill", d => colorScale(d.state));

    // Legend
    const legend = g.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${innerWidth + 15}, 0)`);

    const legendItems = legend.selectAll(".legend-item")
        .data(statesData)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(0, ${i * 18})`);

    legendItems.append("line")
        .attr("x1", 0)
        .attr("x2", 18)
        .attr("y1", 0)
        .attr("y2", 0)
        .attr("stroke", d => colorScale(d.state))
        .attr("stroke-width", d => d.state === 'National' ? 3 : 2);

    legendItems.append("text")
        .attr("x", 24)
        .attr("dy", "0.35em")
        .style("font-size", "11px")
        .style("font-weight", d => d.state === 'National' ? "600" : "400")
        .text(d => d.state);

    return svg.node();
}

// Export for template
window.StateTrendChart = { loader, render };
