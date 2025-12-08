/**
 * USA Choropleth Map Chart
 * Pure D3.js function that returns an SVG node for displaying disease case totals by state
 */

// FIPS to state code mapping (for tooltip display)
const FIPS_TO_STATE = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
    "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
    "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
    "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
    "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
    "56": "WY"
};

// State code to FIPS mapping
const STATE_TO_FIPS = Object.fromEntries(
    Object.entries(FIPS_TO_STATE).map(([k, v]) => [v, k])
);

/**
 * Get US TopoJSON data (bundled, no fetch needed)
 * @returns {Object} The TopoJSON data
 */
function loadUSTopology() {
    // Use pre-bundled topology from vendor.js (us-atlas npm package)
    return window.usStatesTopology;
}

/**
 * Create a USA choropleth map showing case totals by state
 * @param {Object} data - Data object with states, max_cases, min_cases, available_states
 * @param {string} diseaseName - Name of the disease
 * @param {Object} usTopology - Pre-loaded US TopoJSON data
 * @param {Object} options - Optional configuration {width, height}
 * @returns {SVGElement} The SVG element node
 */
function createUSAMapChart(data, diseaseName, usTopology, options = {}) {
    // TopoJSON viewport is 975x610 for Albers USA projection
    const width = options.width || 975;
    const height = options.height || 610;
    const legendWidth = 200;
    const legendHeight = 16;
    const legendMargin = { right: 20, bottom: 50 };

    // Create detached SVG
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto");

    // Validate data
    if (!data || !data.states || Object.keys(data.states).length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .text("No state data available");
        return svg.node();
    }

    // Validate TopoJSON
    if (!usTopology || !usTopology.objects || !usTopology.objects.states) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .text("Map data not loaded");
        return svg.node();
    }

    // Build lookup by FIPS code
    const casesByFips = {};
    for (const [stateCode, stateData] of Object.entries(data.states)) {
        casesByFips[stateData.fips] = {
            cases: stateData.cases,
            stateCode: stateCode
        };
    }

    // Color scale - sequential blue scale
    const colorScale = d3.scaleSequential()
        .domain([data.min_cases, data.max_cases])
        .interpolator(d3.interpolateBlues);

    // No-data color (gray)
    const noDataColor = "#e5e7eb";

    // Get color for a state
    const getColor = (fipsId) => {
        const fips = String(fipsId).padStart(2, '0');
        const stateData = casesByFips[fips];
        if (!stateData || stateData.cases === 0) {
            return noDataColor;
        }
        return colorScale(stateData.cases);
    };

    // Path generator (no projection needed - Albers USA is pre-projected)
    const path = d3.geoPath();

    // Convert TopoJSON to GeoJSON
    const states = topojson.feature(usTopology, usTopology.objects.states);
    const stateMesh = topojson.mesh(usTopology, usTopology.objects.states, (a, b) => a !== b);

    // Draw states
    svg.append("g")
        .selectAll("path")
        .data(states.features)
        .join("path")
        .attr("fill", d => getColor(d.id))
        .attr("d", path)
        .attr("stroke", "#fff")
        .attr("stroke-width", 0.5)
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
            const fips = String(d.id).padStart(2, '0');
            const stateCode = FIPS_TO_STATE[fips] || fips;
            const stateName = d.properties.name || stateCode;
            const stateData = casesByFips[fips];

            // Show tooltip
            const tooltipEl = document.getElementById('usa-map-tooltip');
            if (tooltipEl) {
                let tooltipText;
                if (stateData && stateData.cases > 0) {
                    tooltipText = `<strong>${stateName}</strong><br>${stateData.cases.toLocaleString()} cases`;
                } else {
                    tooltipText = `<strong>${stateName}</strong><br>No data`;
                }
                tooltipEl.innerHTML = tooltipText;
                tooltipEl.style.visibility = "visible";
            }

            d3.select(this)
                .attr("stroke", "#000")
                .attr("stroke-width", 2);
        })
        .on("mousemove", function(event) {
            const tooltipEl = document.getElementById('usa-map-tooltip');
            if (tooltipEl) {
                tooltipEl.style.top = (event.pageY - 10) + "px";
                tooltipEl.style.left = (event.pageX + 10) + "px";
            }
        })
        .on("mouseout", function() {
            const tooltipEl = document.getElementById('usa-map-tooltip');
            if (tooltipEl) {
                tooltipEl.style.visibility = "hidden";
            }
            d3.select(this)
                .attr("stroke", "#fff")
                .attr("stroke-width", 0.5);
        });

    // Draw state borders
    svg.append("path")
        .datum(stateMesh)
        .attr("fill", "none")
        .attr("stroke", "#fff")
        .attr("stroke-width", 0.5)
        .attr("stroke-linejoin", "round")
        .attr("d", path);

    // Add legend
    const legendX = width - legendWidth - legendMargin.right;
    const legendY = height - legendHeight - legendMargin.bottom;

    const legend = svg.append("g")
        .attr("transform", `translate(${legendX}, ${legendY})`);

    // Legend gradient
    const defs = svg.append("defs");
    const gradientId = "usa-map-legend-gradient-" + Math.random().toString(36).substr(2, 9);
    const gradient = defs.append("linearGradient")
        .attr("id", gradientId)
        .attr("x1", "0%")
        .attr("x2", "100%")
        .attr("y1", "0%")
        .attr("y2", "0%");

    gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", colorScale(data.min_cases));

    gradient.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", colorScale(data.max_cases));

    // Legend rectangle
    legend.append("rect")
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", `url(#${gradientId})`);

    // Legend axis
    const legendScale = d3.scaleLinear()
        .domain([data.min_cases, data.max_cases])
        .range([0, legendWidth]);

    // Use compact format (e.g., 50K, 100K) and fewer ticks
    const formatNumber = (d) => {
        if (d >= 1000000) return d3.format(".1s")(d).replace("M", "M");
        if (d >= 1000) return d3.format(".0s")(d).replace("k", "K");
        return d3.format(",")(d);
    };

    const legendAxis = d3.axisBottom(legendScale)
        .ticks(3)
        .tickFormat(formatNumber);

    legend.append("g")
        .attr("transform", `translate(0, ${legendHeight})`)
        .call(legendAxis)
        .selectAll("text")
        .style("font-size", "10px");

    // Legend title
    legend.append("text")
        .attr("x", legendWidth / 2)
        .attr("y", -6)
        .attr("text-anchor", "middle")
        .style("font-size", "11px")
        .style("font-weight", "600")
        .text("Total Cases");

    // No-data legend item
    const noDataLegend = svg.append("g")
        .attr("transform", `translate(${legendX}, ${legendY + legendHeight + 28})`);

    noDataLegend.append("rect")
        .attr("width", 14)
        .attr("height", 14)
        .attr("fill", noDataColor)
        .attr("stroke", "#ccc")
        .attr("stroke-width", 0.5);

    noDataLegend.append("text")
        .attr("x", 20)
        .attr("y", 11)
        .style("font-size", "10px")
        .text("No data");

    return svg.node();
}

/**
 * Create a brush context chart for date range selection
 * Shows a mini area chart with national case totals and a draggable brush
 * @param {Array} timeseriesData - Array of {period: string, total_cases: number}
 * @param {Function} onBrushChange - Callback when brush selection changes: (startDate, endDate) => void
 * @param {Object} options - Optional configuration {width, height, initialRange}
 * @returns {Object} {node: SVGElement, setBrushRange: (start, end) => void}
 */
function createBrushContextChart(timeseriesData, onBrushChange, options = {}) {
    const width = options.width || 975;
    const height = options.height || 80;
    const margin = { top: 10, right: 20, bottom: 25, left: 40 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create detached SVG
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto");

    // Validate data
    if (!timeseriesData || timeseriesData.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("No time series data available");
        return { node: svg.node(), setBrushRange: () => {} };
    }

    // Parse dates and prepare data (format: YYYY-MM-DD per Pydantic model)
    const parseDate = d3.timeParse("%Y-%m-%d");
    const data = timeseriesData.map(d => ({
        date: parseDate(d.period),
        cases: d.total_cases
    })).filter(d => d.date !== null).sort((a, b) => a.date - b.date);

    if (data.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("No valid date data");
        return { node: svg.node(), setBrushRange: () => {} };
    }

    // Scales
    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, innerWidth]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.cases)])
        .nice()
        .range([innerHeight, 0]);

    // Area generator
    const area = d3.area()
        .x(d => x(d.date))
        .y0(innerHeight)
        .y1(d => y(d.cases))
        .curve(d3.curveMonotoneX);

    // Main group with margins
    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Draw area
    g.append("path")
        .datum(data)
        .attr("fill", "#93c5fd")
        .attr("fill-opacity", 0.6)
        .attr("d", area);

    // Draw line on top
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.cases))
        .curve(d3.curveMonotoneX);

    g.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#3b82f6")
        .attr("stroke-width", 1.5)
        .attr("d", line);

    // X-axis
    const formatDate = d3.timeFormat("%b %Y");
    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).ticks(6).tickFormat(formatDate))
        .selectAll("text")
        .style("font-size", "10px");

    // Brush
    const brush = d3.brushX()
        .extent([[0, 0], [innerWidth, innerHeight]])
        .on("end", brushed);

    const brushG = g.append("g")
        .attr("class", "brush")
        .call(brush);

    // Style the brush selection
    brushG.selectAll(".selection")
        .attr("fill", "#3b82f6")
        .attr("fill-opacity", 0.3)
        .attr("stroke", "#1d4ed8")
        .attr("stroke-width", 1);

    // Initialize brush to cover full range
    const fullExtent = [0, innerWidth];
    brushG.call(brush.move, fullExtent);

    // Brush event handler
    function brushed(event) {
        if (!event.selection) {
            // If cleared, reset to full range
            brushG.call(brush.move, fullExtent);
            return;
        }

        const [x0, x1] = event.selection;

        // Convert pixel positions to dates
        let startDate = x.invert(x0);
        let endDate = x.invert(x1);

        // Snap to month boundaries
        startDate = d3.timeMonth.floor(startDate);
        endDate = d3.timeMonth.ceil(endDate);

        // Clamp to data extent
        const [minDate, maxDate] = d3.extent(data, d => d.date);
        if (startDate < minDate) startDate = minDate;
        if (endDate > maxDate) endDate = d3.timeMonth.ceil(maxDate);

        // Only snap visually if user finished dragging (not during drag)
        if (event.sourceEvent) {
            const snappedX0 = x(startDate);
            const snappedX1 = x(endDate);
            // Snap brush to month boundaries
            if (Math.abs(snappedX0 - x0) > 1 || Math.abs(snappedX1 - x1) > 1) {
                brushG.transition().duration(100).call(brush.move, [snappedX0, snappedX1]);
            }
        }

        // Notify callback
        if (onBrushChange) {
            onBrushChange(startDate, endDate);
        }
    }

    // Method to programmatically set brush range
    function setBrushRange(startDate, endDate) {
        const x0 = x(startDate);
        const x1 = x(endDate);
        brushG.call(brush.move, [x0, x1]);
    }

    return {
        node: svg.node(),
        setBrushRange
    };
}
