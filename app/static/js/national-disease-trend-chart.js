/**
 * National Disease Trend Chart
 * D3.js line chart for displaying national disease case trends over time
 */

/**
 * Create a line chart showing national disease trends
 * @param {string} containerId - ID of the container element
 * @param {Array} data - Array of {period, total_cases} objects
 * @param {string} diseaseName - Name of the disease
 */
function createNationalDiseaseTrendChart(containerId, data, diseaseName) {
    // Clear any existing chart
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Validate data
    if (!data || !Array.isArray(data) || data.length === 0) {
        d3.select(`#${containerId}`)
            .append("div")
            .attr("class", "flex items-center justify-center h-48")
            .append("p")
            .attr("class", "text-base-content/50")
            .text("No data available");
        return;
    }

    // Chart dimensions
    const container = document.getElementById(containerId);
    const containerWidth = container.clientWidth;
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const width = containerWidth - margin.left - margin.right;
    const height = 200 - margin.top - margin.bottom;

    // Parse dates
    const parseDate = d3.timeParse("%Y-%m-%d");
    data.forEach(d => {
        d.date = parseDate(d.period);
        d.cases = +d.total_cases;
    });

    // Create SVG
    const svg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // X scale
    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);

    // Y scale
    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.cases)])
        .nice()
        .range([height, 0]);

    // Line generator - use linear interpolation for clear connection between points
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.cases))
        .defined(d => d.date !== null && d.cases !== null); // Skip null values

    // Add X axis
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(5).tickFormat(d3.timeFormat("%b %Y")))
        .selectAll("text")
        .style("font-size", "10px")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis
    svg.append("g")
        .call(d3.axisLeft(y).ticks(5))
        .selectAll("text")
        .style("font-size", "10px");

    // Add Y axis label
    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x", 0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .style("font-size", "11px")
        .text("Cases");

    // Add the line connecting all points
    svg.append("path")
        .datum(data)
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", "#3b82f6")
        .attr("stroke-width", 2.5)
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("d", line);

    // Add dots
    svg.selectAll("dot")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => x(d.date))
        .attr("cy", d => y(d.cases))
        .attr("r", 4)
        .attr("fill", "#3b82f6")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5);

    // Add tooltip
    const tooltip = d3.select("body")
        .append("div")
        .attr("class", "chart-tooltip")
        .style("position", "absolute")
        .style("visibility", "hidden")
        .style("background-color", "oklch(var(--b1))")
        .style("border", "1px solid oklch(var(--bc) / 0.2)")
        .style("border-radius", "0.5rem")
        .style("padding", "0.5rem")
        .style("font-size", "12px")
        .style("pointer-events", "none")
        .style("z-index", "1000");

    svg.selectAll("circle")
        .on("mouseover", function(event, d) {
            tooltip.style("visibility", "visible")
                .html(`<strong>${d3.timeFormat("%B %Y")(d.date)}</strong><br/>Cases: ${d.cases.toLocaleString()}`);
        })
        .on("mousemove", function(event) {
            tooltip.style("top", (event.pageY - 10) + "px")
                .style("left", (event.pageX + 10) + "px");
        })
        .on("mouseout", function() {
            tooltip.style("visibility", "hidden");
        });
}
