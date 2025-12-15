/**
 * State Colors Module
 *
 * Provides a deterministic state-to-color mapping used across all components.
 * This ensures color consistency between the state selector, trend charts,
 * maps, and any other visualization that displays state data.
 *
 * Colors are assigned based on alphabetical state order, guaranteeing the
 * same color for each state regardless of data ordering or filtering.
 */

(function() {
    // Color palette - visually distinct colors for categorical data
    // Based on Tailwind CSS color palette for consistency with UI
    const PALETTE = [
        '#ef4444',  // red-500
        '#f59e0b',  // amber-500
        '#10b981',  // emerald-500
        '#3b82f6',  // blue-500
        '#8b5cf6',  // violet-500
        '#ec4899',  // pink-500
        '#06b6d4',  // cyan-500
        '#14b8a6',  // teal-500
        '#f97316',  // orange-500
        '#84cc16',  // lime-500
        '#a855f7',  // purple-500
        '#6366f1',  // indigo-500
        '#22c55e',  // green-500
        '#eab308',  // yellow-500
        '#d946ef',  // fuchsia-500
        '#0ea5e9',  // sky-500
    ];

    // Special color for National aggregate
    const NATIONAL_COLOR = '#1f2937';  // gray-800

    // All US states + DC in alphabetical order (fixed domain for deterministic colors)
    const STATE_ORDER = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
        'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
        'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
        'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
        'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI',
        'WY'
    ];

    // Build the state-to-color mapping (computed once at load time)
    const STATE_COLOR_MAP = new Map();
    STATE_COLOR_MAP.set('National', NATIONAL_COLOR);

    STATE_ORDER.forEach((state, index) => {
        STATE_COLOR_MAP.set(state, PALETTE[index % PALETTE.length]);
    });

    /**
     * Get the color for a state.
     *
     * @param {string} state - State code (e.g., 'CA', 'TX') or 'National'
     * @returns {string} Hex color code
     */
    function getStateColor(state) {
        return STATE_COLOR_MAP.get(state) || '#94a3b8';  // gray-400 fallback
    }

    /**
     * Get all state colors as a Map.
     * Useful for components that need to iterate over all colors.
     *
     * @returns {Map<string, string>} Map of state code to hex color
     */
    function getStateColorMap() {
        return new Map(STATE_COLOR_MAP);
    }

    /**
     * Create a D3 ordinal scale using the state color mapping.
     * Convenience function for D3-based charts.
     *
     * @param {Array<string>} [domain] - Optional domain array (states to include)
     * @returns {d3.ScaleOrdinal} D3 ordinal scale
     */
    function createStateColorScale(domain) {
        const scale = d3.scaleOrdinal();

        if (domain) {
            scale.domain(domain);
            scale.range(domain.map(state => getStateColor(state)));
        } else {
            scale.domain(['National', ...STATE_ORDER]);
            scale.range(['National', ...STATE_ORDER].map(state => getStateColor(state)));
        }

        return scale;
    }

    /**
     * Get the color palette array.
     *
     * @returns {Array<string>} Array of hex color codes
     */
    function getPalette() {
        return [...PALETTE];
    }

    // Export to window
    window.StateColors = {
        getStateColor,
        getStateColorMap,
        createStateColorScale,
        getPalette,
        NATIONAL_COLOR
    };
})();
