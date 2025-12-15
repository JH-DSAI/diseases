/**
 * Mosaic State - Shared coordinator and selections for cross-filtering
 *
 * This module provides lazy-initialized shared state for Mosaic cross-filtering.
 * Charts can publish to and subscribe from shared selections to coordinate filtering.
 *
 * Usage:
 *   // Publisher (e.g., state selector)
 *   MosaicState.selectState('CA');
 *   MosaicState.toggleState('NY');
 *   MosaicState.clearStateSelection();
 *
 *   // Publisher (e.g., date range selector)
 *   MosaicState.setDateRange(startDate, endDate);
 *   MosaicState.clearDateRange();
 *
 *   // Subscriber (e.g., charts)
 *   const unsubscribe = MosaicState.subscribeToStateSelection((selectedStates) => {
 *       // Re-render with new selection
 *   });
 *
 *   const unsubscribe = MosaicState.subscribeToDateRange((dateRange) => {
 *       // dateRange is { startDate: Date|null, endDate: Date|null }
 *   });
 */

let coordinator = null;
let stateSelection = null;

// State selection management
const selectedStates = new Set();
const stateSelectionSubscribers = [];

// Date range selection management
let dateRange = { startDate: null, endDate: null };
const dateRangeSubscribers = [];

/**
 * Get the shared Mosaic Coordinator (lazy-initialized).
 * The coordinator routes SQL queries to the REST connector.
 */
function getCoordinator() {
    if (!coordinator) {
        coordinator = new window.Mosaic.Coordinator();
        coordinator.databaseConnector(window.createRestConnector());
    }
    return coordinator;
}

/**
 * Get the shared state selection (lazy-initialized).
 * Used for cross-chart state filtering (e.g., clicking a state in row chart
 * highlights it in the map).
 */
function getStateSelection() {
    if (!stateSelection) {
        stateSelection = new window.Mosaic.Selection();
    }
    return stateSelection;
}

/**
 * Get the current selected states as a Set.
 */
function getSelectedStates() {
    return new Set(selectedStates);
}

/**
 * Notify all subscribers of state selection change.
 * Preserves scroll position to prevent layout jump during re-renders.
 */
function notifyStateSelectionSubscribers() {
    const scrollY = window.scrollY;
    const currentSelection = getSelectedStates();
    stateSelectionSubscribers.forEach(callback => {
        try {
            callback(currentSelection);
        } catch (e) {
            console.error('State selection subscriber error:', e);
        }
    });
    // Restore scroll position after DOM updates settle
    requestAnimationFrame(() => {
        window.scrollTo(0, scrollY);
    });
}

/**
 * Select a single state (clears previous selection).
 */
function selectState(state) {
    selectedStates.clear();
    if (state && state !== 'National') {
        selectedStates.add(state);
    }
    notifyStateSelectionSubscribers();
}

/**
 * Toggle a state in the selection (multi-select).
 */
function toggleState(state) {
    if (state === 'National') {
        selectedStates.clear();
    } else if (selectedStates.has(state)) {
        selectedStates.delete(state);
    } else {
        selectedStates.add(state);
    }
    notifyStateSelectionSubscribers();
}

/**
 * Clear the state selection.
 */
function clearStateSelection() {
    selectedStates.clear();
    if (stateSelection) {
        stateSelection.update({ clauses: [] });
    }
    notifyStateSelectionSubscribers();
}

/**
 * Subscribe to state selection changes.
 * @param {Function} callback - Called with Set of selected states when selection changes
 * @returns {Function} Unsubscribe function
 */
function subscribeToStateSelection(callback) {
    stateSelectionSubscribers.push(callback);
    // Immediately call with current state
    callback(getSelectedStates());
    // Return unsubscribe function
    return () => {
        const index = stateSelectionSubscribers.indexOf(callback);
        if (index > -1) {
            stateSelectionSubscribers.splice(index, 1);
        }
    };
}

// =============================================================================
// Date Range Selection
// =============================================================================

/**
 * Get the current date range.
 * @returns {Object} { startDate: Date|null, endDate: Date|null }
 */
function getDateRange() {
    return { ...dateRange };
}

/**
 * Notify all subscribers of date range change.
 * Preserves scroll position to prevent layout jump during re-renders.
 */
function notifyDateRangeSubscribers() {
    const scrollY = window.scrollY;
    const currentRange = getDateRange();
    dateRangeSubscribers.forEach(callback => {
        try {
            callback(currentRange);
        } catch (e) {
            console.error('Date range subscriber error:', e);
        }
    });
    // Restore scroll position after DOM updates settle
    requestAnimationFrame(() => {
        window.scrollTo(0, scrollY);
    });
}

/**
 * Set the date range filter.
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 */
function setDateRange(startDate, endDate) {
    dateRange = { startDate, endDate };
    notifyDateRangeSubscribers();
}

/**
 * Clear the date range filter (show all time).
 */
function clearDateRange() {
    dateRange = { startDate: null, endDate: null };
    notifyDateRangeSubscribers();
}

/**
 * Subscribe to date range changes.
 * @param {Function} callback - Called with { startDate, endDate } when range changes
 * @returns {Function} Unsubscribe function
 */
function subscribeToDateRange(callback) {
    dateRangeSubscribers.push(callback);
    // Immediately call with current state
    callback(getDateRange());
    // Return unsubscribe function
    return () => {
        const index = dateRangeSubscribers.indexOf(callback);
        if (index > -1) {
            dateRangeSubscribers.splice(index, 1);
        }
    };
}

/**
 * Format date range for display.
 * @returns {string} Formatted date range string (e.g., "Jan 2024 – Mar 2024" or "All Time")
 */
function getDateRangeDisplay() {
    if (!dateRange.startDate || !dateRange.endDate) {
        return 'All Time';
    }
    const formatDisplay = d3.timeFormat("%b %Y");
    return `${formatDisplay(dateRange.startDate)} – ${formatDisplay(dateRange.endDate)}`;
}

// Expose globally for use in components
window.MosaicState = {
    // Coordinator
    getCoordinator,
    getStateSelection,
    // State selection
    getSelectedStates,
    selectState,
    toggleState,
    clearStateSelection,
    subscribeToStateSelection,
    // Date range selection
    getDateRange,
    setDateRange,
    clearDateRange,
    subscribeToDateRange,
    getDateRangeDisplay
};
