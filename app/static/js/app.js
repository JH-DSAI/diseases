// Disease Dashboard - Custom JavaScript

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Disease Dashboard initialized');

    // Check for API key in localStorage (for development)
    const apiKey = localStorage.getItem('api_key');
    if (apiKey) {
        console.log('API key found in localStorage');
    }
});

/**
 * D3.js utility functions for future chart implementations
 */
const ChartUtils = {
    /**
     * Create a simple line chart
     * @param {string} selector - CSS selector for container
     * @param {Array} data - Array of {x, y} data points
     * @param {Object} options - Chart options
     */
    lineChart: function(selector, data, options = {}) {
        // Placeholder for future implementation
        console.log('Line chart placeholder:', selector, data);
    },

    /**
     * Create a bar chart
     * @param {string} selector - CSS selector for container
     * @param {Array} data - Array of {label, value} data points
     * @param {Object} options - Chart options
     */
    barChart: function(selector, data, options = {}) {
        // Placeholder for future implementation
        console.log('Bar chart placeholder:', selector, data);
    },

    /**
     * Create a pie chart
     * @param {string} selector - CSS selector for container
     * @param {Array} data - Array of {label, value} data points
     * @param {Object} options - Chart options
     */
    pieChart: function(selector, data, options = {}) {
        // Placeholder for future implementation
        console.log('Pie chart placeholder:', selector, data);
    }
};

/**
 * API utility functions
 */
const API = {
    /**
     * Get headers with authentication
     */
    getHeaders: function() {
        const apiKey = localStorage.getItem('api_key');
        const headers = {
            'Content-Type': 'application/json'
        };
        if (apiKey) {
            headers['Authorization'] = `Bearer ${apiKey}`;
        }
        return headers;
    },

    /**
     * Fetch data from API endpoint
     * @param {string} endpoint - API endpoint path
     * @returns {Promise} - Fetch promise
     */
    get: async function(endpoint) {
        try {
            const response = await fetch(endpoint, {
                method: 'GET',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
};

/**
 * Alpine.js data stores for reactive components
 */
document.addEventListener('alpine:init', () => {
    // Global app state
    Alpine.store('app', {
        loading: false,
        error: null,

        setLoading(state) {
            this.loading = state;
        },

        setError(message) {
            this.error = message;
        },

        clearError() {
            this.error = null;
        }
    });
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChartUtils, API };
}
