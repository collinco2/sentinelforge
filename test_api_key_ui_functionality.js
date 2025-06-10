// SentinelForge API Key UI Testing Script
// Run this in the browser console at http://localhost:3000/settings

console.log("🔧 SentinelForge API Key UI Testing Script");
console.log("📍 Current URL:", window.location.href);

// Test Results Object
const testResults = {
  authentication: null,
  pageLoad: null,
  buttonExists: null,
  modalOpens: null,
  formFunctionality: null,
  apiIntegration: null,
  errors: []
};

// Helper function to wait for elements
function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const element = document.querySelector(selector);
    if (element) {
      resolve(element);
      return;
    }

    const observer = new MutationObserver((mutations, obs) => {
      const element = document.querySelector(selector);
      if (element) {
        obs.disconnect();
        resolve(element);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}

// Helper function to simulate click
function simulateClick(element) {
  const event = new MouseEvent('click', {
    view: window,
    bubbles: true,
    cancelable: true
  });
  element.dispatchEvent(event);
}

// Test 1: Check Authentication Status
async function testAuthentication() {
  console.log("\n🔐 Test 1: Checking Authentication Status");
  
  try {
    const sessionToken = localStorage.getItem('session_token');
    if (!sessionToken) {
      testResults.authentication = "❌ No session token found";
      console.log("❌ No session token found in localStorage");
      return false;
    }

    // Test API call with session token
    const response = await fetch('/api/user/api-keys', {
      headers: {
        'X-Session-Token': sessionToken
      }
    });

    if (response.ok) {
      testResults.authentication = "✅ Authenticated successfully";
      console.log("✅ Authentication successful");
      return true;
    } else {
      testResults.authentication = `❌ Authentication failed: ${response.status}`;
      console.log(`❌ Authentication failed: ${response.status}`);
      return false;
    }
  } catch (error) {
    testResults.authentication = `❌ Authentication error: ${error.message}`;
    console.log(`❌ Authentication error:`, error);
    return false;
  }
}

// Test 2: Check Page Load and Navigation
async function testPageLoad() {
  console.log("\n📄 Test 2: Checking Page Load and Navigation");
  
  try {
    // Check if we're on the settings page
    if (!window.location.href.includes('/settings')) {
      console.log("🔄 Navigating to settings page...");
      window.location.href = '/settings';
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    // Check for API & Tokens tab
    const apiTokensTab = await waitForElement('[value="api-tokens"]', 3000);
    if (apiTokensTab) {
      console.log("✅ API & Tokens tab found");
      simulateClick(apiTokensTab);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    testResults.pageLoad = "✅ Page loaded successfully";
    console.log("✅ Settings page loaded successfully");
    return true;
  } catch (error) {
    testResults.pageLoad = `❌ Page load error: ${error.message}`;
    console.log(`❌ Page load error:`, error);
    return false;
  }
}

// Test 3: Check Create Key Button Exists
async function testButtonExists() {
  console.log("\n🔘 Test 3: Checking Create Key Button");
  
  try {
    const createButton = await waitForElement('[data-testid="create-api-key-button"]', 5000);
    
    if (createButton) {
      testResults.buttonExists = "✅ Create Key button found";
      console.log("✅ Create Key button found:", createButton);
      console.log("📍 Button text:", createButton.textContent);
      console.log("📍 Button classes:", createButton.className);
      return createButton;
    } else {
      testResults.buttonExists = "❌ Create Key button not found";
      console.log("❌ Create Key button not found");
      return null;
    }
  } catch (error) {
    testResults.buttonExists = `❌ Button search error: ${error.message}`;
    console.log(`❌ Button search error:`, error);
    return null;
  }
}

// Test 4: Test Modal Opening
async function testModalOpening(createButton) {
  console.log("\n🪟 Test 4: Testing Modal Opening");
  
  try {
    if (!createButton) {
      testResults.modalOpens = "❌ No button to test";
      return false;
    }

    console.log("🔄 Clicking Create Key button...");
    simulateClick(createButton);
    
    // Wait for modal to appear
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Check for modal dialog
    const modal = document.querySelector('[role="dialog"]');
    const dialogContent = document.querySelector('[data-testid*="dialog"]') || 
                         document.querySelector('.dialog-content') ||
                         document.querySelector('[class*="dialog"]');
    
    if (modal || dialogContent) {
      testResults.modalOpens = "✅ Modal opened successfully";
      console.log("✅ Modal opened successfully");
      console.log("📍 Modal element:", modal || dialogContent);
      return true;
    } else {
      testResults.modalOpens = "❌ Modal did not open";
      console.log("❌ Modal did not open");
      console.log("🔍 Available dialogs:", document.querySelectorAll('[role="dialog"]'));
      return false;
    }
  } catch (error) {
    testResults.modalOpens = `❌ Modal test error: ${error.message}`;
    console.log(`❌ Modal test error:`, error);
    return false;
  }
}

// Test 5: Test Form Functionality
async function testFormFunctionality() {
  console.log("\n📝 Test 5: Testing Form Functionality");
  
  try {
    // Look for form elements
    const nameInput = document.querySelector('[data-testid="api-key-name-input"]') ||
                     document.querySelector('input[placeholder*="API"]') ||
                     document.querySelector('input[id*="key-name"]');
    
    if (nameInput) {
      console.log("✅ Name input field found");
      
      // Test input functionality
      nameInput.value = "Test API Key";
      nameInput.dispatchEvent(new Event('input', { bubbles: true }));
      
      console.log("✅ Input field accepts text");
      testResults.formFunctionality = "✅ Form elements working";
      return true;
    } else {
      testResults.formFunctionality = "❌ Form elements not found";
      console.log("❌ Form elements not found");
      return false;
    }
  } catch (error) {
    testResults.formFunctionality = `❌ Form test error: ${error.message}`;
    console.log(`❌ Form test error:`, error);
    return false;
  }
}

// Test 6: Test API Integration
async function testAPIIntegration() {
  console.log("\n🔌 Test 6: Testing API Integration");
  
  try {
    const sessionToken = localStorage.getItem('session_token');
    if (!sessionToken) {
      testResults.apiIntegration = "❌ No session token for API test";
      return false;
    }

    // Test API key creation endpoint
    const response = await fetch('/api/user/api-keys', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken
      },
      body: JSON.stringify({
        name: 'UI Test Key',
        description: 'Test key created from UI test',
        access_scope: ['read']
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log("✅ API key creation successful:", data);
      testResults.apiIntegration = "✅ API integration working";
      return true;
    } else {
      const error = await response.text();
      testResults.apiIntegration = `❌ API error: ${response.status} - ${error}`;
      console.log(`❌ API error: ${response.status}`, error);
      return false;
    }
  } catch (error) {
    testResults.apiIntegration = `❌ API test error: ${error.message}`;
    console.log(`❌ API test error:`, error);
    return false;
  }
}

// Main Test Runner
async function runAllTests() {
  console.log("🚀 Starting SentinelForge API Key UI Tests");
  console.log("=" * 50);
  
  try {
    // Run tests sequentially
    const isAuthenticated = await testAuthentication();
    if (!isAuthenticated) {
      console.log("⚠️ Authentication failed - some tests may not work");
    }
    
    await testPageLoad();
    const createButton = await testButtonExists();
    await testModalOpening(createButton);
    await testFormFunctionality();
    await testAPIIntegration();
    
    // Print final results
    console.log("\n📊 TEST RESULTS SUMMARY");
    console.log("=" * 50);
    Object.entries(testResults).forEach(([test, result]) => {
      if (test !== 'errors') {
        console.log(`${test}: ${result}`);
      }
    });
    
    if (testResults.errors.length > 0) {
      console.log("\n❌ ERRORS:");
      testResults.errors.forEach(error => console.log(`  - ${error}`));
    }
    
    // Overall status
    const passedTests = Object.values(testResults).filter(result => 
      typeof result === 'string' && result.startsWith('✅')
    ).length;
    const totalTests = Object.keys(testResults).length - 1; // Exclude errors array
    
    console.log(`\n🎯 OVERALL: ${passedTests}/${totalTests} tests passed`);
    
    if (passedTests === totalTests) {
      console.log("🎉 ALL TESTS PASSED! API Key functionality is working correctly.");
    } else {
      console.log("⚠️ Some tests failed. Check the results above for details.");
    }
    
    return testResults;
    
  } catch (error) {
    console.error("💥 Test runner error:", error);
    testResults.errors.push(`Test runner error: ${error.message}`);
    return testResults;
  }
}

// Auto-run tests if this script is executed
if (typeof window !== 'undefined') {
  console.log("🔧 SentinelForge API Key UI Test Script Loaded");
  console.log("📝 Run 'runAllTests()' to start testing");
  console.log("📝 Or run individual tests like 'testAuthentication()'");
  
  // Make functions available globally
  window.sentinelForgeUITest = {
    runAllTests,
    testAuthentication,
    testPageLoad,
    testButtonExists,
    testModalOpening,
    testFormFunctionality,
    testAPIIntegration,
    testResults
  };
}
