/**
 * URL State Manager - Syncs filter state to URL query parameters
 *
 * Enables shareable URLs with filter state persisted:
 * /disease/pertussis?states=CA,NY,TX&start=2024-01-01&end=2024-06-30
 *
 * Usage:
 *   // Initialize on page load (after MosaicState is ready)
 *   window.URLStateManager.init();
 */

(function() {
    // Debounce helper
    function debounce(fn, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    // Format date as YYYY-MM-DD for URL
    function formatDate(date) {
        if (!date) return null;
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    // Parse YYYY-MM-DD string to Date
    function parseDate(str) {
        if (!str) return null;
        const date = new Date(str);
        return isNaN(date.getTime()) ? null : date;
    }

    /**
     * Restore filter state from current URL parameters.
     * Called on page load before subscribing to changes.
     */
    function restoreFromUrl() {
        const params = new URLSearchParams(window.location.search);

        // Restore selected states
        const statesParam = params.get('states');
        if (statesParam) {
            const states = statesParam.split(',').filter(s => s.trim());
            states.forEach(state => {
                window.MosaicState.toggleState(state.trim());
            });
        }

        // Restore date range
        const startParam = params.get('start');
        const endParam = params.get('end');
        if (startParam && endParam) {
            const startDate = parseDate(startParam);
            const endDate = parseDate(endParam);
            if (startDate && endDate) {
                window.MosaicState.setDateRange(startDate, endDate);
            }
        }
    }

    /**
     * Sync current filter state to URL (debounced).
     * Uses replaceState to avoid polluting browser history.
     */
    const syncToUrl = debounce(function() {
        const params = new URLSearchParams();

        // Serialize selected states
        const selectedStates = window.MosaicState.getSelectedStates();
        if (selectedStates.size > 0) {
            const statesArray = Array.from(selectedStates).sort();
            params.set('states', statesArray.join(','));
        }

        // Serialize date range
        const { startDate, endDate } = window.MosaicState.getDateRange();
        if (startDate && endDate) {
            params.set('start', formatDate(startDate));
            params.set('end', formatDate(endDate));
        }

        // Build new URL
        const paramsString = params.toString();
        const newUrl = paramsString
            ? `${window.location.pathname}?${paramsString}`
            : window.location.pathname;

        // Update URL without page reload
        window.history.replaceState(null, '', newUrl);
    }, 300);

    /**
     * Initialize URL state manager.
     * Should be called after DOM is ready and MosaicState is available.
     */
    function init() {
        if (!window.MosaicState) {
            console.warn('URLStateManager: MosaicState not found, skipping init');
            return;
        }

        // Restore state from URL first (before subscribing)
        restoreFromUrl();

        // Subscribe to future changes
        window.MosaicState.subscribeToStateSelection(syncToUrl);
        window.MosaicState.subscribeToDateRange(syncToUrl);
    }

    // Expose globally
    window.URLStateManager = {
        init,
        restoreFromUrl,
        syncToUrl
    };
})();
