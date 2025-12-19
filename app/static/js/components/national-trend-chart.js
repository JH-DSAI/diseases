/**
 * National Disease Trend Chart
 * Pure D3.js function that returns an SVG node for displaying national disease case trends
 */

/**
 * Create a line chart showing national disease trends
 * @param {Array} data - Array of {period, total_cases} objects
 * @param {string} diseaseName - Name of the disease
 * @param {Object} options - Optional configuration {width, height}
 * @returns {SVGElement} The SVG element node
 */
function createNationalTrendChart(data, diseaseName, options = {}) {
    const width = options.width || 400;
    const height = options.height || 205;
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create detached SVG with accessibility attributes
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("role", "img")
        .attr("aria-label", `National trend chart showing ${diseaseName} cases over time`)
        .style("width", "100%")
        .style("height", "auto");

    // Validate data
    if (!data || !Array.isArray(data) || data.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .attr("class", "text-base-content/50")
            .style("font-size", "14px")
            .text("No data available");
        return svg.node();
    }

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Parse dates
    const parseDate = d3.timeParse("%Y-%m-%d");
    const chartData = data.map(d => ({
        date: parseDate(d.period),
        cases: +d.total_cases
    })).filter(d => d.date !== null);

    // X scale
    const x = d3.scaleTime()
        .domain(d3.extent(chartData, d => d.date))
        .range([0, innerWidth]);

    // Y scale
    const y = d3.scaleLinear()
        .domain([0, d3.max(chartData, d => d.cases)])
        .nice()
        .range([innerHeight, 0]);

    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.cases))
        .defined(d => d.date !== null && d.cases !== null);

    // Add X axis
    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).ticks(5).tickFormat(d3.timeFormat("%b %Y")))
        .selectAll("text")
        .style("font-size", "10px")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis
    g.append("g")
        .call(d3.axisLeft(y).ticks(5))
        .selectAll("text")
        .style("font-size", "10px");

    // Add Y axis label
    g.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x", 0 - (innerHeight / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .style("font-size", "11px")
        .text("Cases");

    // Add the line
    g.append("path")
        .datum(chartData)
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", "#3b82f6")
        .attr("stroke-width", 2.5)
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("d", line);

    // Add dots
    g.selectAll(".dot")
        .data(chartData)
        .enter()
        .append("circle")
        .attr("class", "dot")
        .attr("cx", d => x(d.date))
        .attr("cy", d => y(d.cases))
        .attr("r", 4)
        .attr("fill", "#3b82f6")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5);

    // Add tooltip behavior (using title for simplicity in pure function)
    g.selectAll(".dot")
        .append("title")
        .text(d => `${d3.timeFormat("%B %Y")(d.date)}: ${d.cases.toLocaleString()} cases`);

    return svg.node();
}
