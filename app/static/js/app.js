// Disease Dashboard - Custom JavaScript

/**
 * Disease color configuration
 * Maps disease slugs to their accent colors from the design system
 */
const DISEASE_COLORS = {
    'measles': '#13A3D3',
    'meningococcal-disease': '#4625DA',
    'meningococcus': '#4625DA',
    'pertussis': '#9225DA',
    'default': '#3b82f6'
};

/**
 * Get the accent color for a disease
 * @param {string} slug - Disease slug
 * @returns {string} Hex color code
 */
function getDiseaseColor(slug) {
    return DISEASE_COLORS[slug] || DISEASE_COLORS['default'];
}

/**
 * Persistent query params manager.
 * Stores specified URL params in sessionStorage and applies them to navigation links.
 */
class PersistedParams {
    constructor(options = {}) {
        this.storageKey = options.storageKey || 'disease_dashboard_params';
        // Keys to persist - add new filter keys here as needed
        this.persistedKeys = options.persistedKeys || ['data_source'];
        // Selector for links that should include persisted params
        this.linkSelector = options.linkSelector || '[data-home-link]';
        // Path where params should be cleared if not present in URL
        this.homePath = options.homePath || '/';
    }

    // Get all persisted params as an object
    getAll() {
        try {
            return JSON.parse(sessionStorage.getItem(this.storageKey)) || {};
        } catch {
            return {};
        }
    }

    // Get a specific persisted param
    get(key) {
        return this.getAll()[key] || null;
    }

    // Set a specific param
    set(key, value) {
        const params = this.getAll();
        if (value === null || value === undefined) {
            delete params[key];
        } else {
            params[key] = value;
        }
        sessionStorage.setItem(this.storageKey, JSON.stringify(params));
    }

    // Delete a specific param
    delete(key) {
        this.set(key, null);
    }

    // Clear all persisted params
    clear() {
        sessionStorage.removeItem(this.storageKey);
    }

    // Sync from current URL - saves persisted keys from URL to storage
    syncFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const isHomePage = window.location.pathname === this.homePath;

        this.persistedKeys.forEach(key => {
            const value = urlParams.get(key);
            if (value) {
                this.set(key, value);
            } else if (isHomePage) {
                // Clear param if on home page without it (user explicitly removed it)
                this.delete(key);
            }
        });
    }

    // Build query string from persisted params
    toQueryString() {
        const params = this.getAll();
        const urlParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value) urlParams.set(key, value);
        });
        const str = urlParams.toString();
        return str ? `?${str}` : '';
    }

    // Update all navigation links with persisted params
    updateLinks() {
        const queryString = this.toQueryString();
        const links = document.querySelectorAll(this.linkSelector);

        links.forEach(link => {
            const basePath = link.dataset.basePath || '/';
            link.href = basePath + queryString;
        });
    }

    // Initialize - sync from URL and update links
    init() {
        this.syncFromUrl();
        this.updateLinks();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Disease Dashboard initialized');

    // Create global instance for persisted params
    window.persistedParams = new PersistedParams({
        persistedKeys: ['data_source'], // Add more keys here as needed
    });

    // Initial setup
    window.persistedParams.init();

    // Initialize URL state manager for filter persistence
    // This restores state/date filters from URL query params
    if (window.URLStateManager) {
        window.URLStateManager.init();
    }

    // Listen for HTMX pushUrl events to sync params
    document.body.addEventListener('htmx:pushedIntoHistory', function() {
        window.persistedParams.init();
    });
});
