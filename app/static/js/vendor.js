/**
 * Vendor Bundle - Third-party dependencies
 * This file bundles HTMX, Alpine.js, D3.js, and Mosaic for the application
 */

// HTMX - Dynamic HTML updates
import 'htmx.org';

// Alpine.js - Reactive components
import Alpine from 'alpinejs';

// D3.js - Data visualizations
import * as d3 from 'd3';

// TopoJSON - For map rendering
import * as topojson from 'topojson-client';

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

// Expose D3 globally for existing chart code
window.d3 = d3;

// Expose TopoJSON globally for map rendering
window.topojson = topojson;

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

console.log('Vendor bundle loaded: HTMX, Alpine.js, D3.js, TopoJSON, Mosaic');
