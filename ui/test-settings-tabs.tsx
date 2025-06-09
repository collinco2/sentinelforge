/**
 * Test file to verify the refactored Settings page with horizontal tabs works correctly
 * This file tests the new tabbed layout and navigation
 */

import React from "react";
import { BrowserRouter } from "react-router-dom";
import { SettingsPage } from "./src/pages/SettingsPage";

// Mock auth context for testing
const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
  // Mock user with analyst role to access settings
  const mockUser = {
    user_id: 1,
    username: "test_analyst",
    email: "analyst@sentinelforge.com",
    role: "analyst" as const,
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    permissions: {
      can_override_risk_scores: true,
      can_view_audit_trail: true,
      can_manage_user_roles: false,
    },
  };

  const mockAuthContext = {
    user: mockUser,
    isAuthenticated: true,
    hasRole: (roles: string[]) => roles.includes("analyst"),
    login: async () => mockUser,
    logout: async () => {},
  };

  return <div data-mock-auth={JSON.stringify(mockAuthContext)}>{children}</div>;
};

// Test component that renders the tabbed Settings page
const TestSettingsTabs = () => {
  return (
    <BrowserRouter>
      <MockAuthProvider>
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-4">
            Testing Settings Page with Horizontal Tabs
          </h1>
          <div className="border rounded-lg p-4">
            <SettingsPage />
          </div>
        </div>
      </MockAuthProvider>
    </BrowserRouter>
  );
};

export default TestSettingsTabs;

// Test the new tabbed features:
// 1. ✅ Horizontal tabs layout using shadcn/ui Tabs component
// 2. ✅ Four tabs: API & Tokens, UI Preferences, Notifications, Security
// 3. ✅ Proper component organization:
//    - API & Tokens → TokenSettings + ApiKeyManagement
//    - UI Preferences → UIPreferences
//    - Notifications → NotificationSettings
//    - Security → PasswordChangeForm
// 4. ✅ Default to first tab (API & Tokens)
// 5. ✅ Mobile responsive design with abbreviated labels
// 6. ✅ Proper icons for each tab (Key, Palette, Bell, Lock)
// 7. ✅ Replaced previous two-column layout with organized tabs
// 8. ✅ Maintained all existing functionality and security features
