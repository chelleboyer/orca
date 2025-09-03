/**
 * Object Cards JavaScript functionality
 * Handles filtering, layout switching, pagination, and quick actions
 */

class ObjectCards {
    constructor(config) {
        this.config = config;
        this.currentFilters = {
            query: '',
            layout: 'grid',
            sort_by: 'name',
            sort_order: 'asc',
            limit: 20,
            offset: 0
        };
        this.currentData = null;
        this.debounceTimer = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCards();
    }

    bindEvents() {
        // Search input
        const searchInput = document.getElementById('searchQuery');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.debounceSearch(e.target.value);
            });
        }

        // Layout toggle
        const gridBtn = document.getElementById('gridLayout');
        const listBtn = document.getElementById('listLayout');
        
        if (gridBtn) {
            gridBtn.addEventListener('click', () => this.setLayout('grid'));
        }
        if (listBtn) {
            listBtn.addEventListener('click', () => this.setLayout('list'));
        }

        // Filters
        const completionFilter = document.getElementById('completionFilter');
        if (completionFilter) {
            completionFilter.addEventListener('change', (e) => {
                this.applyCompletionFilter(e.target.value);
            });
        }

        const sortBy = document.getElementById('sortBy');
        if (sortBy) {
            sortBy.addEventListener('change', (e) => {
                this.setSorting(e.target.value);
            });
        }

        // Advanced filters toggle
        const toggleAdvanced = document.getElementById('toggleAdvancedFilters');
        const advancedFilters = document.getElementById('advancedFilters');
        if (toggleAdvanced && advancedFilters) {
            toggleAdvanced.addEventListener('click', () => {
                const isHidden = advancedFilters.classList.contains('hidden');
                advancedFilters.classList.toggle('hidden');
                toggleAdvanced.classList.toggle('expanded', !isHidden);
                
                const icon = toggleAdvanced.querySelector('i');
                if (icon) {
                    icon.className = isHidden ? 'fas fa-chevron-up mr-1' : 'fas fa-chevron-down mr-1';
                }
            });
        }

        // Advanced filter inputs
        ['minAttributes', 'maxAttributes', 'attributeType'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.applyAdvancedFilters());
            }
        });

        // Pagination
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousPage());
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextPage());
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshCards');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadCards());
        }

        // Modal events
        this.bindModalEvents();
    }

    bindModalEvents() {
        const modal = document.getElementById('quickActionModal');
        const cancelBtn = document.getElementById('modalCancel');
        const confirmBtn = document.getElementById('modalConfirm');

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideModal());
        }

        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.executeModalAction());
        }

        // Close modal on background click
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal();
                }
            });
        }

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.hideModal();
            }
        });
    }

    debounceSearch(query) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.currentFilters.query = query;
            this.currentFilters.offset = 0;
            this.loadCards();
        }, 300);
    }

    setLayout(layout) {
        this.currentFilters.layout = layout;
        
        // Update button states
        const gridBtn = document.getElementById('gridLayout');
        const listBtn = document.getElementById('listLayout');
        
        if (layout === 'grid') {
            gridBtn?.classList.add('bg-blue-600', 'text-white');
            gridBtn?.classList.remove('bg-gray-100', 'text-gray-700');
            listBtn?.classList.add('bg-gray-100', 'text-gray-700');
            listBtn?.classList.remove('bg-blue-600', 'text-white');
        } else {
            listBtn?.classList.add('bg-blue-600', 'text-white');
            listBtn?.classList.remove('bg-gray-100', 'text-gray-700');
            gridBtn?.classList.add('bg-gray-100', 'text-gray-700');
            gridBtn?.classList.remove('bg-blue-600', 'text-white');
        }
        
        this.renderCards();
    }

    applyCompletionFilter(filterValue) {
        // Reset completion filters
        this.currentFilters.has_definition = null;
        this.currentFilters.has_attributes = null;
        this.currentFilters.has_core_attributes = null;
        this.currentFilters.has_relationships = null;

        switch (filterValue) {
            case 'complete':
                this.currentFilters.has_definition = true;
                this.currentFilters.has_attributes = true;
                this.currentFilters.has_core_attributes = true;
                this.currentFilters.has_relationships = true;
                break;
            case 'incomplete':
                // This is complex, we'll implement it as "not all complete"
                break;
            case 'has_definition':
                this.currentFilters.has_definition = true;
                break;
            case 'no_definition':
                this.currentFilters.has_definition = false;
                break;
            case 'has_attributes':
                this.currentFilters.has_attributes = true;
                break;
            case 'no_attributes':
                this.currentFilters.has_attributes = false;
                break;
            case 'has_core_attributes':
                this.currentFilters.has_core_attributes = true;
                break;
            case 'no_core_attributes':
                this.currentFilters.has_core_attributes = false;
                break;
            case 'has_relationships':
                this.currentFilters.has_relationships = true;
                break;
            case 'no_relationships':
                this.currentFilters.has_relationships = false;
                break;
        }

        this.currentFilters.offset = 0;
        this.loadCards();
    }

    setSorting(sortValue) {
        const [field, order = 'asc'] = sortValue.split('_');
        
        if (field.endsWith('desc')) {
            this.currentFilters.sort_by = field.replace('_desc', '');
            this.currentFilters.sort_order = 'desc';
        } else {
            this.currentFilters.sort_by = field;
            this.currentFilters.sort_order = order;
        }

        this.currentFilters.offset = 0;
        this.loadCards();
    }

    applyAdvancedFilters() {
        const minAttr = document.getElementById('minAttributes')?.value;
        const maxAttr = document.getElementById('maxAttributes')?.value;
        const attrType = document.getElementById('attributeType')?.value;

        this.currentFilters.min_attributes = minAttr ? parseInt(minAttr) : null;
        this.currentFilters.max_attributes = maxAttr ? parseInt(maxAttr) : null;
        this.currentFilters.attribute_type = attrType || null;

        this.currentFilters.offset = 0;
        this.loadCards();
    }

    async loadCards() {
        this.showLoading();

        try {
            const params = new URLSearchParams();
            
            Object.entries(this.currentFilters).forEach(([key, value]) => {
                if (value !== null && value !== '' && value !== undefined) {
                    params.append(key, value);
                }
            });

            const response = await fetch(`${this.config.apiBaseUrl}/projects/${this.config.projectId}/object-cards?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.currentData = data;
            
            this.updateStatistics(data.statistics);
            this.renderCards();
            this.renderPagination();
            
        } catch (error) {
            console.error('Error loading cards:', error);
            this.showError('Failed to load object cards. Please try again.');
        }
    }

    showLoading() {
        const loadingState = document.getElementById('loadingState');
        const emptyState = document.getElementById('emptyState');
        const gridContainer = document.getElementById('gridContainer');
        const listContainer = document.getElementById('listContainer');
        const pagination = document.getElementById('paginationContainer');

        loadingState?.classList.remove('hidden');
        emptyState?.classList.add('hidden');
        gridContainer?.classList.add('hidden');
        listContainer?.classList.add('hidden');
        pagination?.classList.add('hidden');
    }

    showError(message) {
        const loadingState = document.getElementById('loadingState');
        loadingState?.classList.add('hidden');
        
        // Create error state if doesn't exist
        let errorState = document.getElementById('errorState');
        if (!errorState) {
            errorState = document.createElement('div');
            errorState.id = 'errorState';
            errorState.className = 'text-center py-12';
            errorState.innerHTML = `
                <div class="mx-auto h-12 w-12 text-red-400 mb-4">
                    <i class="fas fa-exclamation-triangle text-4xl"></i>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">Error Loading Cards</h3>
                <p class="text-gray-600 mb-4" id="errorMessage">${message}</p>
                <button onclick="window.objectCards.loadCards()" class="btn btn-primary">
                    <i class="fas fa-sync-alt mr-2"></i>Try Again
                </button>
            `;
            document.getElementById('cardsContainer')?.appendChild(errorState);
        } else {
            document.getElementById('errorMessage').textContent = message;
            errorState.classList.remove('hidden');
        }
    }

    updateStatistics(stats) {
        if (!stats) return;

        document.getElementById('totalObjects').textContent = stats.total_objects || '0';
        document.getElementById('withDefinitions').textContent = stats.with_definitions || '0';
        document.getElementById('withAttributes').textContent = stats.with_attributes || '0';
        document.getElementById('withRelationships').textContent = stats.with_relationships || '0';
        document.getElementById('averageCompletion').textContent = `${Math.round(stats.average_completion || 0)}%`;
    }

    renderCards() {
        const loadingState = document.getElementById('loadingState');
        const emptyState = document.getElementById('emptyState');
        const gridContainer = document.getElementById('gridContainer');
        const listContainer = document.getElementById('listContainer');

        loadingState?.classList.add('hidden');

        if (!this.currentData || this.currentData.cards.length === 0) {
            emptyState?.classList.remove('hidden');
            gridContainer?.classList.add('hidden');
            listContainer?.classList.add('hidden');
            return;
        }

        emptyState?.classList.add('hidden');

        if (this.currentFilters.layout === 'grid') {
            gridContainer?.classList.remove('hidden');
            listContainer?.classList.add('hidden');
            this.renderGridCards();
        } else {
            gridContainer?.classList.add('hidden');
            listContainer?.classList.remove('hidden');
            this.renderListCards();
        }
    }

    renderGridCards() {
        const container = document.getElementById('gridContainer');
        if (!container) return;

        container.innerHTML = this.currentData.cards.map(card => this.createGridCard(card)).join('');
        this.bindCardEvents();
    }

    renderListCards() {
        const container = document.getElementById('listContainer');
        if (!container) return;

        container.innerHTML = this.currentData.cards.map(card => this.createListCard(card)).join('');
        this.bindCardEvents();
    }

    createGridCard(card) {
        const completionPercentage = card.completion_status.completion_score;
        const completionClass = this.getCompletionClass(completionPercentage);
        
        return `
            <div class="object-card" data-object-id="${card.id}">
                <div class="object-card-header">
                    <h3 class="object-card-title">${this.escapeHtml(card.name)}</h3>
                    <p class="object-card-definition">${this.escapeHtml(card.definition_summary || 'No definition provided')}</p>
                </div>

                <div class="core-attributes">
                    <div class="core-attributes-title">Core Attributes</div>
                    ${card.core_attributes.length > 0 ? `
                        <div class="core-attributes-list">
                            ${card.core_attributes.map(attr => `
                                <span class="core-attribute-badge">
                                    ${this.escapeHtml(attr.name)}
                                    <span class="attribute-type">${attr.display_type}</span>
                                </span>
                            `).join('')}
                        </div>
                    ` : '<div class="no-core-attributes">No core attributes</div>'}
                </div>

                <div class="card-stats">
                    <div class="stat-item">
                        <div class="stat-value">${card.all_attributes_count}</div>
                        <div class="stat-label">Attributes</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${card.relationship_count}</div>
                        <div class="stat-label">Relations</div>
                    </div>
                </div>

                <div class="completion-status">
                    <div class="completion-bar">
                        <div class="completion-progress ${completionClass}" style="width: ${completionPercentage}%"></div>
                    </div>
                    <div class="completion-text">${Math.round(completionPercentage)}% Complete</div>
                    
                    <div class="completion-indicators">
                        ${this.createCompletionIndicators(card.completion_status)}
                    </div>
                </div>

                <div class="quick-actions">
                    ${this.createQuickActions(card)}
                </div>
            </div>
        `;
    }

    createListCard(card) {
        const completionPercentage = card.completion_status.completion_score;
        
        return `
            <div class="object-card" data-object-id="${card.id}">
                <div class="list-card-main">
                    <h3 class="list-card-title">${this.escapeHtml(card.name)}</h3>
                    <p class="list-card-definition">${this.escapeHtml(card.definition_summary || 'No definition provided')}</p>
                    
                    <div class="list-card-attributes">
                        ${card.core_attributes.map(attr => `
                            <span class="core-attribute-badge">
                                ${this.escapeHtml(attr.name)} (${attr.display_type})
                            </span>
                        `).join('')}
                    </div>
                </div>

                <div class="list-card-stats">
                    <div class="stat-item">
                        <div class="stat-value">${card.all_attributes_count}</div>
                        <div class="stat-label">Attributes</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${card.relationship_count}</div>
                        <div class="stat-label">Relations</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${Math.round(completionPercentage)}%</div>
                        <div class="stat-label">Complete</div>
                    </div>
                </div>

                <div class="list-card-actions">
                    ${this.createQuickActions(card, true)}
                </div>
            </div>
        `;
    }

    createCompletionIndicators(status) {
        const indicators = [
            { key: 'has_definition', label: 'Definition', icon: 'fa-file-text' },
            { key: 'has_attributes', label: 'Attributes', icon: 'fa-list' },
            { key: 'has_core_attributes', label: 'Core Attrs', icon: 'fa-star' },
            { key: 'has_relationships', label: 'Relations', icon: 'fa-link' }
        ];

        return indicators.map(indicator => `
            <div class="completion-indicator ${status[indicator.key] ? 'complete' : 'incomplete'}">
                <i class="fas ${indicator.icon}"></i>
                <span>${indicator.label}</span>
            </div>
        `).join('');
    }

    createQuickActions(card, isListLayout = false) {
        const actions = card.quick_actions || [];
        const actionLabels = {
            view: 'View',
            edit: 'Edit',
            add_definition: 'Add Definition',
            add_attributes: 'Add Attributes',
            mark_core_attributes: 'Mark Core',
            add_relationships: 'Add Relations',
            duplicate: 'Duplicate',
            export: 'Export'
        };

        const maxActions = isListLayout ? 3 : 4;
        const visibleActions = actions.slice(0, maxActions);
        
        return visibleActions.map((action, index) => {
            const isPrimary = action === 'view' || action === 'edit';
            const isSecondary = action === 'add_definition' || action === 'add_attributes';
            const classes = isPrimary ? 'primary' : (isSecondary ? 'secondary' : '');
            
            return `
                <button class="quick-action-btn ${classes}" 
                        data-action="${action}" 
                        data-object-id="${card.id}">
                    ${actionLabels[action] || action}
                </button>
            `;
        }).join('');
    }

    bindCardEvents() {
        // Bind quick action buttons
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const objectId = btn.dataset.objectId;
                this.executeQuickAction(action, objectId);
            });
        });

        // Bind card click events (for viewing)
        document.querySelectorAll('.object-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.classList.contains('quick-action-btn')) {
                    const objectId = card.dataset.objectId;
                    this.executeQuickAction('view', objectId);
                }
            });
        });
    }

    async executeQuickAction(action, objectId) {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/projects/${this.config.projectId}/object-cards/quick-action`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: action,
                    object_id: objectId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success && result.redirect_url) {
                window.location.href = result.redirect_url;
            } else if (!result.success) {
                console.error('Quick action failed:', result.message);
                this.showModal('Error', result.message || 'Action failed');
            }
            
        } catch (error) {
            console.error('Error executing quick action:', error);
            this.showModal('Error', 'Failed to execute action. Please try again.');
        }
    }

    renderPagination() {
        const container = document.getElementById('paginationContainer');
        const data = this.currentData;
        
        if (!container || !data) return;

        if (data.total <= data.limit) {
            container.classList.add('hidden');
            return;
        }

        container.classList.remove('hidden');

        // Update info text
        const showingFrom = Math.min(data.offset + 1, data.total);
        const showingTo = Math.min(data.offset + data.limit, data.total);
        
        document.getElementById('showingFrom').textContent = showingFrom;
        document.getElementById('showingTo').textContent = showingTo;
        document.getElementById('totalCount').textContent = data.total;

        // Update button states
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        
        prevBtn.disabled = !data.has_previous;
        nextBtn.disabled = !data.has_next;

        // Generate page numbers
        this.renderPageNumbers();
    }

    renderPageNumbers() {
        const container = document.getElementById('pageNumbers');
        const data = this.currentData;
        
        if (!container || !data) return;

        const currentPage = data.current_page;
        const totalPages = data.total_pages;
        const maxVisible = 5;

        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);

        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        const pageNumbers = [];
        
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === currentPage;
            pageNumbers.push(`
                <button class="pagination-btn ${isActive ? 'active' : ''}" 
                        data-page="${i}">
                    ${i}
                </button>
            `);
        }

        container.innerHTML = pageNumbers.join('');

        // Bind page number events
        container.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = parseInt(btn.dataset.page);
                this.goToPage(page);
            });
        });
    }

    previousPage() {
        if (this.currentData?.has_previous) {
            this.goToPage(this.currentData.current_page - 1);
        }
    }

    nextPage() {
        if (this.currentData?.has_next) {
            this.goToPage(this.currentData.current_page + 1);
        }
    }

    goToPage(page) {
        this.currentFilters.offset = (page - 1) * this.currentFilters.limit;
        this.loadCards();
    }

    getCompletionClass(percentage) {
        if (percentage >= 75) return 'completion-high';
        if (percentage >= 50) return 'completion-medium';
        if (percentage >= 25) return 'completion-low';
        return 'completion-none';
    }

    showModal(title, content, confirmAction = null) {
        const modal = document.getElementById('quickActionModal');
        const titleEl = document.getElementById('modalTitle');
        const contentEl = document.getElementById('modalContent');
        const confirmBtn = document.getElementById('modalConfirm');

        titleEl.textContent = title;
        contentEl.innerHTML = content;
        
        if (confirmAction) {
            confirmBtn.style.display = 'block';
            this.modalAction = confirmAction;
        } else {
            confirmBtn.style.display = 'none';
            this.modalAction = null;
        }

        modal.classList.remove('hidden');
    }

    hideModal() {
        const modal = document.getElementById('quickActionModal');
        modal.classList.add('hidden');
        this.modalAction = null;
    }

    executeModalAction() {
        if (this.modalAction) {
            this.modalAction();
        }
        this.hideModal();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
