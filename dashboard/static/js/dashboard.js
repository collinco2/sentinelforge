// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const welcomeCard = document.getElementById('welcomeCard');
    const iocDetailsCard = document.getElementById('iocDetailsCard');
    const mlExplanationCard = document.getElementById('mlExplanationCard');
    const highRiskOnly = document.getElementById('highRiskOnly');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Hide details cards initially
    iocDetailsCard.style.display = 'none';
    mlExplanationCard.style.display = 'none';
    
    // Search form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const iocValue = searchInput.value.trim();
        
        if (iocValue) {
            searchIOC(iocValue);
        }
    });
    
    // Search for an IOC
    function searchIOC(iocValue) {
        showLoading();
        
        // Fetch IOC details from API
        fetch(`/api/ioc/${encodeURIComponent(iocValue)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('IOC not found or API error');
                }
                return response.json();
            })
            .then(data => {
                welcomeCard.style.display = 'none';
                displayIOCDetails(data);
                displayMLExplanation(data);
                hideLoading();
            })
            .catch(error => {
                hideLoading();
                showError(`Error: ${error.message}`);
            });
    }
    
    // Display IOC Details
    function displayIOCDetails(data) {
        const iocDetailsContent = document.getElementById('iocDetailsContent');
        const riskBadgeClass = getRiskBadgeClass(data.score);
        
        iocDetailsContent.innerHTML = `
            <h4>${data.value} <span class="badge ${riskBadgeClass}">${data.category}</span></h4>
            <div class="mb-3">
                <strong>Type:</strong> ${data.ioc_type}
            </div>
            <div class="mb-3">
                <strong>Score:</strong> ${data.score}
            </div>
            <div class="mb-3">
                <strong>Source:</strong> ${data.source || 'Unknown'}
            </div>
            <div class="mb-3">
                <strong>First Seen:</strong> ${formatDate(data.first_seen)}
            </div>
            <div class="mb-3">
                <strong>Last Updated:</strong> ${formatDate(data.last_updated)}
            </div>
            <h5 class="mt-4">Raw Data</h5>
            <div class="json-data">${JSON.stringify(data, null, 2)}</div>
        `;
        
        iocDetailsCard.style.display = 'block';
    }
    
    // Display ML Explanation
    function displayMLExplanation(data) {
        if (!data.ml_explanation) {
            mlExplanationCard.style.display = 'none';
            return;
        }
        
        const mlExplanationContent = document.getElementById('mlExplanationContent');
        const explanation = data.ml_explanation;
        
        // Create content for ML explanation
        let content = `
            <div class="mb-3">
                <strong>ML Score:</strong> ${explanation.ml_score} (${explanation.ml_score_normalized} normalized)
            </div>
            <div class="mb-3">
                <strong>Rule Score:</strong> ${explanation.rule_score}
            </div>
            <div class="mb-3">
                <strong>Confidence:</strong> ${(explanation.confidence * 100).toFixed(2)}%
            </div>
        `;
        
        // Add feature contributions
        if (explanation.feature_importance) {
            content += `<h5 class="mt-4">Feature Contributions</h5>`;
            
            // Sort features by absolute importance
            const sortedFeatures = Object.entries(explanation.feature_importance)
                .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
            
            // Get max absolute value for scaling
            const maxValue = Math.max(...sortedFeatures.map(f => Math.abs(f[1])));
            
            // Create bars for top features
            const topFeatures = sortedFeatures.slice(0, 10);
            content += `<div class="feature-bars">`;
            
            topFeatures.forEach(([feature, value]) => {
                const isPositive = value >= 0;
                const barClass = isPositive ? 'feature-bar-positive' : 'feature-bar-negative';
                const width = (Math.abs(value) / maxValue * 100).toFixed(2);
                
                content += `
                    <div class="feature-bar-wrapper">
                        <div class="feature-bar-label">${formatFeatureName(feature)}</div>
                        <div class="feature-bar ${barClass}" style="width: ${width}%">
                            <div class="feature-bar-value">${value.toFixed(4)}</div>
                        </div>
                    </div>
                `;
            });
            
            content += `</div>`;
        }
        
        // Add SHAP visualization placeholder
        content += `
            <h5 class="mt-4">SHAP Values</h5>
            <div id="shap" class="mt-3">
                <p class="text-muted">SHAP visualization goes here</p>
            </div>
        `;
        
        mlExplanationContent.innerHTML = content;
        mlExplanationCard.style.display = 'block';
        
        // In a real implementation, we would call a function to render SHAP visualization using D3.js
        // renderShapVisualization(explanation.shap_values);
    }
    
    // Render SHAP Visualization with D3.js
    function renderShapVisualization(shapValues) {
        // This is a placeholder for the actual D3.js visualization
        // In a real implementation, this would create a waterfall chart or other visualization
        const shapContainer = document.getElementById('shap');
        
        // Example D3 code would go here
    }
    
    // Helper Functions
    function formatDate(dateStr) {
        if (!dateStr) return 'N/A';
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
    
    function formatFeatureName(name) {
        return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    function getRiskBadgeClass(score) {
        if (score < 30) return 'badge-low';
        if (score < 70) return 'badge-medium';
        if (score < 90) return 'badge-high';
        return 'badge-critical';
    }
    
    function showLoading() {
        loadingOverlay.style.display = 'flex';
    }
    
    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }
    
    function showError(message) {
        // Create toast or alert
        alert(message);
    }
}); 