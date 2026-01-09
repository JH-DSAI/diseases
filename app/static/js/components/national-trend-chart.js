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

/**
 * Create a bar chart showing national disease trends (monthly cases)
 * @param {Array} data - Array of {period, total_cases} objects
 * @param {string} diseaseName - Name of the disease
 * @param {Object} options - Optional configuration {width, height, color}
 * @returns {Object} { svg: SVGElement, total: number, startDate: string, endDate: string }
 */
function createNationalTrendBarChart(data, diseaseName, options = {}) {
    const width = options.width || 420;
    const height = options.height || 200;
    const color = options.color || '#3b82f6';
    const margin = { top: 10, right: 10, bottom: 7, left: 45 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create detached SVG with accessibility attributes
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("role", "img")
        .attr("aria-label", `Monthly cases bar chart for ${diseaseName}`)
        .style("width", "100%")
        .style("height", "auto");

    // Validate data
    if (!data || !Array.isArray(data) || data.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .style("fill", "#666")
            .text("No data available");
        return { svg: svg.node(), total: 0, startDate: null, endDate: null };
    }

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Parse dates and sort data
    const parseDate = d3.timeParse("%Y-%m-%d");
    const chartData = data.map(d => ({
        date: parseDate(d.period),
        cases: +d.total_cases,
        period: d.period
    })).filter(d => d.date !== null)
      .sort((a, b) => a.date - b.date);

    // Take only the last 12 months of data
    const last12Months = chartData.slice(-12);

    // X scale (band scale for bars)
    const x = d3.scaleBand()
        .domain(last12Months.map(d => d.period))
        .range([0, innerWidth])
        .padding(0.1);

    // Y scale
    const maxCases = d3.max(last12Months, d => d.cases) || 100;
    const y = d3.scaleLinear()
        .domain([0, maxCases])
        .nice()
        .range([innerHeight, 0]);

    // Add Y axis gridlines first (full width)
    const yTicks = y.ticks(5);
    g.selectAll(".gridline")
        .data(yTicks)
        .enter()
        .append("line")
        .attr("class", "gridline")
        .attr("x1", -margin.left)
        .attr("x2", innerWidth)
        .attr("y1", d => y(d))
        .attr("y2", d => y(d))
        .attr("stroke", "#e5e5e5")
        .attr("stroke-width", 1);

    // Add Y axis labels with background (using foreignObject for CSS styling)
    yTicks.forEach(tick => {
        const yPos = y(tick);
        const labelText = tick.toLocaleString();

        g.append("foreignObject")
            .attr("x", -margin.left)
            .attr("y", yPos - 10)
            .attr("width", margin.left)
            .attr("height", 20)
            .append("xhtml:span")
            .attr("class", "chart-y-label")
            .text(labelText);
    });

    // Add bars
    g.selectAll(".bar")
        .data(last12Months)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.period))
        .attr("y", d => y(d.cases))
        .attr("width", x.bandwidth())
        .attr("height", d => innerHeight - y(d.cases))
        .attr("fill", color)
        .attr("rx", 2)
        .attr("ry", 2);

    // Add tooltip behavior using title elements
    g.selectAll(".bar")
        .append("title")
        .text(d => `${d3.timeFormat("%B %Y")(d.date)}: ${d.cases.toLocaleString()} cases`);

    // Calculate metadata for HTML rendering
    const formatDate = d3.timeFormat("%B %Y");
    const firstDate = last12Months.length > 0 ? last12Months[0].date : null;
    const lastDate = last12Months.length > 0 ? last12Months[last12Months.length - 1].date : null;
    const totalCases = last12Months.reduce((sum, d) => sum + d.cases, 0);

    return {
        svg: svg.node(),
        total: totalCases,
        startDate: firstDate ? formatDate(firstDate) : null,
        endDate: lastDate ? formatDate(lastDate) : null
    };
}
