/**
 * CTA Matrix JavaScript
 * Handles matrix interactions, filtering, and modal management
 */

// Global state
let currentMatrix = null;
let filteredMatrix = null;

// Initialize matrix when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeMatrix();
    setupEventListeners();
});

/**
 * Initialize matrix functionality
 */
function initializeMatrix() {
    // Setup HTMX event listeners
    setupHTMXEventListeners();
    
    // Initialize filter functionality
    initializeFilters();
    
    // Setup matrix cell click handlers
    setupCellClickHandlers();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Modal event listeners
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            hideModals();
        }
    });
    
    // Escape key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideModals();
        }
    });
    
    // Matrix refresh on window resize (for responsive layout)
    window.addEventListener('resize', debounce(function() {
        adjustMatrixLayout();
    }, 250));
}

/**
 * Setup HTMX event listeners
 */
function setupHTMXEventListeners() {
    // Listen for successful HTMX requests
    document.body.addEventListener('htmx:afterRequest', function(event) {
        const target = event.detail.target;
        
        // Handle matrix grid updates
        if (target && target.id === 'matrix-grid') {
            onMatrixDataLoaded();
        }
        
        // Handle cell modal content updates
        if (target && target.closest('#ctaModal')) {
            onCellModalLoaded();
        }
        
        // Handle successful CTA creation/updates
        if (event.detail.xhr.status >= 200 && event.detail.xhr.status < 300) {
            handleSuccessfulOperation(event);
        }
    });
    
    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('HTMX Error:', event.detail);
        showErrorMessage('An error occurred. Please try again.');
    });
}

/**
 * Handle matrix data loaded
 */
function onMatrixDataLoaded() {
    // Store matrix data for filtering
    storeMatrixData();
    
    // Adjust layout
    adjustMatrixLayout();
    
    // Setup cell interactions
    setupCellClickHandlers();
    
    // Apply any active filters
    applyCurrentFilters();
}

/**
 * Store matrix data for filtering
 */
function storeMatrixData() {
    const matrixContainer = document.querySelector('.matrix-grid-container');
    if (!matrixContainer) return;
    
    // Extract matrix data from DOM
    currentMatrix = {
        roles: extractRolesData(),
        objects: extractObjectsData(),
        cells: extractCellsData()
    };
    
    filteredMatrix = JSON.parse(JSON.stringify(currentMatrix));
}

/**
 * Extract roles data from DOM
 */
function extractRolesData() {
    const roleHeaders = document.querySelectorAll('.matrix-role-header');
    return Array.from(roleHeaders).map(header => ({
        id: header.closest('[data-role-id]').dataset.roleId,
        name: header.querySelector('.role-name').textContent.trim(),
        description: header.querySelector('.role-description')?.textContent.trim() || ''
    }));
}

/**
 * Extract objects data from DOM
 */
function extractObjectsData() {
    const objectHeaders = document.querySelectorAll('.matrix-object-header');
    return Array.from(objectHeaders).map(header => ({
        id: header.dataset.objectId,
        name: header.querySelector('.object-name').textContent.trim(),
        coreNoun: header.querySelector('.object-core-noun')?.textContent.trim() || ''
    }));
}

/**
 * Extract cells data from DOM
 */
function extractCellsData() {
    const cells = document.querySelectorAll('.matrix-cell');
    return Array.from(cells).map(cell => ({
        roleId: cell.dataset.roleId,
        objectId: cell.dataset.objectId,
        ctaCount: parseInt(cell.dataset.ctaCount) || 0,
        hasCrud: {
            create: cell.querySelector('.crud-indicator.create-action') !== null,
            read: cell.querySelector('.crud-indicator.read-action') !== null,
            update: cell.querySelector('.crud-indicator.update-action') !== null,
            delete: cell.querySelector('.crud-indicator.delete-action') !== null,
            none: cell.querySelector('.crud-indicator.none-action') !== null
        }
    }));
}

/**
 * Setup cell click handlers
 */
function setupCellClickHandlers() {
    const cells = document.querySelectorAll('.matrix-cell .cell-content');
    cells.forEach(cell => {
        // Remove existing click handlers
        cell.removeEventListener('click', handleCellClick);
        // Add new click handler
        cell.addEventListener('click', handleCellClick);
    });
}

/**
 * Handle cell click
 */
function handleCellClick(event) {
    const cellContent = event.currentTarget;
    const cell = cellContent.closest('.matrix-cell');
    const roleId = cell.dataset.roleId;
    const objectId = cell.dataset.objectId;
    
    // Show loading state
    showCTAModal();
    
    // HTMX will handle the actual request
    // The click event will bubble up and trigger the hx-get
}

/**
 * Filter matrix based on current filter values
 */
function filterMatrix() {
    if (!currentMatrix) return;
    
    const filters = getCurrentFilters();
    
    // Filter roles
    const filteredRoles = currentMatrix.roles.filter(role => 
        !filters.role || role.id === filters.role
    );
    
    // Filter objects
    const filteredObjects = currentMatrix.objects.filter(object => 
        !filters.object || object.id === filters.object
    );
    
    // Filter cells
    const filteredCells = currentMatrix.cells.filter(cell => {
        // Role filter
        if (filters.role && cell.roleId !== filters.role) return false;
        
        // Object filter
        if (filters.object && cell.objectId !== filters.object) return false;
        
        // CRUD filter
        if (filters.crud) {
            const crudKey = filters.crud.toLowerCase();
            if (crudKey === 'none') {
                return cell.hasCrud.none;
            } else {
                return cell.hasCrud[crudKey];
            }
        }
        
        return true;
    });
    
    // Update DOM to show filtered results
    updateMatrixDisplay(filteredRoles, filteredObjects, filteredCells);
}

/**
 * Get current filter values
 */
function getCurrentFilters() {
    return {
        role: document.getElementById('filterRole')?.value || '',
        object: document.getElementById('filterObject')?.value || '',
        crud: document.getElementById('filterCrud')?.value || ''
    };
}

/**
 * Apply current filters
 */
function applyCurrentFilters() {
    const filters = getCurrentFilters();
    if (filters.role || filters.object || filters.crud) {
        filterMatrix();
    }
}

/**
 * Update matrix display with filtered data
 */
function updateMatrixDisplay(roles, objects, cells) {
    const matrixTable = document.querySelector('.matrix-table');
    if (!matrixTable) return;
    
    // Show/hide rows
    const roleRows = document.querySelectorAll('.matrix-row');
    roleRows.forEach(row => {
        const roleId = row.dataset.roleId;
        const shouldShow = roles.some(role => role.id === roleId);
        row.style.display = shouldShow ? '' : 'none';
    });
    
    // Show/hide columns
    const objectHeaders = document.querySelectorAll('.matrix-object-header');
    objectHeaders.forEach((header, index) => {
        const objectId = header.dataset.objectId;
        const shouldShow = objects.some(object => object.id === objectId);
        const columnIndex = index + 1; // +1 because first column is role names
        
        // Hide/show header
        header.style.display = shouldShow ? '' : 'none';
        
        // Hide/show cells in this column
        const columnCells = document.querySelectorAll(`.matrix-cell:nth-child(${columnIndex + 1})`);
        columnCells.forEach(cell => {
            cell.style.display = shouldShow ? '' : 'none';
        });
    });
    
    // Update summary stats
    updateSummaryStats(roles.length, objects.length, cells.length);
}

/**
 * Update summary statistics
 */
function updateSummaryStats(roleCount, objectCount, cellCount) {
    const summaryStats = document.querySelector('.summary-stats');
    if (!summaryStats) return;
    
    const stats = summaryStats.querySelectorAll('.stat-item');
    if (stats[1]) stats[1].querySelector('.stat-number').textContent = roleCount;
    if (stats[2]) stats[2].querySelector('.stat-number').textContent = objectCount;
    if (stats[3]) stats[3].querySelector('.stat-number').textContent = cellCount;
}

/**
 * Initialize filter functionality
 */
function initializeFilters() {
    const filterSelects = document.querySelectorAll('.matrix-filters select');
    filterSelects.forEach(select => {
        select.addEventListener('change', filterMatrix);
    });
}

/**
 * Show CTA modal
 */
function showCTAModal() {
    const modal = document.getElementById('ctaModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Hide CTA modal
 */
function hideCTAModal() {
    const modal = document.getElementById('ctaModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

/**
 * Show bulk create modal
 */
function showBulkCreateModal() {
    const modal = document.getElementById('bulkCreateModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Hide bulk create modal
 */
function hideBulkCreateModal() {
    const modal = document.getElementById('bulkCreateModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        
        // Clear form
        const form = modal.querySelector('form');
        if (form) form.reset();
    }
}

/**
 * Hide all modals
 */
function hideModals() {
    hideCTAModal();
    hideBulkCreateModal();
}

/**
 * Handle cell modal loaded
 */
function onCellModalLoaded() {
    // Setup form validation
    setupFormValidation();
    
    // Focus first input
    const firstInput = document.querySelector('#ctaModal input, #ctaModal select, #ctaModal textarea');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const form = document.getElementById('addCTAForm');
    if (!form) return;
    
    // Real-time validation
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('blur', validateField);
        field.addEventListener('input', clearFieldError);
    });
}

/**
 * Validate individual field
 */
function validateField(event) {
    const field = event.target;
    const isValid = field.checkValidity();
    
    if (!isValid) {
        showFieldError(field, field.validationMessage);
    } else {
        clearFieldError(field);
    }
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('error');
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    field.parentNode.appendChild(errorElement);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('error');
    const errorElement = field.parentNode.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

/**
 * Handle successful operations
 */
function handleSuccessfulOperation(event) {
    const target = event.detail.target;
    
    // If it's a CTA creation, refresh the matrix
    if (target && target.id === 'addCTAResult') {
        setTimeout(() => {
            // Refresh the matrix
            const refreshButton = document.querySelector('[hx-target="#matrix-grid"]');
            if (refreshButton) {
                htmx.trigger(refreshButton, 'click');
            }
        }, 1000);
    }
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    // Create temporary error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-error';
    errorDiv.textContent = message;
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '1rem';
    errorDiv.style.right = '1rem';
    errorDiv.style.zIndex = '9999';
    
    document.body.appendChild(errorDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

/**
 * Adjust matrix layout for responsive design
 */
function adjustMatrixLayout() {
    const matrixTable = document.querySelector('.matrix-table');
    if (!matrixTable) return;
    
    // Adjust table layout based on screen size
    const screenWidth = window.innerWidth;
    
    if (screenWidth < 768) {
        // Mobile adjustments
        matrixTable.style.fontSize = '0.75rem';
    } else {
        // Desktop
        matrixTable.style.fontSize = '';
    }
}

/**
 * Export matrix data
 */
function exportMatrix() {
    const projectId = window.location.pathname.split('/')[2]; // Extract from URL
    
    // Create download link
    const link = document.createElement('a');
    link.href = `/api/v1/projects/${projectId}/export/cta-matrix`;
    link.download = 'cta-matrix.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Generate user stories from CTAs
 */
function generateUserStories() {
    const projectId = window.location.pathname.split('/')[2];
    
    // Navigate to user stories page or show generation modal
    window.location.href = `/projects/${projectId}/user-stories/generate`;
}

/**
 * Utility: Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global access
window.filterMatrix = filterMatrix;
window.showCTAModal = showCTAModal;
window.hideCTAModal = hideCTAModal;
window.showBulkCreateModal = showBulkCreateModal;
window.hideBulkCreateModal = hideBulkCreateModal;
window.exportMatrix = exportMatrix;
window.generateUserStories = generateUserStories;
