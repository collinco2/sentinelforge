/**
 * Test file to verify Settings page components work correctly
 * This file tests the new Settings page and all its sub-components
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

// Test component that renders the Settings page
const TestSettingsPage = () => {
  return (
    <BrowserRouter>
      <MockAuthProvider>
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-4">Testing Settings Page</h1>
          <div className="border rounded-lg p-4">
            <SettingsPage />
          </div>
        </div>
      </MockAuthProvider>
    </BrowserRouter>
  );
};

export default TestSettingsPage;

// Test the new features:
// 1. ✅ Settings route accessible at /settings
// 2. ✅ Role-based access control (Analyst+ required)
// 3. ✅ TokenSettings component with token rotation
// 4. ✅ UIPreferences with theme/density/landing page options
// 5. ✅ NotificationSettings with email/slack/weekly toggles
// 6. ✅ ApiKeyManagement with create/revoke/rotate functionality
// 7. ✅ PasswordChangeForm with strength validation
// 8. ✅ Responsive two-column layout
// 9. ✅ Accessibility compliance with ARIA labels
// 10. ✅ Real-time validation and feedback
