/**
 * Vendor Bundle - Third-party dependencies
 * This file bundles HTMX, Alpine.js, D3.js (selective), and Mosaic for the application
 */

// HTMX - Dynamic HTML updates
import 'htmx.org';

// Alpine.js - Reactive components
import Alpine from 'alpinejs';

// D3.js - Selective imports for tree-shaking
// d3-selection
import { create, select } from 'd3-selection';
// d3-scale
import { scaleLinear, scaleTime, scaleOrdinal, scaleBand, scaleSequential, scaleQuantile } from 'd3-scale';
// d3-scale-chromatic
import { interpolateBlues } from 'd3-scale-chromatic';
// d3-axis
import { axisBottom, axisLeft } from 'd3-axis';
// d3-shape
import { line, area, curveMonotoneX, stack } from 'd3-shape';
// d3-array
import { extent, max as d3Max, groups } from 'd3-array';
// d3-time-format
import { timeFormat, timeParse } from 'd3-time-format';
// d3-format
import { format } from 'd3-format';
// d3-geo
import { geoPath } from 'd3-geo';
// d3-brush
import { brushX } from 'd3-brush';
// d3-time
import { timeMonth } from 'd3-time';
// d3-transition (side effect - enables .transition() on selections)
import 'd3-transition';

// TopoJSON - For map rendering
import * as topojson from 'topojson-client';

// US Atlas - Pre-bundled US state topology (no CDN fetch needed)
import usStatesTopology from 'us-atlas/states-albers-10m.json';

// Mosaic - Cross-filtering coordinator
import { Coordinator, Selection, MosaicClient } from '@uwdata/mosaic-core';
import { Query, count, sum, avg, min, max } from '@uwdata/mosaic-sql';

// Expose Alpine globally
window.Alpine = Alpine;

// Start Alpine after DOM is ready
// This allows page scripts to register components before Alpine initializes
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Alpine.start());
} else {
    Alpine.start();
}

// Expose D3 globally - only the functions we actually use
window.d3 = {
    // d3-selection
    create,
    select,
    // d3-scale
    scaleLinear,
    scaleTime,
    scaleOrdinal,
    scaleBand,
    scaleSequential,
    scaleQuantile,
    // d3-scale-chromatic
    interpolateBlues,
    // d3-axis
    axisBottom,
    axisLeft,
    // d3-shape
    line,
    area,
    curveMonotoneX,
    stack,
    // d3-array
    extent,
    max: d3Max,
    groups,
    // d3-time-format
    timeFormat,
    timeParse,
    // d3-format
    format,
    // d3-geo
    geoPath,
    // d3-brush
    brushX,
    // d3-time
    timeMonth,
};

// Expose TopoJSON globally for map rendering
window.topojson = topojson;

// Expose pre-loaded US states topology (no fetch needed)
window.usStatesTopology = usStatesTopology;

// Expose Mosaic globally for cross-filtering
window.Mosaic = {
    Coordinator,
    Selection,
    MosaicClient,
    Query,
    count,
    sum,
    avg,
    min,
    max
};

console.log('Vendor bundle loaded: HTMX, Alpine.js, D3.js (selective), TopoJSON, Mosaic');
