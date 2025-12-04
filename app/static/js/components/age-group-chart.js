/**
 * Age Group Distribution Chart
 * Pure D3.js function that returns an SVG node for displaying age group distribution by state
 */

/**
 * Create a 100% stacked bar chart showing age group distribution by state
 * @param {Object} data - Data object with states, age_groups, and available_states
 * @param {string} diseaseName - Name of the disease
 * @param {Array} selectedStates - Array of state names to display
 * @param {Object} options - Optional configuration {width, height}
 * @returns {SVGElement} The SVG element node
 */
function createAgeGroupChart(data, diseaseName, selectedStates = [], options = {}) {
    const width = options.width || 800;
    const height = options.height || 450;
    const margin = { top: 30, right: 150, bottom: 80, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create detached SVG
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto");

    // Validate data
    if (!data || !data.states || !data.age_groups || !data.available_states) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .text("No age group data available");
        return svg.node();
    }

    // Filter for selected states
    const statesToShow = selectedStates.length > 0 ? selectedStates : [];

    if (statesToShow.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .text("Select states to view age group distribution");
        return svg.node();
    }

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Prepare data in "wide format" for stacking
    const chartData = [];
    statesToShow.forEach(state => {
        if (data.states[state]) {
            const stateData = { state: state };
            data.age_groups.forEach(ageGroup => {
                stateData[ageGroup] = data.states[state][ageGroup]?.percentage || 0;
            });
            chartData.push(stateData);
        }
    });

    // List of subgroups (age groups)
    const subgroups = data.age_groups;

    // List of groups (states)
    const groups = chartData.map(d => d.state);

    // X scale for states
    const x = d3.scaleBand()
        .domain(groups)
        .range([0, innerWidth])
        .padding(0.2);

    // Y scale for percentages (0-100%)
    const y = d3.scaleLinear()
        .domain([0, 100])
        .range([innerHeight, 0]);

    // Color scale for age groups
    const color = d3.scaleOrdinal()
        .domain(subgroups)
        .range([
            '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
            '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#84cc16'
        ]);

    // Stack the data
    const stackedData = d3.stack()
        .keys(subgroups)
        (chartData);

    // Add X axis (states)
    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .style("font-size", "10px")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis (percentage)
    g.append("g")
        .call(d3.axisLeft(y).ticks(10).tickFormat(d => d + "%"))
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
        .text("Percentage of Cases");

    // Show the bars (stacked)
    g.append("g")
        .selectAll("g")
        .data(stackedData)
        .enter().append("g")
        .attr("fill", d => color(d.key))
        .selectAll("rect")
        .data(d => d)
        .enter().append("rect")
        .attr("x", d => x(d.data.state))
        .attr("y", d => y(d[1]))
        .attr("height", d => y(d[0]) - y(d[1]))
        .attr("width", x.bandwidth())
        .style("opacity", 0.9)
        .append("title")
        .text(d => {
            const ageGroup = d3.select(this.parentNode.parentNode).datum().key;
            return `${d.data.state} - ${ageGroup}: ${(d[1] - d[0]).toFixed(1)}%`;
        });

    // Add legend
    const legend = g.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${innerWidth + 20}, 0)`);

    const legendItems = legend.selectAll(".legend-item")
        .data(subgroups)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(0, ${i * 20})`);

    legendItems.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", d => color(d));

    legendItems.append("text")
        .attr("x", 20)
        .attr("y", 12)
        .style("font-size", "10px")
        .text(d => d);

    return svg.node();
}
