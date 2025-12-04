/**
 * Disease State Trend Chart
 * Pure D3.js function that returns an SVG node for displaying disease case trends by state
 */

/**
 * Create a multi-line chart showing disease trends by state
 * @param {Object} data - Data object with states, national, and available_states
 * @param {string} diseaseName - Name of the disease
 * @param {Array} selectedStates - Array of state names to display
 * @param {Object} options - Optional configuration {width, height}
 * @returns {SVGElement} The SVG element node
 */
function createStateTrendChart(data, diseaseName, selectedStates = [], options = {}) {
    const width = options.width || 800;
    const height = options.height || 400;
    const margin = { top: 30, right: 150, bottom: 60, left: 80 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create detached SVG
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto");

    // Validate data
    if (!data || !data.states || !data.national || !data.available_states) {
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

    // Parse dates
    const parseDate = d3.timeParse("%Y-%m-%d");

    // Prepare data for selected states
    const statesData = [];
    selectedStates.forEach(state => {
        if (data.states[state]) {
            const stateData = data.states[state].map(d => ({
                date: parseDate(d.period.split('T')[0]),
                cases: +d.cases,
                state: state
            }));
            statesData.push({ state: state, values: stateData });
        }
    });

    // Prepare national data
    const nationalData = data.national.map(d => ({
        date: parseDate(d.period.split('T')[0]),
        cases: +d.cases,
        state: 'National Total'
    }));
    statesData.push({ state: 'National Total', values: nationalData });

    // Get date extent across all data
    let allDates = [];
    statesData.forEach(s => {
        allDates = allDates.concat(s.values.map(v => v.date));
    });

    // X scale
    const x = d3.scaleTime()
        .domain(d3.extent(allDates))
        .range([0, innerWidth]);

    // Y scale - find max across all selected states and national
    let maxCases = 0;
    statesData.forEach(s => {
        const stateMax = d3.max(s.values, d => d.cases);
        if (stateMax > maxCases) maxCases = stateMax;
    });

    const y = d3.scaleLinear()
        .domain([0, maxCases])
        .nice()
        .range([innerHeight, 0]);

    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(statesData.map(d => d.state))
        .range([
            '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
            '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#84cc16',
            '#a855f7', '#6366f1', '#22c55e', '#eab308', '#d946ef'
        ]);

    // Override color for National Total
    const getColor = (state) => {
        if (state === 'National Total') return '#1f2937';
        return colorScale(state);
    };

    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.cases))
        .defined(d => d.date !== null && d.cases !== null);

    // Add X axis
    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat("%b %Y")))
        .selectAll("text")
        .style("font-size", "10px")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis
    g.append("g")
        .call(d3.axisLeft(y).ticks(8))
        .selectAll("text")
        .style("font-size", "10px");

    // Add Y axis label
    g.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x", 0 - (innerHeight / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "600")
        .text("Cases");

    // Add lines for each state
    const lines = g.selectAll(".state-line")
        .data(statesData)
        .enter()
        .append("g")
        .attr("class", "state-line");

    lines.append("path")
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", d => getColor(d.state))
        .attr("stroke-width", d => d.state === 'National Total' ? 3 : 2)
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("d", d => line(d.values))
        .style("opacity", d => d.state === 'National Total' ? 1 : 0.8);

    // Add legend
    const legend = g.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${innerWidth + 20}, 0)`);

    const legendItems = legend.selectAll(".legend-item")
        .data(statesData)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(0, ${i * 20})`);

    legendItems.append("line")
        .attr("x1", 0)
        .attr("x2", 20)
        .attr("y1", 0)
        .attr("y2", 0)
        .attr("stroke", d => getColor(d.state))
        .attr("stroke-width", d => d.state === 'National Total' ? 3 : 2);

    legendItems.append("text")
        .attr("x", 25)
        .attr("y", 0)
        .attr("dy", "0.35em")
        .style("font-size", d => d.state === 'National Total' ? "11px" : "10px")
        .style("font-weight", d => d.state === 'National Total' ? "600" : "400")
        .text(d => d.state);

    return svg.node();
}
