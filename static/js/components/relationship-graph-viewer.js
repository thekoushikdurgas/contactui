/**
 * Relationship Graph Viewer
 * 
 * Interactive D3.js force-directed graph visualization
 * for page-endpoint relationships.
 */

class RelationshipGraphViewer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }
        
        // Options
        this.apiUrl = options.apiUrl || '/docs/api/dashboard/graph/';
        this.width = options.width || this.container.clientWidth || 800;
        this.height = options.height || this.container.clientHeight || 600;
        this.nodeRadius = {
            page: options.pageRadius || 14,
            endpoint: options.endpointRadius || 10
        };
        
        // State
        this.data = null;
        this.simulation = null;
        this.svg = null;
        this.zoom = null;
        this.selectedNode = null;
        this.highlightedNodes = new Set();
        
        // Bind methods
        this.handleResize = this.handleResize.bind(this);
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize the graph viewer
     */
    async init() {
        this.showLoading();
        
        try {
            await this.loadData();
            this.createGraph();
            this.attachEventListeners();
        } catch (error) {
            console.error('Failed to initialize graph:', error);
            this.showError('Failed to load relationship graph');
        }
    }
    
    /**
     * Load graph data from API
     */
    async loadData() {
        const response = await fetch(this.apiUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const rawData = await response.json();
        
        // Handle wrapped response format from dashboard_graph_api: { success, data: { nodes, edges, statistics } }
        if (rawData.success && rawData.data) {
            this.data = rawData.data;
        } else {
            this.data = rawData;
        }
        
        // Validate data structure - check for nodes AND edges/links
        if (!this.data.nodes || (!this.data.edges && !this.data.links)) {
            // Try to build graph from relationships if in different format
            this.data = this.normalizeData(this.data);
        } else if (this.data.links && !this.data.edges) {
            // D3 convention uses 'links' instead of 'edges'
            this.data.edges = this.data.links;
        }
        
        // Normalize edge fields: Lambda API uses from/to, D3 expects source/target
        if (this.data.edges && this.data.edges.length > 0) {
            this.data.edges = this.data.edges.map(edge => ({
                ...edge,
                source: edge.source || edge.from,
                target: edge.target || edge.to
            }));
        }
    }
    
    /**
     * Normalize data structure
     */
    normalizeData(rawData) {
        // If data is already in correct format with valid nodes
        if (rawData.nodes && rawData.edges && rawData.nodes.length > 0) {
            // Validate that all edge source/target exist in nodes
            const nodeIds = new Set(rawData.nodes.map(n => n.id));
            const validEdges = rawData.edges.filter(e => {
                const sourceId = typeof e.source === 'object' ? e.source.id : e.source;
                const targetId = typeof e.target === 'object' ? e.target.id : e.target;
                return nodeIds.has(sourceId) && nodeIds.has(targetId);
            });
            return { nodes: rawData.nodes, edges: validEdges };
        }
        
        // Build from relationships array
        const edges = [];
        const nodeMap = new Map();
        
        const relationships = rawData.relationships || [];
        
        relationships.forEach(rel => {
            const endpointPath = rel.endpoint_path || rel.endpoint_id;
            const method = rel.method || 'QUERY';
            
            // Handle nested pages structure (from local storage index)
            const pages = rel.pages || [];
            if (pages.length > 0) {
                // Nested format: { endpoint_path, method, pages: [...] }
                const endpointId = `endpoint:${endpointPath}`;
                
                // Add endpoint node
                if (endpointPath && !nodeMap.has(endpointId)) {
                    nodeMap.set(endpointId, {
                        id: endpointId,
                        label: this.truncateLabel(endpointPath),
                        fullLabel: endpointPath,
                        type: 'endpoint',
                        method: method,
                        data: { endpoint_path: endpointPath, method: method }
                    });
                }
                
                // Add page nodes and edges for each page in the array
                pages.forEach(page => {
                    const pagePath = page.page_path || page.page_id;
                    if (!pagePath) return;
                    
                    const pageId = `page:${pagePath}`;
                    
                    // Add page node
                    if (!nodeMap.has(pageId)) {
                        nodeMap.set(pageId, {
                            id: pageId,
                            label: this.truncateLabel(page.page_title || pagePath),
                            fullLabel: pagePath,
                            type: 'page',
                            data: { page_path: pagePath, page_title: page.page_title }
                        });
                    }
                    
                    // Add edge from page to endpoint
                    if (endpointPath) {
                        edges.push({
                            source: pageId,
                            target: endpointId,
                            usage_type: page.usage_type || 'primary',
                            usage_context: page.usage_context
                        });
                    }
                });
            } else {
                // Flat format: { page_id/page_path, endpoint_id/endpoint_path }
                const pageId = rel.page_id || rel.page_path;
                const endpointId = rel.endpoint_id || endpointPath;
                
                // Add page node
                if (pageId && !nodeMap.has(`page:${pageId}`)) {
                    nodeMap.set(`page:${pageId}`, {
                        id: `page:${pageId}`,
                        label: this.truncateLabel(pageId),
                        fullLabel: pageId,
                        type: 'page',
                        data: { page_id: pageId }
                    });
                }
                
                // Add endpoint node
                if (endpointId && !nodeMap.has(`endpoint:${endpointId}`)) {
                    nodeMap.set(`endpoint:${endpointId}`, {
                        id: `endpoint:${endpointId}`,
                        label: this.truncateLabel(endpointId),
                        fullLabel: endpointId,
                        type: 'endpoint',
                        method: method,
                        data: { endpoint_id: endpointId, method: method }
                    });
                }
                
                // Add edge
                if (pageId && endpointId) {
                    edges.push({
                        source: `page:${pageId}`,
                        target: `endpoint:${endpointId}`,
                        usage_type: rel.usage_type || 'primary',
                        usage_context: rel.usage_context
                    });
                }
            }
        });
        
        return {
            nodes: Array.from(nodeMap.values()),
            edges: edges
        };
    }
    
    /**
     * Truncate label for display
     */
    truncateLabel(label, maxLength = 15) {
        if (!label) return '';
        if (label.length <= maxLength) return label;
        return label.substring(0, maxLength - 2) + '...';
    }
    
    /**
     * Create the D3.js graph
     */
    createGraph() {
        // Clear container
        this.container.innerHTML = '';
        
        const { nodes, edges } = this.data;
        
        // Check for empty data
        if (!nodes || nodes.length === 0) {
            this.showEmpty();
            return;
        }
        
        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, this.width, this.height]);
        
        // Create zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.graphGroup.attr('transform', event.transform);
            });
        
        this.svg.call(this.zoom);
        
        // Create main group for zoom/pan
        this.graphGroup = this.svg.append('g');
        
        // Create arrow marker for directed edges
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .append('path')
            .attr('d', 'M 0,-5 L 10,0 L 0,5')
            .attr('fill', '#94a3b8');
        
        // Create force simulation
        this.simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(edges)
                .id(d => d.id)
                .distance(100)
                .strength(0.5))
            .force('charge', d3.forceManyBody()
                .strength(-300)
                .distanceMax(400))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide()
                .radius(d => this.nodeRadius[d.type] + 10));
        
        // Create links
        this.links = this.graphGroup.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(edges)
            .enter()
            .append('line')
            .attr('class', d => `graph-link ${d.usage_type || 'primary'}`)
            .attr('marker-end', 'url(#arrowhead)');
        
        // Create node groups
        this.nodeGroups = this.graphGroup.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'graph-node')
            .call(this.drag(this.simulation));
        
        // Add circles to nodes
        this.nodeGroups.append('circle')
            .attr('class', d => `graph-node-circle ${d.type}${d.method ? ` endpoint-${d.method.toLowerCase()}` : ''}`)
            .attr('r', d => this.nodeRadius[d.type]);
        
        // Add labels to nodes
        this.nodeGroups.append('text')
            .attr('class', 'graph-node-label')
            .attr('dy', d => this.nodeRadius[d.type] + 12)
            .text(d => d.label);
        
        // Add tooltip
        this.createTooltip();
        
        // Add event handlers
        this.nodeGroups
            .on('mouseover', (event, d) => this.handleNodeHover(event, d, true))
            .on('mouseout', (event, d) => this.handleNodeHover(event, d, false))
            .on('click', (event, d) => this.handleNodeClick(event, d));
        
        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            this.links
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            this.nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`);
        });
        
        // Add controls
        this.createControls();
        
        // Add legend
        this.createLegend();
        
        // Add info panel
        this.createInfoPanel();
    }
    
    /**
     * Create drag behavior
     */
    drag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
        
        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }
    
    /**
     * Create tooltip element
     */
    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'graph-tooltip';
        this.container.appendChild(this.tooltip);
    }
    
    /**
     * Handle node hover
     */
    handleNodeHover(event, d, isHover) {
        if (isHover) {
            // Show tooltip
            this.tooltip.innerHTML = `
                <div class="graph-tooltip-title">${this.escapeHtml(d.fullLabel || d.label)}</div>
                <span class="graph-tooltip-badge ${d.type}">${d.type}</span>
                ${d.method ? `<span class="graph-tooltip-badge endpoint">${d.method}</span>` : ''}
            `;
            this.tooltip.classList.add('visible');
            
            // Position tooltip
            const rect = this.container.getBoundingClientRect();
            const x = event.clientX - rect.left + 15;
            const y = event.clientY - rect.top - 10;
            this.tooltip.style.left = `${x}px`;
            this.tooltip.style.top = `${y}px`;
            
            // Highlight connected nodes and edges
            this.highlightConnections(d.id);
        } else {
            // Hide tooltip
            this.tooltip.classList.remove('visible');
            
            // Remove highlights
            this.clearHighlights();
        }
    }
    
    /**
     * Handle node click
     */
    handleNodeClick(event, d) {
        event.stopPropagation();
        
        // Toggle selection
        if (this.selectedNode === d.id) {
            this.selectedNode = null;
            this.clearHighlights();
        } else {
            this.selectedNode = d.id;
            this.highlightConnections(d.id, true);
        }
    }
    
    /**
     * Highlight connected nodes and edges
     */
    highlightConnections(nodeId, persistent = false) {
        const connectedNodes = new Set([nodeId]);
        
        // Find connected nodes
        this.data.edges.forEach(edge => {
            const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
            const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
            
            if (sourceId === nodeId) {
                connectedNodes.add(targetId);
            } else if (targetId === nodeId) {
                connectedNodes.add(sourceId);
            }
        });
        
        // Highlight nodes
        this.nodeGroups.select('circle')
            .classed('highlighted', d => connectedNodes.has(d.id));
        
        // Highlight edges
        this.links.classed('highlighted', d => {
            const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
            const targetId = typeof d.target === 'object' ? d.target.id : d.target;
            return sourceId === nodeId || targetId === nodeId;
        });
        
        // Dim other nodes
        this.nodeGroups.style('opacity', d => connectedNodes.has(d.id) ? 1 : 0.3);
        this.links.style('opacity', d => {
            const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
            const targetId = typeof d.target === 'object' ? d.target.id : d.target;
            return sourceId === nodeId || targetId === nodeId ? 1 : 0.1;
        });
    }
    
    /**
     * Clear all highlights
     */
    clearHighlights() {
        if (this.selectedNode) return; // Keep selection
        
        this.nodeGroups.select('circle').classed('highlighted', false);
        this.links.classed('highlighted', false);
        this.nodeGroups.style('opacity', 1);
        this.links.style('opacity', 1);
    }
    
    /**
     * Create zoom controls
     */
    createControls() {
        const controls = document.createElement('div');
        controls.className = 'graph-controls';
        controls.innerHTML = `
            <button class="graph-control-btn" data-action="zoom-in" title="Zoom In">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
            </button>
            <button class="graph-control-btn" data-action="zoom-out" title="Zoom Out">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
                </svg>
            </button>
            <button class="graph-control-btn" data-action="reset" title="Reset View">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
            </button>
            <button class="graph-control-btn" data-action="fullscreen" title="Fullscreen">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
            </button>
        `;
        
        controls.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            
            const action = btn.dataset.action;
            switch (action) {
                case 'zoom-in':
                    this.svg.transition().call(this.zoom.scaleBy, 1.3);
                    break;
                case 'zoom-out':
                    this.svg.transition().call(this.zoom.scaleBy, 0.7);
                    break;
                case 'reset':
                    this.svg.transition().call(this.zoom.transform, d3.zoomIdentity);
                    break;
                case 'fullscreen':
                    this.toggleFullscreen();
                    break;
            }
        });
        
        this.container.appendChild(controls);
    }
    
    /**
     * Create legend
     */
    createLegend() {
        const legend = document.createElement('div');
        legend.className = 'graph-legend';
        legend.innerHTML = `
            <div class="graph-legend-item">
                <span class="graph-legend-dot page"></span>
                <span>Page</span>
            </div>
            <div class="graph-legend-item">
                <span class="graph-legend-dot endpoint"></span>
                <span>Endpoint</span>
            </div>
            <div class="graph-legend-item">
                <span class="graph-legend-line"></span>
                <span>Relationship</span>
            </div>
        `;
        this.container.appendChild(legend);
    }
    
    /**
     * Create info panel
     */
    createInfoPanel() {
        const pageCount = this.data.nodes.filter(n => n.type === 'page').length;
        const endpointCount = this.data.nodes.filter(n => n.type === 'endpoint').length;
        const edgeCount = this.data.edges.length;
        
        const info = document.createElement('div');
        info.className = 'graph-info-panel';
        info.innerHTML = `
            <div class="graph-info-stat">
                <strong>${pageCount}</strong> pages
            </div>
            <div class="graph-info-stat">
                <strong>${endpointCount}</strong> endpoints
            </div>
            <div class="graph-info-stat">
                <strong>${edgeCount}</strong> relationships
            </div>
        `;
        this.container.appendChild(info);
    }
    
    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            this.container.requestFullscreen();
        }
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        this.container.innerHTML = `
            <div class="graph-loading">
                <div class="graph-loading-spinner"></div>
                <div class="graph-loading-text">Loading relationship graph...</div>
            </div>
        `;
    }
    
    /**
     * Show empty state
     */
    showEmpty() {
        this.container.innerHTML = `
            <div class="graph-empty">
                <svg class="graph-empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <div class="graph-empty-title">No relationships found</div>
                <div class="graph-empty-text">Create relationships between pages and endpoints to see the visualization.</div>
            </div>
        `;
    }
    
    /**
     * Show error state
     */
    showError(message) {
        this.container.innerHTML = `
            <div class="graph-empty">
                <svg class="graph-empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: #ef4444;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div class="graph-empty-title" style="color: #ef4444;">Error</div>
                <div class="graph-empty-text">${this.escapeHtml(message)}</div>
            </div>
        `;
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(str) {
        if (typeof str !== 'string') return str;
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    /**
     * Handle window resize
     */
    handleResize() {
        if (!this.container || !this.svg) return;
        
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        
        this.svg.attr('viewBox', [0, 0, this.width, this.height]);
        
        if (this.simulation) {
            this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(0.3).restart();
        }
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        window.addEventListener('resize', this.handleResize);
        
        // Clear selection on background click
        if (this.svg) {
            this.svg.on('click', () => {
                this.selectedNode = null;
                this.clearHighlights();
            });
        }
    }
    
    /**
     * Destroy the graph viewer
     */
    destroy() {
        window.removeEventListener('resize', this.handleResize);
        
        if (this.simulation) {
            this.simulation.stop();
        }
        
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
    
    /**
     * Refresh the graph
     */
    async refresh() {
        this.destroy();
        await this.init();
    }
}

// Export for global use
window.RelationshipGraphViewer = RelationshipGraphViewer;
