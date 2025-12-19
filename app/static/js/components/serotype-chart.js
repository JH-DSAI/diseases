/**
 * Serotype Distribution Chart
 * Pure D3.js function that returns an SVG node for displaying serotype distribution by state
 */

/**
 * Create a 100% stacked bar chart showing serotype distribution by state
 * @param {Object} data - Data object with states, serotypes, and available_states
 * @param {string} diseaseName - Name of the disease
 * @param {Array} selectedStates - Array of state names to display
 * @param {Object} options - Optional configuration {width, height}
 * @returns {SVGElement} The SVG element node
 */
function createSerotypeChart(data, diseaseName, selectedStates = [], options = {}) {
    const width = options.width || 800;
    const height = options.height || 450;
    const margin = { top: 30, right: 150, bottom: 80, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create detached SVG with accessibility attributes
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("role", "img")
        .attr("aria-label", `Serotype distribution chart for ${diseaseName} cases by state`)
        .style("width", "100%")
        .style("height", "auto");

    // Validate data
    if (!data || !data.states || !data.serotypes || !data.available_states || data.serotypes.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .text("No serotype data available");
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
            .text("Select states to view serotype distribution");
        return svg.node();
    }

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Prepare data in "wide format" for stacking
    const chartData = [];
    statesToShow.forEach(state => {
        if (data.states[state]) {
            const stateData = { state: state };
            data.serotypes.forEach(serotype => {
                stateData[serotype] = data.states[state][serotype]?.percentage || 0;
            });
            chartData.push(stateData);
        }
    });

    // List of subgroups (serotypes)
    const subgroups = data.serotypes;

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

    // ColorBrewer Dark2 palette - colorblind-friendly qualitative colors
    // https://colorbrewer2.org/
    const serotypeColors = {
        'A': '#1B9E77',       // dark teal
        'B': '#D95F02',       // dark orange
        'C': '#7570B3',       // dark lilac
        'W': '#E7298A',       // dark magenta
        'X': '#66A61E',       // dark lime
        'Y': '#E6AB02',       // dark gold
        'Z': '#A6761D',       // dark tan
        'ACWY': '#7570B3',    // dark lilac (grouped serogroups)
        'UNKNOWN': '#999999', // medium gray
        'UNSPECIFIED': '#666666' // dark gray
    };

    const color = d3.scaleOrdinal()
        .domain(subgroups)
        .range(subgroups.map(s => serotypeColors[s.toUpperCase()] || '#94a3b8'));

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
        .text(function(d) {
            const serotype = d3.select(this.parentNode.parentNode).datum().key;
            const stateData = data.states[d.data.state][serotype];
            const count = stateData ? stateData.count : 0;
            return `${d.data.state} - Serogroup ${serotype}: ${count} cases (${(d[1] - d[0]).toFixed(1)}%)`;
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
        .attr("transform", (d, i) => `translate(0, ${i * 22})`);

    legendItems.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", d => color(d));

    legendItems.append("text")
        .attr("x", 20)
        .attr("y", 12)
        .style("font-size", "11px")
        .text(d => `Serogroup ${d}`);

    return svg.node();
}
