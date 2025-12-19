/**
 * Map Legend Component
 * A reusable legend component for choropleth maps
 */

/**
 * Create a map legend HTML element
 * @param {Object} props - Legend configuration
 * @param {string} props.title - Legend title (e.g., "Total Cases")
 * @param {string[]} props.colors - Array of color values
 * @param {number[]} props.breaks - Array of breakpoint values (length = colors.length + 1)
 * @param {string} props.noDataColor - Color for N/A values
 * @param {number} [props.boxWidth=32] - Width of each color box in pixels
 * @param {number} [props.boxHeight=10] - Height of each color box in pixels
 * @returns {HTMLElement} The legend container element
 */
function createMapLegend(props) {
    const {
        title = 'Legend',
        colors = [],
        breaks = [],
        noDataColor = '#e5e7eb',
        boxWidth = 64,
        boxHeight = 20
    } = props || {};

    const container = document.createElement('div');
    container.className = 'flex items-center gap-4 text-sm';

    // Compact number format
    const formatNumber = (d) => {
        if (d >= 1000000) return d3.format(".2s")(d);
        if (d >= 1000) return d3.format(".2s")(d);
        return d3.format(",")(Math.round(d));
    };

    // Title
    const titleEl = document.createElement('span');
    titleEl.className = 'font-semibold text-xs';
    titleEl.textContent = title;
    container.appendChild(titleEl);

    if (colors.length > 0 && breaks.length > 0) {
        // Color bar with labels
        const barContainer = document.createElement('div');
        barContainer.className = 'flex flex-col';

        // Color boxes row
        const colorRow = document.createElement('div');
        colorRow.className = 'flex';
        colorRow.style.border = '1px solid #999';

        colors.forEach(color => {
            const box = document.createElement('div');
            box.style.width = `${boxWidth}px`;
            box.style.height = `${boxHeight}px`;
            box.style.backgroundColor = color;
            colorRow.appendChild(box);
        });
        barContainer.appendChild(colorRow);

        // Labels row - positioned at breakpoints between boxes
        const labelRow = document.createElement('div');
        labelRow.className = 'relative text-xs';
        labelRow.style.width = `${colors.length * boxWidth}px`;
        labelRow.style.height = '14px';

        breaks.forEach((value, i) => {
            const label = document.createElement('span');
            label.style.position = 'absolute';
            label.style.top = '0';

            if (i === 0) {
                // First label: left-aligned at start
                label.style.left = '0';
            } else if (i === breaks.length - 1) {
                // Last label: right-aligned at end
                label.style.right = '0';
            } else {
                // Middle labels: centered at breakpoint
                label.style.left = `${i * boxWidth}px`;
                label.style.transform = 'translateX(-50%)';
            }

            label.textContent = formatNumber(value);
            labelRow.appendChild(label);
        });

        barContainer.appendChild(labelRow);
        container.appendChild(barContainer);
    }

    // N/A indicator
    const naContainer = document.createElement('div');
    naContainer.className = 'flex items-center gap-1';

    const naBox = document.createElement('div');
    naBox.style.width = `${boxHeight}px`;
    naBox.style.height = `${boxHeight}px`;
    naBox.style.backgroundColor = noDataColor;
    naBox.style.border = '1px solid #999';
    naContainer.appendChild(naBox);

    const naLabel = document.createElement('span');
    naLabel.className = 'text-xs';
    naLabel.textContent = 'N/A';
    naContainer.appendChild(naLabel);

    container.appendChild(naContainer);

    return container;
}
