/**
 * REST Connector for Mosaic Coordinator
 *
 * This connector sends SQL queries to the FastAPI backend's /api/query endpoint.
 * It implements the connector interface expected by Mosaic's Coordinator.
 */

/**
 * Create a REST connector for Mosaic coordinator.
 *
 * @param {string} baseUrl - Base URL for the API (default: '/api')
 * @returns {Object} Connector object with query method
 */
function createRestConnector(baseUrl = '/api') {
    return {
        /**
         * Execute a SQL query via the REST API.
         *
         * @param {string} sql - The SQL query string
         * @param {string} type - Response type: 'json' or 'arrow' (default: 'json')
         * @returns {Promise<Object>} Query results with data, columns, and row_count
         */
        async query(sql, type = 'json') {
            const response = await fetch(`${baseUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sql, type })
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `Query failed: ${response.status}`);
            }

            return response.json();
        }
    };
}

// Expose globally for use in templates
window.createRestConnector = createRestConnector;
