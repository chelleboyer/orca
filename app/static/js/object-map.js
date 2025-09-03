/**
 * Object Map Visualization JavaScript
 * Handles interactive object map with D3.js
 */

class ObjectMap {
    constructor() {
        this.svg = d3.select('#object-map-svg');
        this.mapContent = d3.select('#map-content');
        this.objectsGroup = d3.select('#objects-group');
        this.relationshipsGroup = d3.select('#relationships-group');
        this.labelsGroup = d3.select('#labels-group');
        
        this.currentZoom = 1;
        this.data = null;
        this.selectedObject = null;
        
        this.initializeMap();
        this.setupEventListeners();
        this.loadMapData();
    }

    initializeMap() {
        // Set up zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                this.mapContent.attr('transform', event.transform);
                this.currentZoom = event.transform.k;
                this.updateZoomDisplay();
            });

        this.svg.call(this.zoom);

        // Define arrow markers for relationships
        this.svg.append('defs')
            .append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 8)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('class', 'arrow-marker');
    }

    setupEventListeners() {
        // Grid toggle
        document.getElementById('show-grid').addEventListener('change', (e) => {
            this.toggleGrid(e.target.checked);
        });

        // Attributes toggle
        document.getElementById('show-attributes').addEventListener('change', (e) => {
            this.toggleAttributes(e.target.checked);
        });

        // Layout algorithm change
        document.getElementById('layout-algorithm').addEventListener('change', (e) => {
            if (e.target.value !== 'manual') {
                this.applyAutoLayout(e.target.value);
            }
        });

        // Close detail panel when clicking outside
        this.svg.on('click', (event) => {
            if (event.target === this.svg.node()) {
                this.closeDetailPanel();
            }
        });
    }

    async loadMapData() {
        try {
            this.showLoading(true);
            
            const projectData = JSON.parse(document.getElementById('project-data').textContent);
            const response = await fetch(`${projectData.api_base}/projects/${projectData.project_id}/object-map`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.data = await response.json();
            this.updateStatistics();
            this.renderMap();
            
        } catch (error) {
            console.error('Failed to load map data:', error);
            this.showError('Failed to load object map data. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    renderMap() {
        if (!this.data) return;

        this.renderRelationships();
        this.renderObjects();
    }

    renderObjects() {
        const objects = this.objectsGroup.selectAll('.object-card')
            .data(this.data.objects, d => d.id);

        // Remove old objects
        objects.exit().remove();

        // Create new object groups
        const objectEnter = objects.enter()
            .append('g')
            .attr('class', 'object-card')
            .attr('transform', d => `translate(${d.position.x}, ${d.position.y})`)
            .on('click', (event, d) => {
                event.stopPropagation();
                this.selectObject(d);
            })
            .call(d3.drag()
                .on('start', this.dragStarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragEnded.bind(this))
            );

        // Add object rectangles
        objectEnter.append('rect')
            .attr('width', 200)
            .attr('height', d => this.calculateObjectHeight(d))
            .attr('rx', 8)
            .attr('ry', 8);

        // Add object names
        objectEnter.append('text')
            .attr('class', 'object-name')
            .attr('x', 100)
            .attr('y', 20)
            .text(d => d.name);

        // Add object definitions
        objectEnter.append('text')
            .attr('class', 'object-definition')
            .attr('x', 100)
            .attr('y', 40)
            .text(d => d.definition_short);

        // Add core attributes
        const showAttributes = document.getElementById('show-attributes').checked;
        if (showAttributes) {
            this.renderObjectAttributes(objectEnter);
        }

        // Update existing objects
        const objectUpdate = objectEnter.merge(objects);
        objectUpdate.classed('core', d => d.core_attribute_count > 0);
    }

    renderObjectAttributes(objectSelection) {
        objectSelection.each(function(d) {
            const objectGroup = d3.select(this);
            let yOffset = 60;

            // Render core attributes
            d.core_attributes.slice(0, 3).forEach((attr, i) => {
                const attrGroup = objectGroup.append('g')
                    .attr('class', 'core-attribute')
                    .attr('transform', `translate(10, ${yOffset + i * 15})`);

                attrGroup.append('text')
                    .attr('class', 'attribute-label')
                    .attr('x', 0)
                    .attr('y', 0)
                    .text(`${attr.name}:`);

                attrGroup.append('text')
                    .attr('class', 'attribute-value')
                    .attr('x', 80)
                    .attr('y', 0)
                    .text(attr.value || '-');

                attrGroup.append('text')
                    .attr('class', 'attribute-type-indicator')
                    .attr('x', 180)
                    .attr('y', 0)
                    .text(attr.display_type);
            });
        });
    }

    renderRelationships() {
        const relationships = this.relationshipsGroup.selectAll('.relationship-line')
            .data(this.data.relationships, d => d.id);

        relationships.exit().remove();

        const relationshipEnter = relationships.enter()
            .append('line')
            .attr('class', 'relationship-line')
            .classed('bidirectional', d => d.is_bidirectional);

        relationshipEnter.merge(relationships)
            .attr('x1', d => this.getObjectPosition(d.object_a_id).x + 200)
            .attr('y1', d => this.getObjectPosition(d.object_a_id).y + this.calculateObjectHeight(this.getObjectById(d.object_a_id)) / 2)
            .attr('x2', d => this.getObjectPosition(d.object_b_id).x)
            .attr('y2', d => this.getObjectPosition(d.object_b_id).y + this.calculateObjectHeight(this.getObjectById(d.object_b_id)) / 2);

        // Add cardinality labels
        const labels = this.labelsGroup.selectAll('.cardinality-label')
            .data(this.data.relationships.filter(d => d.cardinality_a || d.cardinality_b), d => d.id);

        labels.exit().remove();

        const labelsEnter = labels.enter()
            .append('text')
            .attr('class', 'cardinality-label');

        labelsEnter.merge(labels)
            .attr('x', d => {
                const pos1 = this.getObjectPosition(d.object_a_id);
                const pos2 = this.getObjectPosition(d.object_b_id);
                return (pos1.x + pos2.x) / 2;
            })
            .attr('y', d => {
                const pos1 = this.getObjectPosition(d.object_a_id);
                const pos2 = this.getObjectPosition(d.object_b_id);
                return (pos1.y + pos2.y) / 2;
            })
            .text(d => {
                const parts = [];
                if (d.cardinality_a) parts.push(d.cardinality_a);
                if (d.cardinality_b) parts.push(d.cardinality_b);
                return parts.join(' : ');
            });
    }

    calculateObjectHeight(objectData) {
        if (!objectData) return 80;
        
        const baseHeight = 60; // Name + definition
        const showAttributes = document.getElementById('show-attributes').checked;
        
        if (showAttributes && objectData.core_attributes) {
            const attributeHeight = Math.min(objectData.core_attributes.length, 3) * 15;
            return baseHeight + attributeHeight + 10;
        }
        
        return baseHeight;
    }

    getObjectById(objectId) {
        return this.data.objects.find(obj => obj.id === objectId);
    }

    getObjectPosition(objectId) {
        const obj = this.getObjectById(objectId);
        return obj ? obj.position : { x: 0, y: 0 };
    }

    selectObject(objectData) {
        // Update selection
        this.selectedObject = objectData;
        
        // Update visual selection
        this.objectsGroup.selectAll('.object-card')
            .classed('selected', d => d.id === objectData.id);

        // Show detail panel
        this.showObjectDetails(objectData);
    }

    showObjectDetails(objectData) {
        const panel = document.getElementById('object-detail-panel');
        
        // Update content
        document.getElementById('detail-object-name').textContent = objectData.name;
        document.getElementById('detail-object-definition').textContent = objectData.definition;
        
        // Update core attributes
        const coreContainer = document.getElementById('detail-core-attributes');
        coreContainer.innerHTML = '';
        
        objectData.core_attributes.forEach(attr => {
            const item = document.createElement('div');
            item.className = 'attribute-item core';
            item.innerHTML = `
                <div>
                    <span class="attribute-name">${attr.name}</span>
                    <span class="attribute-type">${attr.display_type}</span>
                </div>
                <span class="attribute-value-display">${attr.value || '-'}</span>
            `;
            coreContainer.appendChild(item);
        });
        
        // Update all attributes
        const allContainer = document.getElementById('detail-all-attributes');
        allContainer.innerHTML = '';
        
        objectData.all_attributes.forEach(attr => {
            const item = document.createElement('div');
            item.className = `attribute-item ${attr.is_core ? 'core' : ''}`;
            item.innerHTML = `
                <div>
                    <span class="attribute-name">${attr.name}</span>
                    <span class="attribute-type">${attr.display_type}</span>
                </div>
                <span class="attribute-value-display">${attr.value || '-'}</span>
            `;
            allContainer.appendChild(item);
        });
        
        // Show panel
        panel.style.display = 'block';
    }

    closeDetailPanel() {
        document.getElementById('object-detail-panel').style.display = 'none';
        this.objectsGroup.selectAll('.object-card').classed('selected', false);
        this.selectedObject = null;
    }

    // Drag handlers
    dragStarted(event, d) {
        if (!event.active) {
            // Could add force simulation here
        }
    }

    dragged(event, d) {
        d.position.x = event.x;
        d.position.y = event.y;
        
        d3.select(event.sourceEvent.target.parentNode)
            .attr('transform', `translate(${d.position.x}, ${d.position.y})`);
        
        // Update relationship lines
        this.renderRelationships();
    }

    dragEnded(event, d) {
        // Save position to server
        this.saveObjectPosition(d.id, d.position.x, d.position.y);
    }

    async saveObjectPosition(objectId, x, y) {
        try {
            const projectData = JSON.parse(document.getElementById('project-data').textContent);
            await fetch(`${projectData.api_base}/projects/${projectData.project_id}/object-map/object-position/${objectId}?x=${x}&y=${y}`, {
                method: 'PUT'
            });
        } catch (error) {
            console.warn('Failed to save object position:', error);
        }
    }

    // Zoom controls
    zoomIn() {
        this.svg.transition().duration(300).call(
            this.zoom.scaleBy, 1.2
        );
    }

    zoomOut() {
        this.svg.transition().duration(300).call(
            this.zoom.scaleBy, 0.8
        );
    }

    resetZoom() {
        this.svg.transition().duration(500).call(
            this.zoom.transform,
            d3.zoomIdentity
        );
    }

    updateZoomDisplay() {
        document.getElementById('zoom-level').textContent = `${Math.round(this.currentZoom * 100)}%`;
    }

    // Control functions
    toggleGrid(show) {
        d3.select('.grid-background').classed('hidden', !show);
    }

    toggleAttributes(show) {
        if (this.data) {
            this.renderMap(); // Re-render to show/hide attributes
        }
    }

    async applyAutoLayout(algorithm) {
        try {
            this.showLoading(true);
            
            const projectData = JSON.parse(document.getElementById('project-data').textContent);
            const response = await fetch(`${projectData.api_base}/projects/${projectData.project_id}/object-map/auto-layout?algorithm=${algorithm}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Update object positions
                if (result.positions) {
                    this.data.objects.forEach(obj => {
                        if (result.positions[obj.id]) {
                            obj.position = result.positions[obj.id];
                        }
                    });
                }
                
                // Re-render with new positions
                this.renderMap();
                
                // Animate to new positions
                this.objectsGroup.selectAll('.object-card')
                    .transition()
                    .duration(1000)
                    .attr('transform', d => `translate(${d.position.x}, ${d.position.y})`);
            }
        } catch (error) {
            console.error('Failed to apply auto-layout:', error);
        } finally {
            this.showLoading(false);
        }
    }

    updateStatistics() {
        if (!this.data || !this.data.statistics) return;
        
        const stats = this.data.statistics;
        document.getElementById('object-count').textContent = stats.object_count;
        document.getElementById('relationship-count').textContent = stats.relationship_count;
        document.getElementById('attribute-count').textContent = stats.attribute_count;
        document.getElementById('complexity-score').textContent = stats.complexity_score;
    }

    showLoading(show) {
        document.getElementById('map-loading').style.display = show ? 'flex' : 'none';
    }

    showError(message) {
        // Could implement a toast notification system
        console.error(message);
        alert(message); // Simple fallback
    }

    // Export functions
    async exportMap(format) {
        try {
            const projectData = JSON.parse(document.getElementById('project-data').textContent);
            
            if (format === 'svg') {
                this.exportAsSVG();
            } else if (format === 'png') {
                this.exportAsPNG();
            } else {
                // Use API export
                window.open(`${projectData.api_base}/projects/${projectData.project_id}/object-map/export?format=${format}`);
            }
        } catch (error) {
            console.error('Failed to export map:', error);
        }
    }

    exportAsSVG() {
        const svgData = new XMLSerializer().serializeToString(this.svg.node());
        const blob = new Blob([svgData], { type: 'image/svg+xml' });
        this.downloadFile(blob, 'object-map.svg');
    }

    exportAsPNG() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        const svgData = new XMLSerializer().serializeToString(this.svg.node());
        const blob = new Blob([svgData], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            
            canvas.toBlob((pngBlob) => {
                this.downloadFile(pngBlob, 'object-map.png');
                URL.revokeObjectURL(url);
            });
        };
        
        img.src = url;
    }

    downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Global functions for template event handlers
let objectMap;

function autoLayout() {
    const algorithm = document.getElementById('layout-algorithm').value;
    if (algorithm !== 'manual') {
        objectMap.applyAutoLayout(algorithm);
    }
}

function exportMap(format) {
    objectMap.exportMap(format);
}

function refreshMap() {
    objectMap.loadMapData();
}

function zoomIn() {
    objectMap.zoomIn();
}

function zoomOut() {
    objectMap.zoomOut();
}

function resetZoom() {
    objectMap.resetZoom();
}

function toggleGrid() {
    const checkbox = document.getElementById('show-grid');
    objectMap.toggleGrid(checkbox.checked);
}

function toggleAttributes() {
    const checkbox = document.getElementById('show-attributes');
    objectMap.toggleAttributes(checkbox.checked);
}

function changeLayout() {
    const select = document.getElementById('layout-algorithm');
    if (select.value !== 'manual') {
        objectMap.applyAutoLayout(select.value);
    }
}

function closeDetailPanel() {
    objectMap.closeDetailPanel();
}

function editObject() {
    if (objectMap.selectedObject) {
        // Navigate to object edit page
        window.location.href = `/objects/${objectMap.selectedObject.id}/edit`;
    }
}

function viewRelationships() {
    if (objectMap.selectedObject) {
        // Navigate to relationships page
        window.location.href = `/objects/${objectMap.selectedObject.id}/relationships`;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    objectMap = new ObjectMap();
});
