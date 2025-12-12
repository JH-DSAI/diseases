/**
 * State Selector Component - Loader/Action/Render pattern
 *
 * A standalone state selection grid that publishes to MosaicState.
 * Other components (charts, maps) subscribe to MosaicState for updates.
 */

/**
 * Loader: Process embedded JSON data from HTML partial.
 *
 * @param {Array} embeddedData - Array of { state, total } objects
 * @returns {Object} Context with states
 */
function loader(embeddedData) {
    // Sort states: National first, then by total descending
    const states = [...embeddedData].sort((a, b) => {
        if (a.state === 'National') return -1;
        if (b.state === 'National') return 1;
        return b.total - a.total;
    });

    return {
        states,
        originalData: embeddedData
    };
}

/**
 * Action: Handle user interactions.
 * Publishes to MosaicState for cross-component updates.
 *
 * @param {string} type - Action type
 * @param {Object} payload - Action payload
 * @param {Object} context - Context from loader
 */
function action(type, payload, context) {
    switch (type) {
        case 'SELECT_STATE':
            window.MosaicState.selectState(payload.state);
            break;

        case 'TOGGLE_STATE':
            window.MosaicState.toggleState(payload.state);
            break;

        case 'CLEAR':
            window.MosaicState.clearStateSelection();
            break;

        default:
            console.warn(`Unknown action: ${type}`);
    }
}

/**
 * Render: Create the state selector grid.
 *
 * @param {Object} context - Context from loader
 * @param {Function} dispatch - Dispatch function for actions
 * @param {Set} selectedStates - Currently selected states
 * @returns {HTMLElement} Grid container element
 */
function render(context, dispatch, selectedStates = new Set()) {
    const { states } = context;

    // Create container
    const container = document.createElement('div');
    container.className = 'grid grid-cols-5 gap-2';

    states.forEach(({ state, total }) => {
        const isSelected = selectedStates.has(state);
        const isNational = state === 'National';
        const color = window.StateColors.getStateColor(state);

        // Create chip button
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = `
            flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-medium
            transition-all duration-150 cursor-pointer
            ${isSelected
                ? 'bg-base-300 ring-2 ring-primary ring-offset-1'
                : 'bg-base-200 hover:bg-base-300'}
            ${isNational ? 'col-span-1 font-semibold' : ''}
        `.trim().replace(/\s+/g, ' ');

        // Color indicator dot
        const dot = document.createElement('span');
        dot.className = 'w-2.5 h-2.5 rounded-full flex-shrink-0';
        dot.style.backgroundColor = color;
        if (!isSelected && selectedStates.size > 0 && !isNational) {
            dot.style.opacity = '0.3';
        }

        // State name
        const name = document.createElement('span');
        name.className = 'truncate';
        name.textContent = state;
        if (!isSelected && selectedStates.size > 0 && !isNational) {
            name.style.opacity = '0.5';
        }

        chip.appendChild(dot);
        chip.appendChild(name);

        // Click handler
        chip.addEventListener('click', (event) => {
            if (event.shiftKey) {
                dispatch('TOGGLE_STATE', { state });
            } else {
                dispatch('SELECT_STATE', { state });
            }
        });

        container.appendChild(chip);
    });

    return container;
}

// Export for template
window.StateSelector = { loader, action, render };
