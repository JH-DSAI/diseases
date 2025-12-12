/**
 * Date Range Selector Component - Loader/Action/Render pattern
 *
 * A standalone date range selector with brush interaction that publishes
 * to MosaicState. Other components subscribe to MosaicState for date filtering.
 *
 * Shows a mini area chart with national case totals and a draggable brush.
 */

/**
 * Loader: Process embedded JSON data from HTML partial.
 *
 * @param {Array} embeddedData - Array of {period: string, total_cases: number}
 * @returns {Object} Context with parsed data and date extent
 */
function loader(embeddedData) {
    if (!embeddedData || embeddedData.length === 0) {
        return { data: [], dateExtent: null, originalData: embeddedData };
    }

    // Parse dates (format: YYYY-MM-DD per Pydantic model)
    const parseDate = d3.timeParse("%Y-%m-%d");
    const data = embeddedData
        .map(d => ({
            date: parseDate(d.period),
            cases: d.total_cases
        }))
        .filter(d => d.date !== null)
        .sort((a, b) => a.date - b.date);

    const dateExtent = data.length > 0 ? d3.extent(data, d => d.date) : null;

    return {
        data,
        dateExtent,
        originalData: embeddedData
    };
}

/**
 * Action: Handle user interactions.
 * Publishes to MosaicState for cross-component updates.
 *
 * @param {string} type - Action type
 * @param {Object} payload - Action payload
 * @param {Object} context - Context from loader
 */
function action(type, payload, context) {
    switch (type) {
        case 'SET_DATE_RANGE':
            window.MosaicState.setDateRange(payload.startDate, payload.endDate);
            break;

        case 'CLEAR':
            window.MosaicState.clearDateRange();
            break;

        default:
            console.warn(`Unknown action: ${type}`);
    }
}

/**
 * Render: Create the brush context chart SVG.
 *
 * @param {Object} context - Context from loader
 * @param {Function} dispatch - Dispatch function for actions
 * @param {Object} options - Optional configuration {width, height}
 * @returns {Object} {node: SVGElement, setBrushRange: Function}
 */
function render(context, dispatch, options = {}) {
    const { data, dateExtent } = context;

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
    if (!data || data.length === 0) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .style("fill", "#6b7280")
            .text("No time series data available");
        return { node: svg.node(), setBrushRange: () => {} };
    }

    // Scales
    const x = d3.scaleTime()
        .domain(dateExtent)
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

    // Track if we're in a programmatic snap to prevent feedback loops
    let isSnapping = true;  // Start true to skip initial brush.move event

    // Brush event handler
    function brushed(event) {
        // Skip if this is a programmatic snap (prevents feedback loop)
        if (isSnapping) return;

        if (!event.selection) {
            // If cleared, reset to full range
            isSnapping = true;
            brushG.call(brush.move, fullExtent);
            isSnapping = false;
            return;
        }

        const [x0, x1] = event.selection;

        // Convert pixel positions to dates
        let startDate = x.invert(x0);
        let endDate = x.invert(x1);

        // Snap to nearest month boundaries
        startDate = d3.timeMonth.round(startDate);
        endDate = d3.timeMonth.round(endDate);

        // Ensure minimum 1 month range
        if (startDate >= endDate) {
            endDate = d3.timeMonth.offset(startDate, 1);
        }

        // Clamp to data extent
        const [minDate, maxDate] = dateExtent;
        if (startDate < minDate) startDate = minDate;
        if (endDate > maxDate) endDate = maxDate;

        // Snap brush visually to month boundaries (only for user interactions)
        if (event.sourceEvent) {
            const snappedX0 = x(startDate);
            const snappedX1 = x(endDate);
            // Only snap if there's a meaningful difference
            if (Math.abs(snappedX0 - x0) > 1 || Math.abs(snappedX1 - x1) > 1) {
                isSnapping = true;
                brushG.call(brush.move, [snappedX0, snappedX1]);
                isSnapping = false;
            }
        }

        // Dispatch action to update global state
        dispatch('SET_DATE_RANGE', { startDate, endDate });
    }

    // Initialize brush position (after brushed function is defined)
    brushG.call(brush.move, fullExtent);
    isSnapping = false;  // Now allow brush events

    // Method to programmatically set brush range
    function setBrushRange(startDate, endDate) {
        if (!startDate || !endDate) {
            brushG.call(brush.move, fullExtent);
            return;
        }
        const x0 = x(startDate);
        const x1 = x(endDate);
        brushG.call(brush.move, [x0, x1]);
    }

    return {
        node: svg.node(),
        setBrushRange
    };
}

// Export for template
window.DateRangeSelector = { loader, action, render };
