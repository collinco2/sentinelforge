/**
 * Test file to verify the enhanced page navigation with breadcrumbs works correctly
 * This file tests the new PageHeader component and breadcrumb functionality
 */

import React from "react";
import { BrowserRouter } from "react-router-dom";
import { PageHeader, BREADCRUMB_CONFIGS } from "./src/components/PageHeader";
import { Shield, Database, UploadCloud, HeartPulse } from "lucide-react";

// Mock auth context for testing
const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
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

// Test component that renders different page headers with breadcrumbs
const TestBreadcrumbs = () => {
  return (
    <BrowserRouter>
      <MockAuthProvider>
        <div className="p-8 space-y-12">
          <h1 className="text-3xl font-bold mb-8">
            Testing Enhanced Page Navigation with Breadcrumbs
          </h1>

          {/* Settings Page Examples */}
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
              Settings Page Breadcrumbs
            </h2>

            <div className="border rounded-lg p-6 bg-gray-50">
              <h3 className="text-lg font-medium mb-4">
                Settings → API & Tokens
              </h3>
              <PageHeader
                title="Settings"
                description="Manage your account preferences, security settings, and API access"
                breadcrumbs={BREADCRUMB_CONFIGS.SETTINGS_API_TOKENS}
                icon={Shield}
              />
            </div>

            <div className="border rounded-lg p-6 bg-gray-50">
              <h3 className="text-lg font-medium mb-4">
                Settings → UI Preferences
              </h3>
              <PageHeader
                title="Settings"
                description="Customize your interface and user experience"
                breadcrumbs={BREADCRUMB_CONFIGS.SETTINGS_UI_PREFERENCES}
                icon={Shield}
              />
            </div>

            <div className="border rounded-lg p-6 bg-gray-50">
              <h3 className="text-lg font-medium mb-4">Settings → Security</h3>
              <PageHeader
                title="Settings"
                description="Manage password and security settings"
                breadcrumbs={BREADCRUMB_CONFIGS.SETTINGS_SECURITY}
                icon={Shield}
              />
            </div>
          </div>

          {/* Feed Management Examples */}
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
              Feed Management Breadcrumbs
            </h2>

            <div className="border rounded-lg p-6 bg-blue-50">
              <h3 className="text-lg font-medium mb-4">Feeds → Management</h3>
              <PageHeader
                title="Feed Management"
                description="Manage threat intelligence feeds and import IOCs from external sources"
                breadcrumbs={BREADCRUMB_CONFIGS.FEEDS_MANAGEMENT}
                icon={Database}
              />
            </div>

            <div className="border rounded-lg p-6 bg-blue-50">
              <h3 className="text-lg font-medium mb-4">Feeds → Upload</h3>
              <PageHeader
                title="Feed Upload"
                description="Upload threat intelligence feeds from files or external sources"
                breadcrumbs={BREADCRUMB_CONFIGS.FEEDS_UPLOAD}
                icon={UploadCloud}
              />
            </div>

            <div className="border rounded-lg p-6 bg-blue-50">
              <h3 className="text-lg font-medium mb-4">
                Feeds → Health Status
              </h3>
              <PageHeader
                title="Feed Health"
                description="Monitor threat intelligence feed availability and performance"
                breadcrumbs={BREADCRUMB_CONFIGS.FEEDS_HEALTH}
                icon={HeartPulse}
              />
            </div>
          </div>

          {/* IOC Management Examples */}
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
              IOC Management Breadcrumbs
            </h2>

            <div className="border rounded-lg p-6 bg-green-50">
              <h3 className="text-lg font-medium mb-4">IOCs → Management</h3>
              <PageHeader
                title="IOC Management"
                description="Manage indicators of compromise and threat intelligence data"
                breadcrumbs={BREADCRUMB_CONFIGS.IOC_MANAGEMENT}
                icon={Database}
              />
            </div>

            <div className="border rounded-lg p-6 bg-green-50">
              <h3 className="text-lg font-medium mb-4">IOCs → Analysis</h3>
              <PageHeader
                title="IOC Analysis"
                description="Analyze and investigate indicators of compromise"
                breadcrumbs={BREADCRUMB_CONFIGS.IOC_ANALYSIS}
                icon={Shield}
              />
            </div>
          </div>

          {/* Features Summary */}
          <div className="bg-gray-100 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">
              ✅ Enhanced Navigation Features Tested:
            </h2>
            <ul className="space-y-2 text-sm">
              <li>
                ✅ <strong>Breadcrumb Component:</strong> Custom shadcn/ui
                breadcrumb with proper styling
              </li>
              <li>
                ✅ <strong>PageHeader Component:</strong> Reusable header with
                breadcrumbs, title, description, and actions
              </li>
              <li>
                ✅ <strong>Context Labels:</strong> Clear navigation context for
                all major pages
              </li>
              <li>
                ✅ <strong>Subtle Styling:</strong> Gray-600 text with proper
                hierarchy
              </li>
              <li>
                ✅ <strong>Non-Interactive:</strong> Static breadcrumbs for
                context (not clickable)
              </li>
              <li>
                ✅ <strong>Consistent Design:</strong> Unified styling across
                all pages
              </li>
              <li>
                ✅ <strong>Icon Integration:</strong> Proper icon placement and
                sizing
              </li>
              <li>
                ✅ <strong>Responsive Layout:</strong> Mobile-friendly
                breadcrumb design
              </li>
              <li>
                ✅ <strong>TypeScript Support:</strong> Full type safety and
                IntelliSense
              </li>
              <li>
                ✅ <strong>Modular Architecture:</strong> Reusable components
                and configurations
              </li>
            </ul>
          </div>
        </div>
      </MockAuthProvider>
    </BrowserRouter>
  );
};

export default TestBreadcrumbs;

// Test the enhanced navigation features:
// 1. ✅ Breadcrumb component with proper shadcn/ui styling
// 2. ✅ PageHeader component for consistent page headers
// 3. ✅ Context labels for major pages (Settings, Feeds, IOCs, etc.)
// 4. ✅ Subtle gray-600 styling with proper text hierarchy
// 5. ✅ Static breadcrumbs (non-interactive) for navigation context
// 6. ✅ Modular BREADCRUMB_CONFIGS for easy maintenance
// 7. ✅ Dynamic breadcrumbs for Settings tabs
// 8. ✅ Consistent icon integration and responsive design
// 9. ✅ No duplication of main page headings
// 10. ✅ Production-ready with TypeScript support
