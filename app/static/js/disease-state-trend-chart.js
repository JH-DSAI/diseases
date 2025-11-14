/**
 * Disease State Trend Chart
 * D3.js multi-line chart for displaying disease case trends by state over time
 */

/**
 * Create a multi-line chart showing disease trends by state
 * @param {string} containerId - ID of the container element
 * @param {Object} data - Data object with states, national, and available_states
 * @param {string} diseaseName - Name of the disease
 * @param {Array} selectedStates - Array of state names to display (all if empty)
 */
function createDiseaseStateTrendChart(containerId, data, diseaseName, selectedStates = []) {
    // Clear any existing chart
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Validate data
    if (!data || !data.states || !data.national || !data.available_states) {
        d3.select(`#${containerId}`)
            .append("div")
            .attr("class", "flex items-center justify-center h-96")
            .append("p")
            .attr("class", "text-base-content/50")
            .text("No data available");
        return;
    }

    // If no states selected, show all states
    if (selectedStates.length === 0) {
        selectedStates = data.available_states;
    }

    // Chart dimensions
    const container = document.getElementById(containerId);
    const containerWidth = container.clientWidth;
    const margin = { top: 30, right: 150, bottom: 60, left: 80 };
    const width = containerWidth - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

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

    // Create SVG
    const svg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Get date extent across all data
    let allDates = [];
    statesData.forEach(s => {
        allDates = allDates.concat(s.values.map(v => v.date));
    });

    // X scale
    const x = d3.scaleTime()
        .domain(d3.extent(allDates))
        .range([0, width]);

    // Y scale - find max across all selected states and national
    let maxCases = 0;
    statesData.forEach(s => {
        const stateMax = d3.max(s.values, d => d.cases);
        if (stateMax > maxCases) maxCases = stateMax;
    });

    const y = d3.scaleLinear()
        .domain([0, maxCases])
        .nice()
        .range([height, 0]);

    // Color scale - use different colors for states, special color for national
    const colorScale = d3.scaleOrdinal()
        .domain(statesData.map(d => d.state))
        .range([
            '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
            '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#84cc16',
            '#a855f7', '#6366f1', '#22c55e', '#eab308', '#d946ef'
        ]);

    // Override color for National Total
    const getColor = (state) => {
        if (state === 'National Total') return '#1f2937'; // Dark gray for national
        return colorScale(state);
    };

    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.cases))
        .defined(d => d.date !== null && d.cases !== null);

    // Add X axis
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat("%b %Y")))
        .selectAll("text")
        .style("font-size", "10px")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis
    svg.append("g")
        .call(d3.axisLeft(y).ticks(8))
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
        .text("Cases");

    // Add lines for each state
    const lines = svg.selectAll(".state-line")
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
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width + 20}, 0)`);

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

    // Add invisible overlay for tooltip
    const focus = svg.append("g")
        .style("display", "none");

    // Add circles for each line
    statesData.forEach((stateData) => {
        focus.append("circle")
            .attr("class", `focus-circle-${stateData.state.replace(/\s+/g, '-')}`)
            .attr("r", 4)
            .attr("fill", getColor(stateData.state))
            .attr("stroke", "#fff")
            .attr("stroke-width", 2);
    });

    svg.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .style("fill", "none")
        .style("pointer-events", "all")
        .on("mouseover", () => focus.style("display", null))
        .on("mouseout", () => {
            focus.style("display", "none");
            tooltip.style("visibility", "hidden");
        })
        .on("mousemove", function(event) {
            const x0 = x.invert(d3.pointer(event, this)[0]);

            let tooltipContent = `<strong>${d3.timeFormat("%B %Y")(x0)}</strong><br/>`;

            statesData.forEach((stateData) => {
                // Find closest data point
                const bisect = d3.bisector(d => d.date).left;
                const i = bisect(stateData.values, x0, 1);
                const d0 = stateData.values[i - 1];
                const d1 = stateData.values[i];
                const d = d1 && d0 ? (x0 - d0.date > d1.date - x0 ? d1 : d0) : (d0 || d1);

                if (d) {
                    const circle = focus.select(`.focus-circle-${stateData.state.replace(/\s+/g, '-')}`);
                    circle.attr("cx", x(d.date))
                          .attr("cy", y(d.cases));

                    const stateName = stateData.state === 'National Total'
                        ? `<strong>${stateData.state}</strong>`
                        : stateData.state;
                    tooltipContent += `${stateName}: ${d.cases.toLocaleString()}<br/>`;
                }
            });

            tooltip.style("visibility", "visible")
                .html(tooltipContent);

            tooltip.style("top", (event.pageY - 10) + "px")
                .style("left", (event.pageX + 10) + "px");
        });
}
