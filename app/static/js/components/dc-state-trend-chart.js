/**
 * DC.js State Trend Chart
 * Dimensional charting with crossfilter for interactive state filtering
 */

/**
 * Create a DC.js dashboard with linked state filter and line chart
 * @param {Object} data - Data object with states, national, and available_states
 * @param {string} lineChartId - CSS selector for line chart container
 * @param {string} rowChartId - CSS selector for row chart (state filter) container
 * @param {Object} options - Optional configuration
 * @returns {Object} { lineChart, rowChart, cf } - DC chart instances and crossfilter
 */
function createDCStateTrendChart(data, lineChartId, rowChartId, options = {}) {
    // Flatten state data for crossfilter
    const records = [];

    for (const [state, points] of Object.entries(data.states || {})) {
        points.forEach(p => {
            records.push({
                state: state,
                date: new Date(p.period),
                cases: p.cases || 0
            });
        });
    }

    // Add national totals
    if (data.national) {
        data.national.forEach(p => {
            records.push({
                state: 'National',
                date: new Date(p.period),
                cases: p.cases || 0
            });
        });
    }

    if (records.length === 0) {
        console.warn('No data for DC state trend chart');
        return null;
    }

    // Create crossfilter
    const cf = crossfilter(records);

    // Dimensions
    const stateDim = cf.dimension(d => d.state);
    const dateDim = cf.dimension(d => d.date);

    // For series chart: composite dimension
    const stateAndDateDim = cf.dimension(d => [d.state, d.date]);

    // Groups
    const totalCasesByState = stateDim.group().reduceSum(d => d.cases);

    // Group for series chart - key is [state, date], value is cases
    const casesByStateAndDate = stateAndDateDim.group().reduceSum(d => d.cases);

    // Date extent
    const dateExtent = d3.extent(records, d => d.date);

    // Get container dimensions
    const lineContainer = document.querySelector(lineChartId);
    const rowContainer = document.querySelector(rowChartId);

    // Calculate responsive widths - row chart is fixed, line chart fills remaining space
    const rowWidth = options.rowWidth || 180;
    const stateCount = Object.keys(data.states || {}).length + 1;  // +1 for National
    const rowHeight = options.rowHeight || Math.min(350, Math.max(200, stateCount * 24));

    // Line chart width: container width minus row chart width minus gap
    const containerWidth = lineContainer?.parentElement?.clientWidth || 800;
    const lineWidth = options.lineWidth || Math.max(400, containerWidth - rowWidth - 40);
    const lineHeight = options.lineHeight || 380;

    // Color scale for states (defined early so both charts can use it)
    const stateList = ['National', ...Object.keys(data.states || {}).sort()];
    const colorScale = d3.scaleOrdinal()
        .domain(stateList)
        .range(['#1f2937', '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
                '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#84cc16',
                '#a855f7', '#6366f1', '#22c55e', '#eab308', '#d946ef']);

    // Row chart for state selection
    const rowChart = dc.rowChart(rowChartId)
        .dimension(stateDim)
        .group(totalCasesByState)
        .width(rowWidth)
        .height(rowHeight)
        .margins({ top: 10, right: 10, bottom: 30, left: 60 })
        .elasticX(true)
        .ordering(d => d.key === 'National' ? -Infinity : -d.value)  // National first, then by cases
        .label(() => '')  // Labels added manually on y-axis
        .title(d => `${d.key}: ${d.value.toLocaleString()} total cases`)
        .colors(colorScale)
        .colorAccessor(d => d.key);

    // Reduce x-axis ticks to avoid crowding
    rowChart.xAxis().ticks(3);

    // Add state labels to y-axis (left of bars)
    rowChart.on('renderlet', chart => {
        chart.selectAll('g.row').each(function(d) {
            const g = d3.select(this);
            g.select('text.y-label').remove();
            g.append('text')
                .attr('class', 'y-label')
                .attr('x', -5)
                .attr('dy', '0.9em')
                .attr('text-anchor', 'end')
                .attr('fill', '#374151')
                .text(d.key);
        });
    });

    // Series chart for multi-line display (NOT stacked)
    const seriesChart = dc.seriesChart(lineChartId)
        .dimension(stateAndDateDim)
        .group(casesByStateAndDate)
        .width(lineWidth)
        .height(lineHeight)
        .margins({ top: 20, right: 30, bottom: 50, left: 60 })
        .x(d3.scaleTime().domain(dateExtent))
        .xUnits(d3.timeMonths)
        .brushOn(false)
        .clipPadding(10)
        .seriesAccessor(d => d.key[0])  // state name
        .keyAccessor(d => d.key[1])      // date
        .valueAccessor(d => d.value)     // cases
        .chart(c => {
            const chart = dc.lineChart(c);
            chart.renderArea(false);     // Lines only, no area fill
            chart.curve(d3.curveMonotoneX);
            chart.renderDataPoints({ radius: 2, fillOpacity: 0.8, strokeOpacity: 1 });
            chart.xyTipsOn(true);
            return chart;
        })
        .colors(colorScale);

    // No legend needed - row chart serves as interactive legend

    // Render all charts
    dc.renderAll();

    // Make SVGs responsive
    const lineSvg = document.querySelector(lineChartId + ' svg');
    if (lineSvg) {
        lineSvg.style.maxWidth = '100%';
        lineSvg.style.height = 'auto';
    }

    return {
        lineChart: seriesChart,
        rowChart: rowChart,
        cf: cf,
        reset: () => {
            dc.filterAll();
            dc.renderAll();
        }
    };
}
