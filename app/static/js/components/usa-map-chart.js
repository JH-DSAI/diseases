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
 * @param {Object} options - Optional configuration {width, height, highlightedStates}
 * @returns {Object} Object with {svg: SVGElement, legendData: {colors, breaks, noDataColor}}
 */
function createUSAMapChart(data, diseaseName, usTopology, options = {}) {
    // TopoJSON viewport is 975x610 for Albers USA projection
    const width = options.width || 975;
    const height = options.height || 610;
    const highlightedStates = options.highlightedStates || new Set();

    // Create detached SVG with accessibility attributes
    const svg = d3.create("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("role", "img")
        .attr("aria-label", `USA choropleth map showing ${diseaseName} cases by state`)
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

    // Extract non-zero case values for quantile calculation
    const caseValues = Object.values(data.states)
        .map(s => s.cases)
        .filter(c => c > 0)
        .sort((a, b) => a - b);

    // 5-step blue color palette (light to dark)
    const colorRange = ["#eff6ff", "#bfdbfe", "#60a5fa", "#2563eb", "#1e40af"];

    // Color scale - quantile for even distribution across states
    const colorScale = caseValues.length > 0
        ? d3.scaleQuantile()
            .domain(caseValues)
            .range(colorRange)
        : () => colorRange[0]; // Fallback if no data

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

    // Helper to check if a state is highlighted
    const isHighlighted = (fipsId) => {
        if (highlightedStates.size === 0) return false;
        const fips = String(fipsId).padStart(2, '0');
        const stateCode = FIPS_TO_STATE[fips];
        return stateCode && highlightedStates.has(stateCode);
    };

    // Draw states
    svg.append("g")
        .selectAll("path")
        .data(states.features)
        .join("path")
        .attr("fill", d => getColor(d.id))
        .attr("d", path)
        .attr("stroke", d => isHighlighted(d.id) ? "#1d4ed8" : "#fff")
        .attr("stroke-width", d => isHighlighted(d.id) ? 2.5 : 0.5)
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

    // Build legend data from quantile thresholds
    const quantiles = caseValues.length > 0 && colorScale.quantiles
        ? colorScale.quantiles()
        : [];

    let legendData = null;
    if (quantiles.length > 0) {
        const minVal = caseValues[0];
        const maxVal = caseValues[caseValues.length - 1];
        legendData = {
            colors: colorRange,
            breaks: [minVal, ...quantiles, maxVal],
            noDataColor: noDataColor
        };
    }

    return { svg: svg.node(), legendData };
}


