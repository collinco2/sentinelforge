/**
 * 🔍 SentinelForge Dialog Debug Script
 * 
 * Run this script in the browser console on the Settings page to debug
 * the API Key creation dialog issue.
 * 
 * Usage:
 * 1. Navigate to http://localhost:3000/settings
 * 2. Open browser developer tools (F12)
 * 3. Go to Console tab
 * 4. Copy and paste this entire script
 * 5. Press Enter to run
 */

console.log("🔍 Starting SentinelForge Dialog Debug Analysis...");

// 1. Check if user is authenticated
function checkAuthentication() {
    console.log("\n=== 1. AUTHENTICATION CHECK ===");
    
    const sessionToken = localStorage.getItem("session_token");
    console.log("Session token:", sessionToken ? "✅ Present" : "❌ Missing");
    
    if (sessionToken) {
        console.log("Session token preview:", sessionToken.substring(0, 10) + "...");
    }
    
    // Check if user object exists in any global state
    const userInLocalStorage = localStorage.getItem("current_user");
    console.log("User in localStorage:", userInLocalStorage ? "✅ Present" : "❌ Missing");
    
    return !!sessionToken;
}

// 2. Check DOM elements
function checkDOMElements() {
    console.log("\n=== 2. DOM ELEMENTS CHECK ===");
    
    // Check if the Create Key button exists
    const createButton = document.querySelector('[data-testid="create-api-key-button"]');
    console.log("Create Key button:", createButton ? "✅ Found" : "❌ Not found");
    
    if (createButton) {
        console.log("Button text:", createButton.textContent);
        console.log("Button disabled:", createButton.disabled);
        console.log("Button style display:", getComputedStyle(createButton).display);
        console.log("Button style visibility:", getComputedStyle(createButton).visibility);
    }
    
    // Check for any dialog elements
    const dialogs = document.querySelectorAll('[role="dialog"]');
    console.log("Dialog elements found:", dialogs.length);
    
    dialogs.forEach((dialog, index) => {
        console.log(`Dialog ${index + 1}:`, {
            display: getComputedStyle(dialog).display,
            visibility: getComputedStyle(dialog).visibility,
            zIndex: getComputedStyle(dialog).zIndex,
            position: getComputedStyle(dialog).position,
            opacity: getComputedStyle(dialog).opacity
        });
    });
    
    // Check for Radix UI portal containers
    const portals = document.querySelectorAll('[data-radix-portal]');
    console.log("Radix portals found:", portals.length);
    
    return { createButton, dialogs: dialogs.length, portals: portals.length };
}

// 3. Check CSS and styling issues
function checkStyling() {
    console.log("\n=== 3. STYLING CHECK ===");
    
    // Check for potential z-index issues
    const highZIndexElements = [];
    document.querySelectorAll('*').forEach(el => {
        const zIndex = getComputedStyle(el).zIndex;
        if (zIndex !== 'auto' && parseInt(zIndex) > 1000) {
            highZIndexElements.push({
                element: el.tagName + (el.className ? '.' + el.className.split(' ').join('.') : ''),
                zIndex: zIndex
            });
        }
    });
    
    console.log("High z-index elements:", highZIndexElements);
    
    // Check for overflow hidden that might clip dialogs
    const overflowHiddenElements = [];
    document.querySelectorAll('*').forEach(el => {
        const overflow = getComputedStyle(el).overflow;
        if (overflow === 'hidden') {
            overflowHiddenElements.push(el.tagName + (el.className ? '.' + el.className.split(' ').join('.') : ''));
        }
    });
    
    console.log("Overflow hidden elements:", overflowHiddenElements.slice(0, 10)); // Limit output
}

// 4. Test API endpoints
async function testAPIEndpoints() {
    console.log("\n=== 4. API ENDPOINTS TEST ===");
    
    const sessionToken = localStorage.getItem("session_token");
    if (!sessionToken) {
        console.log("❌ Cannot test API - no session token");
        return;
    }
    
    try {
        // Test session validity
        const sessionResponse = await fetch("/api/session", {
            headers: { "X-Session-Token": sessionToken }
        });
        const sessionData = await sessionResponse.json();
        console.log("Session check:", sessionResponse.ok ? "✅ Valid" : "❌ Invalid");
        console.log("Session data:", sessionData);
        
        // Test API keys endpoint
        const apiKeysResponse = await fetch("/api/user/api-keys", {
            headers: { "X-Session-Token": sessionToken }
        });
        const apiKeysData = await apiKeysResponse.json();
        console.log("API keys endpoint:", apiKeysResponse.ok ? "✅ Working" : "❌ Failed");
        console.log("API keys data:", apiKeysData);
        
    } catch (error) {
        console.log("❌ API test error:", error);
    }
}

// 5. Test dialog functionality manually
function testDialogManually() {
    console.log("\n=== 5. MANUAL DIALOG TEST ===");
    
    // Try to find and click the create button
    const createButton = document.querySelector('[data-testid="create-api-key-button"]');
    if (createButton) {
        console.log("Attempting to click Create Key button...");
        
        // Add event listener to see if click is registered
        createButton.addEventListener('click', (e) => {
            console.log("✅ Click event fired on Create Key button");
            console.log("Event details:", e);
        }, { once: true });
        
        // Simulate click
        createButton.click();
        
        // Check if dialog appeared after a short delay
        setTimeout(() => {
            const dialogs = document.querySelectorAll('[role="dialog"]');
            console.log("Dialogs after click:", dialogs.length);
            
            if (dialogs.length > 0) {
                console.log("✅ Dialog found after click!");
                dialogs.forEach((dialog, index) => {
                    console.log(`Dialog ${index + 1} visibility:`, {
                        display: getComputedStyle(dialog).display,
                        visibility: getComputedStyle(dialog).visibility,
                        opacity: getComputedStyle(dialog).opacity
                    });
                });
            } else {
                console.log("❌ No dialog found after click");
            }
        }, 500);
    } else {
        console.log("❌ Create Key button not found");
    }
}

// 6. Check React DevTools (if available)
function checkReactDevTools() {
    console.log("\n=== 6. REACT DEVTOOLS CHECK ===");
    
    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
        console.log("✅ React DevTools detected");
        console.log("React version:", window.React?.version || "Unknown");
    } else {
        console.log("❌ React DevTools not detected");
    }
    
    // Check for React Fiber
    const reactFiber = document.querySelector('#root')?._reactInternalFiber || 
                      document.querySelector('#root')?._reactInternalInstance;
    console.log("React Fiber:", reactFiber ? "✅ Found" : "❌ Not found");
}

// 7. Generate debug report
function generateDebugReport() {
    console.log("\n=== 7. DEBUG REPORT SUMMARY ===");
    
    const report = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        authentication: checkAuthentication(),
        domElements: checkDOMElements(),
        // Add more checks as needed
    };
    
    console.log("Debug Report:", report);
    
    // Provide recommendations
    console.log("\n=== RECOMMENDATIONS ===");
    if (!report.authentication) {
        console.log("🔧 Please log in first: http://localhost:3000/login");
    }
    if (!report.domElements.createButton) {
        console.log("🔧 Create Key button not found - check if component is rendering");
    }
    if (report.domElements.dialogs === 0) {
        console.log("🔧 No dialogs found - this might be the core issue");
    }
    
    return report;
}

// Run all checks
async function runFullDiagnostic() {
    console.log("🚀 Running full diagnostic...");
    
    checkAuthentication();
    checkDOMElements();
    checkStyling();
    await testAPIEndpoints();
    checkReactDevTools();
    
    console.log("\n⏳ Testing dialog manually in 2 seconds...");
    setTimeout(testDialogManually, 2000);
    
    setTimeout(() => {
        generateDebugReport();
        console.log("\n✅ Diagnostic complete! Check the output above for issues.");
    }, 3000);
}

// Auto-run the diagnostic
runFullDiagnostic();

// Export functions for manual testing
window.sentinelForgeDebug = {
    checkAuthentication,
    checkDOMElements,
    checkStyling,
    testAPIEndpoints,
    testDialogManually,
    checkReactDevTools,
    generateDebugReport,
    runFullDiagnostic
};

console.log("\n💡 Functions available in window.sentinelForgeDebug for manual testing");
