/**
 * Age Group Distribution Chart
 * D3.js grouped bar chart for displaying age group distribution by state
 */

/**
 * Create a grouped bar chart showing age group distribution by state
 * @param {string} containerId - ID of the container element
 * @param {Object} data - Data object with states, age_groups, and available_states
 * @param {string} diseaseName - Name of the disease
 * @param {Array} selectedStates - Array of state names to display
 */
function createAgeGroupChart(containerId, data, diseaseName, selectedStates = []) {
    // Clear any existing chart
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Validate data
    if (!data || !data.states || !data.age_groups || !data.available_states) {
        d3.select(`#${containerId}`)
            .append("div")
            .attr("class", "flex items-center justify-center h-96")
            .append("p")
            .attr("class", "text-base-content/50")
            .text("No age group data available");
        return;
    }

    // Filter for selected states (or show message if none selected)
    const statesToShow = selectedStates.length > 0 ? selectedStates : [];

    if (statesToShow.length === 0) {
        d3.select(`#${containerId}`)
            .append("div")
            .attr("class", "flex items-center justify-center h-96")
            .append("p")
            .attr("class", "text-base-content/50")
            .text("Select states to view age group distribution");
        return;
    }

    // Chart dimensions
    const container = document.getElementById(containerId);
    const containerWidth = container.clientWidth;
    const margin = { top: 30, right: 150, bottom: 80, left: 60 };
    const width = containerWidth - margin.left - margin.right;
    const height = 450 - margin.top - margin.bottom;

    // Prepare data for grouped bar chart
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

    // Create SVG
    const svg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // X scale for states
    const x0 = d3.scaleBand()
        .domain(chartData.map(d => d.state))
        .rangeRound([0, width])
        .paddingInner(0.1);

    // X scale for age groups within each state
    const x1 = d3.scaleBand()
        .domain(data.age_groups)
        .rangeRound([0, x0.bandwidth()])
        .padding(0.05);

    // Y scale for percentages
    const y = d3.scaleLinear()
        .domain([0, 100])
        .nice()
        .range([height, 0]);

    // Color scale for age groups
    const colorScale = d3.scaleOrdinal()
        .domain(data.age_groups)
        .range([
            '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
            '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#84cc16'
        ]);

    // Add X axis (states)
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x0))
        .selectAll("text")
        .style("font-size", "10px")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis (percentage)
    svg.append("g")
        .call(d3.axisLeft(y).ticks(10).tickFormat(d => d + "%"))
        .selectAll("text")
        .style("font-size", "10px");

    // Add Y axis label
    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x", 0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "600")
        .text("Percentage of Cases");

    // Add grouped bars
    const stateGroups = svg.selectAll(".state-group")
        .data(chartData)
        .enter()
        .append("g")
        .attr("class", "state-group")
        .attr("transform", d => `translate(${x0(d.state)},0)`);

    stateGroups.selectAll("rect")
        .data(d => {
            return data.age_groups.map(ageGroup => {
                return {
                    ageGroup: ageGroup,
                    percentage: d[ageGroup] || 0,
                    state: d.state
                };
            });
        })
        .enter()
        .append("rect")
        .attr("x", d => x1(d.ageGroup))
        .attr("y", d => y(d.percentage))
        .attr("width", x1.bandwidth())
        .attr("height", d => height - y(d.percentage))
        .attr("fill", d => colorScale(d.ageGroup))
        .style("opacity", 0.9);

    // Add legend
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width + 20}, 0)`);

    const legendItems = legend.selectAll(".legend-item")
        .data(data.age_groups)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(0, ${i * 20})`);

    legendItems.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", d => colorScale(d));

    legendItems.append("text")
        .attr("x", 20)
        .attr("y", 12)
        .style("font-size", "10px")
        .text(d => d);

    // Add tooltip
    const tooltip = d3.select("body")
        .append("div")
        .attr("class", "age-group-tooltip")
        .style("position", "absolute")
        .style("visibility", "hidden")
        .style("background-color", "oklch(var(--b1))")
        .style("border", "1px solid oklch(var(--bc) / 0.2)")
        .style("border-radius", "0.5rem")
        .style("padding", "0.5rem")
        .style("font-size", "12px")
        .style("pointer-events", "none")
        .style("z-index", "1000");

    // Add tooltip interaction to bars
    stateGroups.selectAll("rect")
        .on("mouseover", function(event, d) {
            d3.select(this).style("opacity", 1);
            tooltip.style("visibility", "visible")
                .html(`<strong>${d.state}</strong><br/>${d.ageGroup}: ${d.percentage.toFixed(1)}%`);
        })
        .on("mousemove", function(event) {
            tooltip.style("top", (event.pageY - 10) + "px")
                .style("left", (event.pageX + 10) + "px");
        })
        .on("mouseout", function() {
            d3.select(this).style("opacity", 0.9);
            tooltip.style("visibility", "hidden");
        });
}
