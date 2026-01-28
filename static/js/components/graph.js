// Project Graph Component JavaScript (Cytoscape.js)

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('graph-container');
    if (!container || typeof cytoscape === 'undefined') {
        return;
    }

    // Initialize Cytoscape graph
    const cy = cytoscape({
        container: container,
        elements: [
            // Example nodes and edges
            { data: { id: 'fe-auth', label: 'Auth Client', type: 'frontend' } },
            { data: { id: 'fe-dash', label: 'Dashboard View', type: 'frontend' } },
            { data: { id: 'be-gateway', label: 'API Gateway', type: 'backend' } },
            { data: { id: 'e1', source: 'fe-auth', target: 'be-gateway', label: 'uses' } },
            { data: { id: 'e2', source: 'fe-dash', target: 'be-gateway', label: 'uses' } },
        ],
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'background-color': '#fff',
                    'border-width': 2,
                    'border-color': '#e2e8f0',
                    'width': 120,
                    'height': 45,
                    'shape': 'round-rectangle',
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#94a3b8',
                    'target-arrow-color': '#94a3b8',
                    'target-arrow-shape': 'triangle',
                }
            }
        ],
        layout: {
            name: 'grid',
            rows: 2
        }
    });
});
