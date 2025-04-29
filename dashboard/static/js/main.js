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

    // Pagination variables
    let currentPage = 1;
    const itemsPerPage = 10;
    let totalPages = 1;

    // Initialize
    loadStats();
    loadIocs();

    // Add event listeners
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            currentPage = 1;
            loadIocs();
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

    // Load statistics
    function loadStats() {
        fetch('/api/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load stats');
                }
                return response.json();
            })
            .then(data => {
                displayStats(data);
            })
            .catch(error => {
                console.error('Error loading stats:', error);
                statsContainer.innerHTML = `<div class="alert alert-danger">Error loading statistics: ${error.message}</div>`;
            });
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
        const offset = (currentPage - 1) * itemsPerPage;
        
        // Show loading state
        iocTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
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
        
        // Fetch IOCs
        fetch(`/api/iocs?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load IOCs');
                }
                return response.json();
            })
            .then(data => {
                displayIocs(data);
                updatePagination();
            })
            .catch(error => {
                console.error('Error loading IOCs:', error);
                iocTableBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center">
                            <div class="alert alert-danger">Error: ${error.message}</div>
                        </td>
                    </tr>
                `;
            });
    }

    // Display IOCs in the table
    function displayIocs(data) {
        if (!Array.isArray(data) || data.length === 0) {
            iocTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">No IOCs found</td>
                </tr>
            `;
            return;
        }
        
        let html = '';
        data.forEach((ioc, index) => {
            const riskClass = getRiskBadgeClass(ioc.score);
            // Make sure we're always using ioc_value, not first_seen or other fields
            const displayValue = (ioc.ioc_value && ioc.ioc_value !== "undefined") ? 
                ioc.ioc_value : `IOC-${index+1}`;
            // Store the actual database ID or some unique identifier for actions
            const actionId = (ioc.ioc_value && ioc.ioc_value !== "undefined") ? 
                ioc.ioc_value : `${ioc.ioc_type}-${index}`;
            
            // Add warning icon if the value has a warning flag
            const warningIcon = ioc.value_warning ? 
                `<i class="bi bi-exclamation-triangle-fill text-warning" title="${ioc.value_warning}"></i> ` : '';
            
            html += `
                <tr data-ioc="${actionId}" class="ioc-row">
                    <td>${warningIcon}${displayValue}</td>
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
                // If the IOC value is "undefined", use the row index
                const idToUse = (iocValue === "undefined") ? `row-${idx}` : iocValue;
                viewIocDetails(idToUse);
            });
        });
        
        document.querySelectorAll('.explain-ioc').forEach((button, idx) => {
            button.addEventListener('click', function() {
                const iocValue = this.getAttribute('data-ioc');
                // If the IOC value is "undefined", use a different approach
                if (iocValue === "undefined") {
                    // Find the actual table row
                    const row = this.closest('tr');
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 1) {
                        // Get the row's IOC value even if it's corrupted
                        const displayedValue = cells[0].textContent.trim();
                        // Find the IOC type from the second cell
                        const iocType = cells.length >= 2 ? cells[1].textContent.trim() : 'unknown';
                        // Generate an explanation based on the table row data
                        showGeneratedExplanation(displayedValue, iocType, parseInt(cells[3].textContent.trim()));
                        return;
                    }
                }
                explainIoc(iocValue);
            });
        });
    }

    // Update pagination controls
    function updatePagination() {
        // Placeholder for now - will implement if needed
    }

    // View IOC details
    function viewIocDetails(iocValue) {
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
                    
                    // Display generic info
                    content += `
                        <h4>${data.ioc_value || iocValue}</h4>
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
                    return;
                }
                
                // Display IOC details in modal
                modalContent.innerHTML = `
                    <h4>${data.ioc_value || iocValue}</h4>
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
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
            })
            .catch(error => {
                console.error('Error getting IOC details:', error);
                modalContent.innerHTML = `
                    <div class="alert alert-warning">
                        <h5>Information Limited</h5>
                        <p>We encountered an issue retrieving complete details for this IOC. Here's what we know:</p>
                    </div>
                    <h4>${iocValue}</h4>
                    <p><strong>Type:</strong> ${iocValue.includes(".") ? "domain" : 
                         iocValue.length > 32 ? "hash" : "unknown"}</p>
                    <p><strong>Note:</strong> This is limited information based on the displayed value.</p>
                `;
            });
    }

    // Explain IOC
    function explainIoc(iocValue) {
        const explanationContainer = document.getElementById('explanation-container');
        const noIocSelected = document.getElementById('no-ioc-selected');
        const explanationIocValue = document.getElementById('explanation-ioc-value');
        
        // Show loading state
        explanationContainer.classList.remove('d-none');
        noIocSelected.classList.add('d-none');
        explanationIocValue.textContent = `Analyzing ${iocValue}...`;
        
        // URL encode the IOC value
        const encodedIoc = encodeURIComponent(iocValue);
        
        // Fetch explanation - wrap in try/catch to ensure we never show raw errors
        try {
            fetch(`/api/explain/${encodedIoc}`)
                .then(response => {
                    return response.json();
                })
                .then(data => {
                    // Handle the explanation data
                    const explanationContent = document.getElementById('explanation-content');
                    const explanationIocValue = document.getElementById('explanation-ioc-value');
                    
                    // Update the IOC value display
                    explanationIocValue.textContent = iocValue;
                    
                    if (data.error || !data.explanation) {
                        explanationContent.innerHTML = `
                            <div class="alert alert-warning">
                                ${data.note || 'Limited explanation available for this IOC'}
                            </div>
                            <p>Basic analysis based on IOC patterns:</p>
                            <ul>
                                <li>IOC Type: ${data.ioc?.ioc_type || 'Unknown'}</li>
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
                                <img src="${data.visualization}" class="img-fluid border rounded" alt="Feature Importance">
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
                    
                    explanationContent.innerHTML = explanationHtml;
                })
                .catch(error => {
                    console.error('Error getting explanation:', error);
                    const explanationContent = document.getElementById('explanation-content');
                    const explanationIocValue = document.getElementById('explanation-ioc-value');
                    
                    explanationIocValue.textContent = iocValue;
                    explanationContent.innerHTML = `
                        <div class="alert alert-danger">
                            <h5>Error</h5>
                            <p>We encountered an issue generating an explanation for this IOC.</p>
                            <p>This may be due to the IOC containing special characters or being in an unsupported format.</p>
                        </div>
                        <p>Basic analysis based on IOC patterns:</p>
                        <ul>
                            <li>IOC Type: ${iocValue.includes(".") ? "domain" : 
                                 iocValue.length > 32 ? "hash" : "unknown"}</li>
                            <li>Risk Category: Medium (assumed)</li>
                            <li>Score: N/A</li>
                        </ul>
                    `;
                });
        } catch (e) {
            console.error('Exception in explain function:', e);
            const explanationContent = document.getElementById('explanation-content');
            const explanationIocValue = document.getElementById('explanation-ioc-value');
            
            explanationIocValue.textContent = iocValue;
            explanationContent.innerHTML = `
                <div class="alert alert-danger">
                    <h5>Error</h5>
                    <p>An unexpected error occurred while processing this IOC.</p>
                </div>
            `;
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
    
    // Create a generic explanation HTML
    function createGenericExplanation(iocValue) {
        // Determine likely IOC type based on value
        let iocType = "unknown";
        if (iocValue.length > 32 && /^[a-f0-9]+$/i.test(iocValue.replace(/[^a-f0-9]/gi, ''))) {
            iocType = "hash";
        } else if (iocValue.includes(".") && !iocValue.includes(" ")) {
            if (/^\d+\.\d+\.\d+\.\d+$/.test(iocValue)) {
                iocType = "ip";
            } else {
                iocType = "domain";
            }
        } else if (iocValue.includes("?") || iocValue.includes("://") || iocValue.includes("/")) {
            iocType = "url";
        }
        
        return `
            <div class="alert alert-info mb-3">
                This is a generic explanation based on typical patterns for ${iocType} values.
                The actual ML model features couldn't be calculated.
            </div>
            
            <ul class="list-group">
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>IOC Type (${iocType})</span>
                        <span>0.3500</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 35%" aria-valuenow="35" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>Source Feed</span>
                        <span>0.2500</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 25%" aria-valuenow="25" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>Length (${iocValue.length} characters)</span>
                        <span>0.1500</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 15%" aria-valuenow="15" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>Special Characters</span>
                        <span>0.1000</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 10%" aria-valuenow="10" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>Pattern Recognition</span>
                        <span>0.0500</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 5%" aria-valuenow="5" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
            </ul>
        `;
    }

    // Display a generated explanation when we can't call the API with the corrupted value
    function showGeneratedExplanation(iocValue, iocType, score) {
        const explanationContainer = document.getElementById('explanation-container');
        const noIocSelected = document.getElementById('no-ioc-selected');
        const explanationIocValue = document.getElementById('explanation-ioc-value');
        
        // Show loading state
        explanationContainer.classList.remove('d-none');
        noIocSelected.classList.add('d-none');
        explanationIocValue.textContent = `Analysis for ${iocValue}`;
        
        // Create generic explanation content
        const featureImportanceContainer = document.getElementById('feature-importance');
        let html = `
            <div class="alert alert-info">
                <strong>Note:</strong> This is a generic explanation for this IOC type. 
                The actual model features couldn't be calculated due to data encoding issues.
            </div>
            
            <ul class="list-group">
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>IOC Type (${iocType})</span>
                        <span>0.3500</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 35%" aria-valuenow="35" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>Source Feed</span>
                        <span>0.2500</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 25%" aria-valuenow="25" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
                <li class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <span>Score (${score})</span>
                        <span>0.1500</span>
                    </div>
                    <div class="progress mt-1">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: 15%" aria-valuenow="15" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </li>
            </ul>
        `;
        
        featureImportanceContainer.innerHTML = html;
        
        // Create score chart
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
                        data: [30, 70], // Example values
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
        
        // Scroll to the insights section
        document.getElementById('model-insights').scrollIntoView({
            behavior: 'smooth'
        });
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
}); 