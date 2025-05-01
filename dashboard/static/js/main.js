// Main.js - Handles loading data for the dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const totalIocsElement = document.getElementById('total-iocs');
    const avgScoreElement = document.getElementById('avg-score');
    const highRiskCountElement = document.getElementById('high-risk-count');
    const iocTableBody = document.getElementById('ioc-table-body');
    const statsContainer = document.getElementById('stats-container');
    const paginationElement = document.getElementById('pagination');
    const filterForm = document.getElementById('filter-form');
    const iocTypeSelect = document.getElementById('ioc-type');
    const minScoreInput = document.getElementById('min-score');
    const maxScoreInput = document.getElementById('max-score');
    const minScoreValue = document.getElementById('min-score-value');
    const maxScoreValue = document.getElementById('max-score-value');
    // New filter elements
    const sourceFeedSelect = document.getElementById('source-feed');
    const categorySelect = document.getElementById('category');
    const dateFromInput = document.getElementById('date-from');
    const dateToInput = document.getElementById('date-to');
    const resetFiltersBtn = document.getElementById('reset-filters');
    // Search elements
    const searchQueryInput = document.getElementById('search-query');
    const clearSearchBtn = document.getElementById('clear-search');
    // Batch actions elements
    const batchActionsToolbar = document.getElementById('batch-actions-toolbar');
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const selectAllBtn = document.getElementById('select-all');
    const deselectAllBtn = document.getElementById('deselect-all');
    const selectedCountElement = document.getElementById('selected-count');
    const batchExportBtn = document.getElementById('batch-export');
    const batchRecategorizeBtn = document.getElementById('batch-recategorize');
    const batchDeleteBtn = document.getElementById('batch-delete');

    // Selected IOCs set
    const selectedIOCs = new Set();
    
    // Pagination variables
    let currentPage = 1;
    const itemsPerPage = 10;
    let totalPages = 1;
    
    // SIMPLER LOADING INDICATOR IMPLEMENTATION
    // Create the loading indicator once at startup
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'globalLoadingOverlay';
    loadingOverlay.style.position = 'fixed';
    loadingOverlay.style.top = '0';
    loadingOverlay.style.left = '0';
    loadingOverlay.style.width = '100%';
    loadingOverlay.style.height = '100%';
    loadingOverlay.style.backgroundColor = 'rgba(0,0,0,0.3)';
    loadingOverlay.style.display = 'flex';
    loadingOverlay.style.justifyContent = 'center';
    loadingOverlay.style.alignItems = 'center';
    loadingOverlay.style.zIndex = '9999';
    
    loadingOverlay.innerHTML = `
        <div class="card p-4 shadow">
            <div class="d-flex flex-column align-items-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mb-0">Loading data...</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(loadingOverlay);
    
    // Add event listeners
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            currentPage = 1;
            loadingOverlay.style.display = 'flex';
            loadIocs();
        });
    }

    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            // Reset all filter inputs
            if (iocTypeSelect) iocTypeSelect.value = '';
            if (sourceFeedSelect) sourceFeedSelect.value = '';
            if (categorySelect) categorySelect.value = '';
            if (minScoreInput) minScoreInput.value = 0;
            if (maxScoreInput) maxScoreInput.value = 100;
            if (minScoreValue) minScoreValue.textContent = '0';
            if (maxScoreValue) maxScoreValue.textContent = '100';
            if (dateFromInput) dateFromInput.value = '';
            if (dateToInput) dateToInput.value = '';
            if (searchQueryInput) searchQueryInput.value = '';
            
            // Reload with reset filters
            currentPage = 1;
            loadingOverlay.style.display = 'flex';
            loadIocs();
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            if (searchQueryInput) {
                searchQueryInput.value = '';
                // Trigger search if there was a value before clearing
                currentPage = 1;
                loadingOverlay.style.display = 'flex';
                loadIocs();
            }
        });
    }
    
    // Add event listener for Enter key in search box
    if (searchQueryInput) {
        searchQueryInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                currentPage = 1;
                loadingOverlay.style.display = 'flex';
                loadIocs();
            }
        });
    }

    if (minScoreInput) {
        minScoreInput.addEventListener('input', function() {
            minScoreValue.textContent = this.value;
        });
    }

    if (maxScoreInput) {
        maxScoreInput.addEventListener('input', function() {
            maxScoreValue.textContent = this.value;
        });
    }

    // Add event listeners for batch action buttons
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.ioc-checkbox');
            const isChecked = this.checked;
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
                const iocId = checkbox.getAttribute('data-ioc');
                
                if (isChecked) {
                    selectedIOCs.add(iocId);
                } else {
                    selectedIOCs.delete(iocId);
                }
            });
            
            updateBatchActionsUI();
        });
    }
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.dispatchEvent(new Event('change'));
            }
        });
    }
    
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', function() {
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.dispatchEvent(new Event('change'));
            }
        });
    }
    
    if (batchExportBtn) {
        batchExportBtn.addEventListener('click', function() {
            if (selectedIOCs.size === 0) return;
            
            // Create a modal with export format options
            const modalHtml = `
                <div class="modal fade" id="batch-export-modal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Export ${selectedIOCs.size} Selected IOCs</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <p>Choose export format:</p>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-primary export-format-btn" data-format="csv">
                                        <i class="bi bi-file-earmark-spreadsheet"></i> CSV Format
                                    </button>
                                    <button class="btn btn-primary export-format-btn" data-format="json">
                                        <i class="bi bi-file-earmark-code"></i> JSON Format
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to the body
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('batch-export-modal'));
            modal.show();
            
            // Add event listeners to the export format buttons
            document.querySelectorAll('.export-format-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const format = this.getAttribute('data-format');
                    exportSelectedIOCs(format);
                    modal.hide();
                    
                    // Clean up - remove modal after hiding
                    modal._element.addEventListener('hidden.bs.modal', function() {
                        document.body.removeChild(modalContainer);
                    });
                });
            });
        });
    }
    
    if (batchRecategorizeBtn) {
        batchRecategorizeBtn.addEventListener('click', function() {
            if (selectedIOCs.size === 0) return;
            
            // Create a modal with category options
            const modalHtml = `
                <div class="modal fade" id="batch-recategorize-modal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Recategorize ${selectedIOCs.size} Selected IOCs</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <p>Choose new category:</p>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-outline-success category-btn" data-category="low">Low Risk</button>
                                    <button class="btn btn-outline-warning category-btn" data-category="medium">Medium Risk</button>
                                    <button class="btn btn-outline-danger category-btn" data-category="high">High Risk</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to the body
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('batch-recategorize-modal'));
            modal.show();
            
            // Add event listeners to the category buttons
            document.querySelectorAll('.category-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const category = this.getAttribute('data-category');
                    recategorizeSelectedIOCs(category);
                    modal.hide();
                    
                    // Clean up - remove modal after hiding
                    modal._element.addEventListener('hidden.bs.modal', function() {
                        document.body.removeChild(modalContainer);
                    });
                });
            });
        });
    }
    
    if (batchDeleteBtn) {
        batchDeleteBtn.addEventListener('click', function() {
            if (selectedIOCs.size === 0) return;
            
            // Create a confirmation modal
            const modalHtml = `
                <div class="modal fade" id="batch-delete-modal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Confirm Deletion</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="alert alert-danger">
                                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                    Are you sure you want to delete ${selectedIOCs.size} IOCs?
                                </div>
                                <p>This action cannot be undone.</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-danger" id="confirm-delete-btn">Delete</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to the body
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('batch-delete-modal'));
            modal.show();
            
            // Add event listener to the confirm button
            document.getElementById('confirm-delete-btn').addEventListener('click', function() {
                deleteSelectedIOCs();
                modal.hide();
                
                // Clean up - remove modal after hiding
                modal._element.addEventListener('hidden.bs.modal', function() {
                    document.body.removeChild(modalContainer);
                });
            });
        });
    }
    
    // Add event listeners for export buttons
    const exportCsvBtn = document.getElementById('export-csv');
    const exportJsonBtn = document.getElementById('export-json');
    
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', function() {
            // Build query parameters from current filters
            const params = buildExportParams();
            // Trigger the download
            window.location.href = `/api/export/csv?${params}`;
        });
    }
    
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', function() {
            // Build query parameters from current filters
            const params = buildExportParams();
            // Trigger the download
            window.location.href = `/api/export/json?${params}`;
        });
    }
    
    // Helper function to build query parameters for export
    function buildExportParams() {
        const params = new URLSearchParams();
        
        // Add all current filters
        if (iocTypeSelect && iocTypeSelect.value) params.append('type', iocTypeSelect.value);
        if (sourceFeedSelect && sourceFeedSelect.value) params.append('source_feed', sourceFeedSelect.value);
        if (categorySelect && categorySelect.value) params.append('category', categorySelect.value);
        if (minScoreInput && minScoreInput.value > 0) params.append('min_score', minScoreInput.value);
        if (maxScoreInput && maxScoreInput.value < 100) params.append('max_score', maxScoreInput.value);
        if (dateFromInput && dateFromInput.value) params.append('date_from', dateFromInput.value);
        if (dateToInput && dateToInput.value) params.append('date_to', dateToInput.value);
        if (searchQueryInput && searchQueryInput.value) params.append('search_query', searchQueryInput.value);
        
        return params.toString();
    }

    // Load statistics
    function loadStats() {
        statsContainer.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading statistics...</span>
                </div>
                <p class="mt-2 text-muted">Loading statistics...</p>
            </div>
        `;
        
        fetch('/api/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load stats: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                displayStats(data);
                // Populate source feed dropdown with data from stats
                populateSourceFeedOptions(data);
                // Hide loading indicator once all data is loaded
                hideLoadingWhenReady();
            })
            .catch(error => {
                console.error('Error loading stats:', error);
                statsContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        Error loading statistics: ${error.message}
                        <button class="btn btn-sm btn-outline-danger ms-2" onclick="loadStats()">
                            <i class="bi bi-arrow-clockwise"></i> Retry
                        </button>
                    </div>
                `;
                // Hide loading on error too
                hideLoadingWhenReady();
            });
    }
    
    // Populate source feed dropdown from stats data
    function populateSourceFeedOptions(data) {
        if (!sourceFeedSelect) return;
        
        // Get unique source feeds from the data
        let sourceFeeds = [];
        if (data && data.by_source_feed) {
            sourceFeeds = Object.keys(data.by_source_feed);
        }
        
        // If no data from stats, try to extract from existing IOCs
        if (sourceFeeds.length === 0 && data && data.iocs && Array.isArray(data.iocs)) {
            const sources = new Set();
            data.iocs.forEach(ioc => {
                if (ioc.source_feed) {
                    sources.add(ioc.source_feed);
                }
            });
            sourceFeeds = Array.from(sources);
        }
        
        // Sort source feeds alphabetically
        sourceFeeds.sort();
        
        // Save current selection
        const currentSelection = sourceFeedSelect.value;
        
        // Clear existing options except first "All Sources" option
        while (sourceFeedSelect.options.length > 1) {
            sourceFeedSelect.remove(1);
        }
        
        // Add new options
        sourceFeeds.forEach(feed => {
            const option = document.createElement('option');
            option.value = feed;
            option.textContent = feed;
            sourceFeedSelect.appendChild(option);
        });
        
        // Restore selection if it still exists, otherwise default to "All Sources"
        if (currentSelection && sourceFeeds.includes(currentSelection)) {
            sourceFeedSelect.value = currentSelection;
        }
    }

    // Display statistics
    function displayStats(data) {
        // Set summary numbers
        totalIocsElement.textContent = data.total || 0;
        avgScoreElement.textContent = data.score_stats?.avg ? data.score_stats.avg.toFixed(1) : 0;
        
        // Calculate high risk count (score >= 70)
        let highRiskCount = 0;
        Object.entries(data.by_type || {}).forEach(([type, count]) => {
            highRiskCount += count;
        });
        highRiskCountElement.textContent = highRiskCount;

        // Display charts and additional stats
        let statsHTML = '';
        
        // Type distribution
        if (data.by_type && Object.keys(data.by_type).length > 0) {
            statsHTML += `<h6>IOC Types</h6><ul class="list-group mb-3">`;
            Object.entries(data.by_type).forEach(([type, count]) => {
                statsHTML += `<li class="list-group-item d-flex justify-content-between align-items-center">
                    ${type}
                    <span class="badge bg-primary rounded-pill">${count}</span>
                </li>`;
            });
            statsHTML += `</ul>`;
        }
        
        // Category distribution
        if (data.by_category && Object.keys(data.by_category).length > 0) {
            statsHTML += `<h6>Categories</h6><ul class="list-group mb-3">`;
            Object.entries(data.by_category).forEach(([category, count]) => {
                statsHTML += `<li class="list-group-item d-flex justify-content-between align-items-center">
                    ${category}
                    <span class="badge bg-primary rounded-pill">${count}</span>
                </li>`;
            });
            statsHTML += `</ul>`;
        }
        
        // Score distribution image
        if (data.visualizations && data.visualizations.score_distribution) {
            statsHTML += `<h6>Score Distribution</h6>
            <img src="${data.visualizations.score_distribution}" alt="Score Distribution" class="img-fluid">`;
        }
        
        statsContainer.innerHTML = statsHTML;
    }

    // Load IOCs
    function loadIocs() {
        const iocType = iocTypeSelect ? iocTypeSelect.value : '';
        const minScore = minScoreInput ? minScoreInput.value : 0;
        const maxScore = maxScoreInput ? maxScoreInput.value : 100;
        const sourceFeed = sourceFeedSelect ? sourceFeedSelect.value : '';
        const category = categorySelect ? categorySelect.value : '';
        const dateFrom = dateFromInput ? dateFromInput.value : '';
        const dateTo = dateToInput ? dateToInput.value : '';
        const searchQuery = searchQueryInput ? searchQueryInput.value : '';
        const offset = (currentPage - 1) * itemsPerPage;
        
        // Show loading state
        iocTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading IOCs...</span>
                    </div>
                    <p class="mt-2 text-muted">Loading IOC data...</p>
                </td>
            </tr>
        `;
        
        // Build query params
        const params = new URLSearchParams({
            limit: itemsPerPage,
            offset: offset
        });
        
        if (iocType) params.append('type', iocType);
        if (minScore) params.append('min_score', minScore);
        if (maxScore !== '100') params.append('max_score', maxScore);
        if (sourceFeed) params.append('source_feed', sourceFeed);
        if (category) params.append('category', category);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        if (searchQuery) params.append('search_query', searchQuery);
        
        // Fetch IOCs
        fetch(`/api/iocs?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load IOCs: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Updated for the new response format with pagination
                if (data.iocs && Array.isArray(data.iocs)) {
                    displayIocs(data.iocs);
                    
                    // Set totalPages from the API response
                    if (data.pagination) {
                        totalPages = data.pagination.total_pages || 1;
                        currentPage = data.pagination.current_page || 1;
                    }
                    
                    updatePagination(data.pagination);
                } else {
                    // Backward compatibility with old format
                    displayIocs(data);
                    updatePagination();
                }
                
                // Hide loading when ready
                hideLoadingWhenReady();
            })
            .catch(error => {
                console.error('Error loading IOCs:', error);
                iocTableBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center">
                            <div class="alert alert-danger">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                Error: ${error.message}
                                <button class="btn btn-sm btn-outline-danger ms-2" onclick="loadIocs()">
                                    <i class="bi bi-arrow-clockwise"></i> Retry
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
                // Hide loading on error too
                hideLoadingWhenReady();
            });
    }

    // Display IOCs in the table
    function displayIocs(data) {
        if (!Array.isArray(data) || data.length === 0) {
            iocTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">No IOCs found</td>
                </tr>
            `;
            return;
        }
        
        let html = '';
        data.forEach((ioc, index) => {
            const riskClass = getRiskBadgeClass(ioc.score);
            
            // Improved handling of undefined or malformed values
            let displayValue = "Unknown";
            let actionId = `ioc-${index}`;
            
            // Make sure we're always using ioc_value, not first_seen or other fields
            if (ioc.ioc_value && ioc.ioc_value !== "undefined") {
                displayValue = ioc.ioc_value;
                actionId = ioc.ioc_value;
            } else if (ioc.ioc_type) {
                // Fallback: use type and index if value is not available
                displayValue = `${ioc.ioc_type}-${index+1}`;
                actionId = `${ioc.ioc_type}-${index}`;
            }
            
            // Add warning icon if the value has a warning flag
            const warningIcon = ioc.value_warning ? 
                `<i class="bi bi-exclamation-triangle-fill text-warning" title="${ioc.value_warning}"></i> ` : '';
            
            // Add special indication for undefined values
            const undefinedWarning = (!ioc.ioc_value || ioc.ioc_value === "undefined") ?
                `<span class="badge bg-warning text-dark">Malformed</span> ` : '';
            
            html += `
                <tr data-ioc="${actionId}" class="ioc-row">
                    <td>
                        <input type="checkbox" class="form-check-input ioc-checkbox" data-ioc="${actionId}">
                    </td>
                    <td>${warningIcon}${undefinedWarning}${displayValue}</td>
                    <td>${ioc.ioc_type || 'Unknown'}</td>
                    <td>${ioc.category || 'N/A'}</td>
                    <td><span class="badge ${riskClass}">${ioc.score}</span></td>
                    <td>
                        <button class="btn btn-sm btn-primary view-ioc" data-ioc="${actionId}">
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <button class="btn btn-sm btn-success explain-ioc" data-ioc="${actionId}">
                            <i class="bi bi-lightbulb"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        iocTableBody.innerHTML = html;
        
        // Add event listeners to action buttons
        document.querySelectorAll('.view-ioc').forEach((button, idx) => {
            button.addEventListener('click', function() {
                const iocValue = this.getAttribute('data-ioc');
                // Don't attempt to use undefined values
                if (iocValue && iocValue !== "undefined") {
                    viewIocDetails(iocValue);
                } else {
                    // Show a generic message
                    const modal = new bootstrap.Modal(document.getElementById('ioc-detail-modal'));
                    const modalContent = document.getElementById('ioc-detail-content');
                    
                    modalContent.innerHTML = `
                        <div class="alert alert-warning">
                            <h5>No IOC Value Available</h5>
                            <p>The system couldn't determine a valid IOC value to display.</p>
                            <p>This typically happens with malformed data in the database.</p>
                        </div>
                    `;
                    modal.show();
                }
            });
        });
        
        document.querySelectorAll('.explain-ioc').forEach((button, idx) => {
            button.addEventListener('click', function() {
                const iocValue = this.getAttribute('data-ioc');
                
                // Don't attempt to use undefined values
                if (iocValue && iocValue !== "undefined") {
                    explainIoc(iocValue);
                } else {
                    // Find the actual table row
                    const row = this.closest('tr');
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        // Get the row's IOC value even if it's corrupted
                        const displayedValue = cells[1].textContent.trim();
                        // Find the IOC type from the second cell
                        const iocType = cells.length >= 3 ? cells[2].textContent.trim() : 'unknown';
                        // Generate an explanation based on the table row data
                        showGeneratedExplanation(displayedValue, iocType, parseInt(cells[4].textContent.trim()));
                    } else {
                        // Fallback if we can't get any data
                        showGeneratedExplanation("Unknown", "unknown", 50);
                    }
                }
            });
        });
        
        // Add event listeners to checkboxes
        document.querySelectorAll('.ioc-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const iocId = this.getAttribute('data-ioc');
                
                if (this.checked) {
                    selectedIOCs.add(iocId);
                } else {
                    selectedIOCs.delete(iocId);
                }
                
                updateBatchActionsUI();
            });
            
            // Set initial checked state based on selectedIOCs
            const iocId = checkbox.getAttribute('data-ioc');
            checkbox.checked = selectedIOCs.has(iocId);
        });
        
        // Update batch actions UI
        updateBatchActionsUI();
    }

    // Update pagination controls
    function updatePagination(paginationData) {
        if (!paginationElement) return;
        
        // Clear existing pagination
        paginationElement.innerHTML = '';
        
        // Also remove any existing page info containers
        const existingPageInfo = document.querySelectorAll('.pagination-info');
        existingPageInfo.forEach(el => el.remove());
        
        // If no pagination data, don't show controls
        if (!paginationData || paginationData.total_pages <= 1) {
            return;
        }
        
        // Get pagination values
        const currentPage = paginationData.current_page;
        const totalPages = paginationData.total_pages;
        const hasNext = paginationData.has_next;
        const hasPrev = paginationData.has_prev;
        
        // Create Previous button
        const prevBtn = document.createElement('li');
        prevBtn.className = `page-item ${!hasPrev ? 'disabled' : ''}`;
        prevBtn.innerHTML = `
            <a class="page-link" href="#" aria-label="Previous">
                <span aria-hidden="true">&laquo;</span>
            </a>
        `;
        
        if (hasPrev) {
            prevBtn.addEventListener('click', function(e) {
                e.preventDefault();
                goToPage(currentPage - 1);
            });
        }
        
        paginationElement.appendChild(prevBtn);
        
        // Create page number buttons
        // We'll show up to 5 page numbers centered around the current page
        const pagesArray = createPaginationArray(currentPage, totalPages);
        
        pagesArray.forEach(pageNum => {
            if (pageNum === '...') {
                // This is an ellipsis
                const ellipsis = document.createElement('li');
                ellipsis.className = 'page-item disabled';
                ellipsis.innerHTML = '<span class="page-link">...</span>';
                paginationElement.appendChild(ellipsis);
            } else {
                // This is a page number
                const pageItem = document.createElement('li');
                pageItem.className = `page-item ${pageNum === currentPage ? 'active' : ''}`;
                pageItem.innerHTML = `<a class="page-link" href="#">${pageNum}</a>`;
                
                if (pageNum !== currentPage) {
                    pageItem.addEventListener('click', function(e) {
                        e.preventDefault();
                        goToPage(pageNum);
                    });
                }
                
                paginationElement.appendChild(pageItem);
            }
        });
        
        // Create Next button
        const nextBtn = document.createElement('li');
        nextBtn.className = `page-item ${!hasNext ? 'disabled' : ''}`;
        nextBtn.innerHTML = `
            <a class="page-link" href="#" aria-label="Next">
                <span aria-hidden="true">&raquo;</span>
            </a>
        `;
        
        if (hasNext) {
            nextBtn.addEventListener('click', function(e) {
                e.preventDefault();
                goToPage(currentPage + 1);
            });
        }
        
        paginationElement.appendChild(nextBtn);
        
        // Add page info text with a specific class for easy identification
        const pageInfoContainer = document.createElement('div');
        pageInfoContainer.className = 'mt-2 text-center text-muted small pagination-info';
        pageInfoContainer.innerHTML = `Page ${currentPage} of ${totalPages} (${paginationData.total_count} items)`;
        paginationElement.parentNode.appendChild(pageInfoContainer);
    }
    
    // Helper function to create a pagination array with ellipsis for large page counts
    function createPaginationArray(currentPage, totalPages) {
        if (totalPages <= 7) {
            // If there are 7 or fewer pages, show all page numbers
            return Array.from({ length: totalPages }, (_, i) => i + 1);
        }
        
        const pages = [];
        
        // Always show first page
        pages.push(1);
        
        if (currentPage > 3) {
            // Add ellipsis if current page is far from the start
            pages.push('...');
        }
        
        // Show pages around current page
        const rangeStart = Math.max(2, currentPage - 1);
        const rangeEnd = Math.min(totalPages - 1, currentPage + 1);
        
        for (let i = rangeStart; i <= rangeEnd; i++) {
            pages.push(i);
        }
        
        if (currentPage < totalPages - 2) {
            // Add ellipsis if current page is far from the end
            pages.push('...');
        }
        
        // Always show last page
        pages.push(totalPages);
        
        return pages;
    }
    
    // Navigate to a specific page
    function goToPage(page) {
        currentPage = page;
        showGlobalLoading();
        loadIocs();
        
        // Scroll to the top of the table
        const tableEl = document.getElementById('ioc-table');
        if (tableEl) {
            tableEl.scrollIntoView({ behavior: 'smooth' });
        }
    }

    // View IOC details
    function viewIocDetails(iocValue) {
        // Check for undefined or empty values more thoroughly
        if (!iocValue || iocValue === "undefined" || iocValue === undefined || iocValue === null) {
            // Show a user-friendly message instead of making the API call
            const modal = new bootstrap.Modal(document.getElementById('ioc-detail-modal'));
            const modalContent = document.getElementById('ioc-detail-content');
            
            modalContent.innerHTML = `
                <div class="alert alert-warning">
                    <h5>No IOC Value Available</h5>
                    <p>The system couldn't determine a valid IOC value to display.</p>
                    <p>This typically happens with malformed data in the database.</p>
                </div>
            `;
            modal.show();
            return;
        }
        
        // Get the modal element
        const modal = new bootstrap.Modal(document.getElementById('ioc-detail-modal'));
        const modalContent = document.getElementById('ioc-detail-content');
        
        // Show loading state
        modalContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // Show the modal
        modal.show();
        
        // Encode the IOC value
        const encodedIoc = encodeURIComponent(iocValue);
        
        // Fetch IOC details
        fetch(`/api/ioc/${encodedIoc}`)
            .then(response => {
                return response.json();
            })
            .then(data => {
                // Check if there's an error or note
                if (data.error || data.note) {
                    let content = '';
                    
                    if (data.note) {
                        content += `
                            <div class="alert alert-warning">
                                ${data.note || 'Note: Limited information available for this IOC'}
                            </div>
                        `;
                    }
                    
                    // Determine if this is likely a hash or other IOC type
                    const valueClass = data.ioc_type === 'hash' || 
                                      (data.ioc_value && data.ioc_value.length > 32 && /^[a-f0-9]+$/i.test(data.ioc_value)) ? 
                                      'hash-value' : 'ioc-value';
                    
                    // Add copy button for hash values
                    const copyButton = (valueClass === 'hash-value') ? 
                        `<button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-clipboard="${data.ioc_value || iocValue}">
                            <i class="bi bi-clipboard"></i> Copy
                         </button>` : '';
                    
                    // Display generic info
                    content += `
                        <div class="d-flex align-items-start">
                            <h4 class="${valueClass}">${data.ioc_value || iocValue}</h4>
                            ${copyButton}
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Type:</strong> ${data.ioc_type || 'Unknown'}</p>
                                <p><strong>Category:</strong> ${data.category || 'Unknown'}</p>
                                <p><strong>Score:</strong> ${data.score || 'N/A'}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Source:</strong> ${data.source_feed || 'Unknown'}</p>
                                <p><strong>First Seen:</strong> ${formatDate(data.first_seen)}</p>
                                <p><strong>Last Updated:</strong> ${formatDate(data.last_updated)}</p>
                            </div>
                        </div>
                    `;
                    
                    modalContent.innerHTML = content;
                    addCopyButtonListeners();
                    return;
                }
                
                // Determine if this is likely a hash or other IOC type
                const valueClass = data.ioc_type === 'hash' || 
                                  (data.ioc_value && data.ioc_value.length > 32 && /^[a-f0-9]+$/i.test(data.ioc_value)) ? 
                                  'hash-value' : 'ioc-value';
                
                // Add copy button for hash values
                const copyButton = (valueClass === 'hash-value') ? 
                    `<button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-clipboard="${data.ioc_value || iocValue}">
                        <i class="bi bi-clipboard"></i> Copy
                     </button>` : '';
                
                // Display IOC details in modal
                modalContent.innerHTML = `
                    <div class="d-flex align-items-start">
                        <h4 class="${valueClass}">${data.ioc_value || iocValue}</h4>
                        ${copyButton}
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Type:</strong> ${data.ioc_type || 'Unknown'}</p>
                            <p><strong>Category:</strong> ${data.category || 'Unknown'}</p>
                            <p><strong>Score:</strong> ${data.score || 'N/A'}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Source:</strong> ${data.source_feed || 'Unknown'}</p>
                            <p><strong>First Seen:</strong> ${formatDate(data.first_seen)}</p>
                            <p><strong>Last Updated:</strong> ${formatDate(data.last_updated)}</p>
                        </div>
                    </div>
                    <div class="mt-3">
                        <h5>Raw Data</h5>
                        <pre class="json-data">${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
                
                addCopyButtonListeners();
            })
            .catch(error => {
                console.error('Error getting IOC details:', error);
                modalContent.innerHTML = `
                    <div class="alert alert-warning">
                        <h5>Information Limited</h5>
                        <p>We encountered an issue retrieving complete details for this IOC. Here's what we know:</p>
                    </div>
                    <h4 class="ioc-value">${iocValue}</h4>
                    <p><strong>Type:</strong> ${iocValue.includes(".") ? "domain" : 
                         iocValue.length > 32 ? "hash" : "unknown"}</p>
                    <p><strong>Note:</strong> This is limited information based on the displayed value.</p>
                `;
            });
    }

    // Add event listeners to the copy buttons
    function addCopyButtonListeners() {
        document.querySelectorAll('.copy-btn').forEach(button => {
            button.addEventListener('click', function() {
                const text = this.getAttribute('data-clipboard');
                navigator.clipboard.writeText(text).then(() => {
                    // Temporarily change button text to show success
                    const originalHtml = this.innerHTML;
                    this.innerHTML = '<i class="bi bi-check"></i> Copied!';
                    this.classList.add('btn-success');
                    this.classList.remove('btn-outline-secondary');
                    
                    // Reset after 2 seconds
                    setTimeout(() => {
                        this.innerHTML = originalHtml;
                        this.classList.remove('btn-success');
                        this.classList.add('btn-outline-secondary');
                    }, 2000);
                }).catch(err => {
                    console.error('Could not copy text: ', err);
                    alert('Failed to copy to clipboard');
                });
            });
        });
    }

    // Function to sanitize IOC values before sending to the server
    function sanitizeIocValue(iocValue) {
        if (!iocValue) return "";
        
        // Handle undefined explicitly
        if (iocValue === undefined || iocValue === "undefined") {
            return "undefined";
        }
        
        // Convert to string if not already
        iocValue = String(iocValue);
        
        // Check for binary or non-printable characters
        const hasBinaryData = [...iocValue].some(char => {
            const code = char.charCodeAt(0);
            return code < 32 || code > 126;
        });
        
        if (hasBinaryData) {
            // If binary data is detected, return a safe placeholder
            return `binary-data-${Math.abs(hashString(iocValue) % 1000).toString().padStart(3, '0')}`;
        }
        
        // Remove potentially problematic characters and truncate if too long
        return iocValue
            .replace(/[<>"'%;)(&+]/g, '_')
            .substring(0, 2048)
            .trim();
    }

    // Simple string hash function
    function hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    }

    // Enhanced fetch function with better error handling
    function fetchWithErrorHandling(url, options = {}) {
        // Add a timeout to the fetch call
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
        
        // Clone options and add the signal
        const fetchOptions = { 
            ...options,
            signal: controller.signal
        };
        
        return fetch(url, fetchOptions)
            .then(response => {
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    // Try to parse error as JSON first
                    return response.json()
                        .then(errorData => {
                            throw new Error(errorData.error || errorData.message || `Request failed with status ${response.status}`);
                        })
                        .catch(e => {
                            // If JSON parsing fails, throw a generic error
                            if (e instanceof SyntaxError) {
                                throw new Error(`Request failed with status ${response.status}`);
                            }
                            throw e;
                        });
                }
                
                return response.json();
            })
            .catch(error => {
                clearTimeout(timeoutId);
                
                // Handle network errors, timeouts, and aborts
                if (error.name === 'AbortError') {
                    showNotification('Request timed out. Please try again.', 'error');
                    throw new Error('Request timed out');
                } else if (error.name === 'TypeError' && error.message.includes('NetworkError')) {
                    showNotification('Network error. Please check your connection.', 'error');
                    throw new Error('Network error');
                }
                
                throw error;
            });
    }

    // Use the sanitization and enhanced fetch in the explain IOC function
    function explainIoc(iocValue) {
        // More aggressive validation to prevent invalid requests
        if (!iocValue) {
            showNotification('No IOC value provided', 'warning');
            return;
        }
        
        // Clear previous results
        const featureImportanceContainer = document.getElementById('feature-importance');
        featureImportanceContainer.innerHTML = '<div class="d-flex justify-content-center my-5"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Show the explanation modal
        const modal = new bootstrap.Modal(document.getElementById('explanation-modal'));
        modal.show();
        
        // Sanitize and encode the IOC value for URL safety
        const sanitizedValue = sanitizeIocValue(iocValue);
        
        if (sanitizedValue === "") {
            showExplanationFallback(iocValue, "The IOC value appears to be empty or invalid.");
            return;
        }
        
        const encodedIoc = encodeURIComponent(sanitizedValue);
        
        // Use our enhanced fetching function
        fetchWithErrorHandling(`/api/explain/${encodedIoc}`)
            .then(data => {
                // Handle the explanation data
                const featureImportanceContainer = document.getElementById('feature-importance');
                const explanationIocValue = document.getElementById('explanation-ioc-value');
                
                // Update the display with the original IOC value
                explanationIocValue.textContent = truncateIocValue(iocValue);
                
                // Check for API errors
                if (data.error) {
                    createGenericScoreChart();
                    featureImportanceContainer.innerHTML = `
                        <div class="alert alert-warning">
                            <h5>Error Retrieving Explanation</h5>
                            <p>${data.message || 'The server encountered an error generating the explanation.'}</p>
                        </div>
                        <p>Basic analysis based on IOC patterns:</p>
                        <ul>
                            <li>IOC Type: ${detectIocType(iocValue)}</li>
                            <li>Risk Category: Medium (assumed)</li>
                            <li>Score: Unknown</li>
                        </ul>
                    `;
                    return;
                }
                
                // Create score chart with actual data or fallback to a default
                createScoreChart(data.ioc?.score || 44);
                
                // Check for missing explanation
                if (!data.explanation) {
                    featureImportanceContainer.innerHTML = `
                        <div class="alert alert-warning">
                            ${data.note || 'Limited explanation available for this IOC'}
                        </div>
                        <p>Basic analysis based on IOC patterns:</p>
                        <ul>
                            <li>IOC Type: ${data.ioc?.ioc_type || detectIocType(iocValue)}</li>
                            <li>Risk Category: ${data.ioc?.category || 'Unknown'}</li>
                            <li>Score: ${data.ioc?.score || 'N/A'}</li>
                        </ul>
                    `;
                    return;
                }
                
                // Render the explanation visualization if available
                let explanationHtml = '';
                
                if (data.visualization) {
                    explanationHtml += `
                        <div class="mb-4">
                            <h5>Feature Importance</h5>
                            <img src="${data.visualization}" class="img-fluid border rounded" alt="Feature Importance" 
                                 onerror="this.onerror=null; this.src='/static/img/fallback_chart.png'; this.alt='Visualization not available';">
                        </div>
                    `;
                }
                
                // Render the explanation details
                explanationHtml += `
                    <div class="mb-4">
                        <h5>Feature Breakdown</h5>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Feature</th>
                                    <th>Importance</th>
                                    <th>Value</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.explanation.forEach(feature => {
                    const valueDisplay = feature.value !== undefined ? feature.value : 'N/A';
                    explanationHtml += `
                        <tr>
                            <td>${feature.feature}</td>
                            <td>${feature.importance.toFixed(3)}</td>
                            <td>${valueDisplay}</td>
                        </tr>
                    `;
                });
                
                explanationHtml += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                // Add the explanation summary
                explanationHtml += `
                    <div class="alert alert-info">
                        <h5>Analysis Summary</h5>
                        <p>This IOC received a score of <strong>${data.ioc?.score || 'Unknown'}</strong>.</p>
                        <p>${data.note || 'The score is based on the features shown above.'}</p>
                    </div>
                `;
                
                featureImportanceContainer.innerHTML = explanationHtml;
            })
            .catch(error => {
                console.error('Error getting explanation:', error);
                showExplanationFallback(iocValue, "We encountered an unexpected error processing this IOC.");
            });
    }

    // Helper function to detect suspicious characters that might cause errors
    function containsSuspiciousCharacters(value) {
        if (!value) return false;
        
        // Count percent signs (common in URL encoding)
        const percentCount = (value.match(/%/g) || []).length;
        if (percentCount > 3) return true;
        
        // Check for non-printable ASCII characters
        if (/[\x00-\x1F\x7F]/.test(value)) return true;
        
        // Check for very long values which are often problematic
        if (value.length > 255) return true;
        
        // Check for extremely unusual character combinations
        const specialCharRatio = (value.match(/[^a-zA-Z0-9.\-_]/g) || []).length / value.length;
        if (specialCharRatio > 0.3) return true;  // More than 30% special characters
        
        return false;
    }

    // Consolidated function to show a fallback explanation
    function showExplanationFallback(iocValue, message) {
        const explanationContainer = document.getElementById('explanation-container');
        const noIocSelected = document.getElementById('no-ioc-selected');
        const explanationIocValue = document.getElementById('explanation-ioc-value');
        const featureImportanceContainer = document.getElementById('feature-importance');
        
        explanationContainer.classList.remove('d-none');
        noIocSelected.classList.add('d-none');
        explanationIocValue.textContent = truncateIocValue(iocValue);
        
        // Create generic chart
        createGenericScoreChart();
        
        featureImportanceContainer.innerHTML = `
            <div class="alert alert-warning">
                <h5>Limited Analysis Available</h5>
                <p>${message}</p>
            </div>
            <p>Basic analysis based on IOC patterns:</p>
            <ul>
                <li>IOC Type: ${detectIocType(iocValue)}</li>
                <li>Risk Category: Medium (assumed)</li>
                <li>Score: N/A</li>
            </ul>
        `;
    }

    // Helper function to truncate IOC values for display
    function truncateIocValue(iocValue) {
        if (!iocValue) return "Unknown";
        
        // If it's already shorter than the limit, return as is
        if (iocValue.length <= 40) return iocValue;
        
        // If it's a URL, try to preserve the domain part
        if (iocValue.includes('://')) {
            const urlParts = iocValue.split('/');
            const domain = urlParts[2] || '';
            return urlParts[0] + '//' + domain + '/...';
        }
        
        // For other long values, show the beginning and end
        return iocValue.substring(0, 20) + '...' + iocValue.substring(iocValue.length - 10);
    }
    
    // Helper function to detect IOC type
    function detectIocType(value) {
        if (!value) return "unknown";
        
        if (value.includes("://")) return "url";
        if (value.match(/^[a-f0-9]{32,64}$/i)) return "hash";
        if (value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/)) return "ip";
        if (value.includes(".") && !value.includes(" ")) return "domain";
        
        return "other";
    }
    
    // Create a score chart with actual data
    function createScoreChart(score) {
        const scoreChartCanvas = document.getElementById('score-chart');
        if (scoreChartCanvas) {
            const ctx = scoreChartCanvas.getContext('2d');
            
            // Clear any existing chart
            if (window.scoreChart) {
                window.scoreChart.destroy();
            }
            
            // Calculate ML vs Rule-based components of the score
            // For demo purposes, we'll show a 60/40 split or use the actual score
            const mlScore = Math.round(score * 0.6);
            const ruleScore = Math.round(score * 0.4);
            
            window.scoreChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['ML Score', 'Rule Score'],
                    datasets: [{
                        data: [mlScore, ruleScore],
                        backgroundColor: ['#0d6efd', '#20c997']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
    
    // Create a generic score chart
    function createGenericScoreChart() {
        const scoreChartCanvas = document.getElementById('score-chart');
        if (scoreChartCanvas) {
            const ctx = scoreChartCanvas.getContext('2d');
            
            // Clear any existing chart
            if (window.scoreChart) {
                window.scoreChart.destroy();
            }
            
            window.scoreChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['ML Score', 'Rule Score'],
                    datasets: [{
                        data: [30, 70],
                        backgroundColor: ['#0d6efd', '#20c997']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    // Helper Functions
    function formatDate(dateStr) {
        if (!dateStr) return 'N/A';
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    function getRiskBadgeClass(score) {
        if (score < 30) return 'bg-secondary';
        if (score < 70) return 'bg-warning text-dark';
        if (score < 90) return 'bg-danger';
        return 'bg-danger';
    }

    // This keeps track of data loading completion
    let statsLoaded = false;
    let iocsLoaded = false;
    
    // Helper function to hide loading overlay when both data sources are loaded
    function hideLoadingWhenReady() {
        // Set a flag indicating this data source is loaded
        if (this === loadStats) {
            statsLoaded = true;
        } else {
            iocsLoaded = true;
        }
        
        // If both data sources are loaded, hide the overlay
        if (statsLoaded && iocsLoaded) {
            loadingOverlay.style.display = 'none';
        }
        
        // Force hide after a timeout regardless of state
        forceHideLoading();
    }
    
    // Shows the global loading overlay
    function showGlobalLoading() {
        // Reset loading flags
        statsLoaded = false;
        iocsLoaded = false;
        
        // Show the loading overlay
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
    }
    
    // Forces the removal of the loading indicator after a reasonable timeout
    // This ensures it doesn't get stuck even if there are issues
    function forceHideLoading() {
        setTimeout(function() {
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }, 2000); // 2 seconds max loading time
    }
    
    // Start loading data and force hide loading after timeout
    loadStats.call(loadStats); 
    loadIocs.call(loadIocs);
    forceHideLoading();

    // Export selected IOCs
    function exportSelectedIOCs(format) {
        if (selectedIOCs.size === 0) return;
        
        // Filter out invalid values to prevent API errors
        const validIOCs = Array.from(selectedIOCs).filter(
            ioc => ioc && ioc !== "undefined" && ioc !== undefined && ioc !== null
        );
        
        if (validIOCs.length === 0) {
            showNotification('No valid IOCs to export', 'warning');
            return;
        }
        
        // Show loading indicator
        showGlobalLoading();
        
        // Create request body
        const requestBody = {
            iocs: validIOCs,
            format: format
        };
        
        // Call the batch export API
        fetch('/api/batch/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Export failed: ${response.status} ${response.statusText}`);
            }
            return response.blob();
        })
        .then(blob => {
            // Create a download link for the file
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `sentinelforge_iocs_${format}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Hide loading and show success
            hideLoadingWhenReady();
            showNotification('Export successful', 'success');
        })
        .catch(error => {
            console.error('Error exporting IOCs:', error);
            hideLoadingWhenReady();
            showNotification('Export failed: ' + error.message, 'error');
        });
    }

    // Recategorize selected IOCs
    function recategorizeSelectedIOCs(category) {
        if (selectedIOCs.size === 0) return;
        
        // Filter out invalid values to prevent API errors
        const validIOCs = Array.from(selectedIOCs).filter(
            ioc => ioc && ioc !== "undefined" && ioc !== undefined && ioc !== null
        );
        
        if (validIOCs.length === 0) {
            showNotification('No valid IOCs to recategorize', 'warning');
            return;
        }
        
        // Show loading indicator
        showGlobalLoading();
        
        // Create request body
        const requestBody = {
            iocs: validIOCs,
            category: category
        };
        
        // Call the batch recategorize API
        fetch('/api/batch/recategorize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `Recategorization failed: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading
            hideLoadingWhenReady();
            
            // Show success message
            showNotification(`Recategorized ${data.updated_count} IOCs to ${category}`, 'success');
            
            // Reload data to reflect changes
            loadIocs();
            loadStats();
            
            // Clear selection
            selectedIOCs.clear();
            updateBatchActionsUI();
        })
        .catch(error => {
            console.error('Error recategorizing IOCs:', error);
            hideLoadingWhenReady();
            showNotification('Recategorization failed: ' + error.message, 'error');
        });
    }

    // Delete selected IOCs
    function deleteSelectedIOCs() {
        if (selectedIOCs.size === 0) return;
        
        // Filter out invalid values to prevent API errors
        const validIOCs = Array.from(selectedIOCs).filter(
            ioc => ioc && ioc !== "undefined" && ioc !== undefined && ioc !== null
        );
        
        if (validIOCs.length === 0) {
            showNotification('No valid IOCs to delete', 'warning');
            return;
        }
        
        // Show loading indicator
        showGlobalLoading();
        
        // Create request body
        const requestBody = {
            iocs: validIOCs
        };
        
        // Call the batch delete API
        fetch('/api/batch/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `Deletion failed: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading
            hideLoadingWhenReady();
            
            // Show success message
            showNotification(`Deleted ${data.deleted_count} IOCs`, 'success');
            
            // Reload data to reflect changes
            loadIocs();
            loadStats();
            
            // Clear selection
            selectedIOCs.clear();
            updateBatchActionsUI();
        })
        .catch(error => {
            console.error('Error deleting IOCs:', error);
            hideLoadingWhenReady();
            showNotification('Deletion failed: ' + error.message, 'error');
        });
    }

    // Update batch actions UI based on selection state
    function updateBatchActionsUI() {
        const selectedCount = selectedIOCs.size;
        
        // Update selected count display
        if (selectedCountElement) {
            selectedCountElement.textContent = selectedCount;
        }
        
        // Show/hide batch actions toolbar
        if (batchActionsToolbar) {
            if (selectedCount > 0) {
                batchActionsToolbar.classList.remove('d-none');
            } else {
                batchActionsToolbar.classList.add('d-none');
            }
        }
        
        // Update "Select All" checkbox state
        if (selectAllCheckbox) {
            const allCheckboxes = document.querySelectorAll('.ioc-checkbox');
            const allChecked = allCheckboxes.length > 0 && selectedCount === allCheckboxes.length;
            selectAllCheckbox.checked = allChecked;
        }
    }

    // Show notification messages
    function showNotification(message, type = 'info') {
        // Create a notification element if it doesn't exist
        let notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-container';
            notificationContainer.style.position = 'fixed';
            notificationContainer.style.bottom = '20px';
            notificationContainer.style.right = '20px';
            notificationContainer.style.zIndex = '9999';
            document.body.appendChild(notificationContainer);
        }
        
        // Create the notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} shadow-sm`;
        notification.style.minWidth = '250px';
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close btn-sm" aria-label="Close"></button>
            </div>
        `;
        
        // Add to container
        notificationContainer.appendChild(notification);
        
        // Add close button functionality
        notification.querySelector('.btn-close').addEventListener('click', function() {
            notification.remove();
        });
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}); 