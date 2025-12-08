/**
 * Vendor Bundle - Third-party dependencies
 * This file bundles HTMX, Alpine.js, and D3.js for the application
 */

// HTMX - Dynamic HTML updates
import 'htmx.org';

// Alpine.js - Reactive components
import Alpine from 'alpinejs';

// D3.js - Data visualizations
import * as d3 from 'd3';

// TopoJSON - For map rendering
import * as topojson from 'topojson-client';

// Crossfilter - Multi-dimensional filtering
import crossfilter from 'crossfilter2';

// DC.js - Dimensional charting with crossfilter
import * as dc from 'dc';
import 'dc/src/compat/d3v6';  // D3 v6+ compatibility layer
import 'dc/dist/style/dc.css';

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

// Expose Crossfilter globally for DC.js
window.crossfilter = crossfilter;

// Expose DC.js globally for dimensional charting
window.dc = dc;

console.log('Vendor bundle loaded: HTMX, Alpine.js, D3.js, TopoJSON, Crossfilter, DC.js');
