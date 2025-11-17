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

console.log('Vendor bundle loaded: HTMX, Alpine.js, D3.js');
