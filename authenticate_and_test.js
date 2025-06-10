// SentinelForge Authentication and Testing Script
// Run this in browser console to authenticate and test API key functionality

console.log("🔐 SentinelForge Authentication and Testing Script");

// Step 1: Authenticate with the API
async function authenticateUser() {
  console.log("🔄 Authenticating user...");
  
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log("✅ Authentication successful:", data);
      
      // Store session token
      if (data.session_token) {
        localStorage.setItem('session_token', data.session_token);
        console.log("💾 Session token stored in localStorage");
        return data.session_token;
      } else {
        console.log("⚠️ No session token in response");
        return null;
      }
    } else {
      const error = await response.text();
      console.log("❌ Authentication failed:", response.status, error);
      return null;
    }
  } catch (error) {
    console.log("💥 Authentication error:", error);
    return null;
  }
}

// Step 2: Navigate to settings page
function navigateToSettings() {
  console.log("🔄 Navigating to settings page...");
  if (window.location.pathname !== '/settings') {
    window.location.href = '/settings';
    return new Promise(resolve => {
      setTimeout(() => {
        console.log("📍 Navigated to:", window.location.href);
        resolve();
      }, 2000);
    });
  } else {
    console.log("📍 Already on settings page");
    return Promise.resolve();
  }
}

// Step 3: Test API Key Button Click
async function testAPIKeyButton() {
  console.log("🔘 Testing API Key button...");
  
  // Wait for page to load
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Look for the API & Tokens tab first
  const apiTokensTab = document.querySelector('[value="api-tokens"]') || 
                      document.querySelector('button[role="tab"]') ||
                      document.querySelector('[data-value="api-tokens"]');
  
  if (apiTokensTab) {
    console.log("✅ Found API & Tokens tab, clicking...");
    apiTokensTab.click();
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // Look for the Create Key button
  const createButton = document.querySelector('[data-testid="create-api-key-button"]') ||
                      document.querySelector('button:contains("Create Key")') ||
                      document.querySelector('button[class*="create"]') ||
                      Array.from(document.querySelectorAll('button')).find(btn => 
                        btn.textContent.includes('Create') && btn.textContent.includes('Key')
                      );
  
  if (createButton) {
    console.log("✅ Found Create Key button:", createButton);
    console.log("📝 Button text:", createButton.textContent);
    console.log("🎨 Button classes:", createButton.className);
    
    // Test clicking the button
    console.log("🔄 Clicking Create Key button...");
    createButton.click();
    
    // Wait for modal to appear
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Check for modal
    const modal = document.querySelector('[role="dialog"]') ||
                 document.querySelector('.modal') ||
                 document.querySelector('[class*="dialog"]') ||
                 document.querySelector('[data-testid*="dialog"]');
    
    if (modal) {
      console.log("🎉 SUCCESS! Modal opened:", modal);
      console.log("📋 Modal content preview:", modal.textContent.substring(0, 200) + "...");
      
      // Look for form elements
      const nameInput = modal.querySelector('input[placeholder*="name"]') ||
                       modal.querySelector('[data-testid*="name"]') ||
                       modal.querySelector('input[type="text"]');
      
      if (nameInput) {
        console.log("✅ Found name input field in modal");
        
        // Test form interaction
        nameInput.value = "Test API Key from Browser";
        nameInput.dispatchEvent(new Event('input', { bubbles: true }));
        console.log("✅ Successfully entered text in form");
        
        return {
          success: true,
          modal: modal,
          nameInput: nameInput,
          message: "API Key creation modal is working correctly!"
        };
      } else {
        console.log("⚠️ Modal opened but no form fields found");
        return {
          success: true,
          modal: modal,
          nameInput: null,
          message: "Modal opens but form elements need investigation"
        };
      }
    } else {
      console.log("❌ Modal did not open after clicking button");
      console.log("🔍 Available elements with 'dialog' or 'modal':");
      document.querySelectorAll('[class*="dialog"], [class*="modal"], [role="dialog"]')
        .forEach((el, i) => console.log(`  ${i + 1}:`, el));
      
      return {
        success: false,
        modal: null,
        nameInput: null,
        message: "Button exists but modal does not open"
      };
    }
  } else {
    console.log("❌ Create Key button not found");
    console.log("🔍 Available buttons:");
    document.querySelectorAll('button').forEach((btn, i) => {
      console.log(`  ${i + 1}: "${btn.textContent.trim()}" - ${btn.className}`);
    });
    
    return {
      success: false,
      modal: null,
      nameInput: null,
      message: "Create Key button not found on page"
    };
  }
}

// Step 4: Complete test workflow
async function runCompleteTest() {
  console.log("🚀 Starting Complete API Key UI Test");
  console.log("=" * 50);
  
  try {
    // Step 1: Authenticate
    const sessionToken = await authenticateUser();
    if (!sessionToken) {
      console.log("💥 Authentication failed - cannot proceed");
      return { success: false, step: "authentication" };
    }
    
    // Step 2: Navigate to settings
    await navigateToSettings();
    
    // Step 3: Test API key functionality
    const result = await testAPIKeyButton();
    
    // Final report
    console.log("\n📊 FINAL TEST REPORT");
    console.log("=" * 50);
    console.log("🔐 Authentication:", sessionToken ? "✅ SUCCESS" : "❌ FAILED");
    console.log("📄 Navigation:", "✅ SUCCESS");
    console.log("🔘 Button Test:", result.success ? "✅ SUCCESS" : "❌ FAILED");
    console.log("🪟 Modal Test:", result.modal ? "✅ SUCCESS" : "❌ FAILED");
    console.log("📝 Form Test:", result.nameInput ? "✅ SUCCESS" : "❌ FAILED");
    console.log("\n💬 Summary:", result.message);
    
    if (result.success && result.modal) {
      console.log("\n🎉 OVERALL RESULT: API Key creation functionality is WORKING!");
      console.log("✅ Users can successfully:");
      console.log("   - Navigate to Settings page");
      console.log("   - Click the Create Key button");
      console.log("   - Open the API key creation modal");
      if (result.nameInput) {
        console.log("   - Interact with form fields");
      }
    } else {
      console.log("\n⚠️ OVERALL RESULT: Issues detected with API Key functionality");
      console.log("❌ Problem:", result.message);
    }
    
    return result;
    
  } catch (error) {
    console.log("💥 Test error:", error);
    return { success: false, error: error.message };
  }
}

// Make functions available globally
if (typeof window !== 'undefined') {
  window.sentinelForgeTest = {
    authenticateUser,
    navigateToSettings,
    testAPIKeyButton,
    runCompleteTest
  };
  
  console.log("✅ Test functions loaded!");
  console.log("📝 Run 'sentinelForgeTest.runCompleteTest()' to start");
}

// Auto-run if desired
// runCompleteTest();
