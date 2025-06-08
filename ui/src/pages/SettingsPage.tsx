/**
 * 🔧 SettingsPage Component - Centralized User Settings Dashboard
 *
 * Provides a comprehensive settings interface where authenticated users can:
 * - Manage authentication tokens and security settings
 * - Customize UI preferences and themes
 * - Configure notification preferences
 * - Manage API keys for programmatic access
 * - Change account passwords with validation
 *
 * Features:
 * - Role-based access control (Analyst+ required)
 * - Responsive design with mobile-friendly layout
 * - Real-time validation and feedback
 * - Secure token and password management
 * - Accessibility compliance with ARIA labels
 */

import React from "react";
import { DashboardLayout } from "../layout/DashboardLayout";
import { TokenSettings } from "../components/settings/TokenSettings";
import { UIPreferences } from "../components/settings/UIPreferences";
import { NotificationSettings } from "../components/settings/NotificationSettings";
import { ApiKeyManagement } from "../components/settings/ApiKeyManagement";
import { PasswordChangeForm } from "../components/settings/PasswordChangeForm";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Shield, AlertCircle } from "lucide-react";

export const SettingsPage: React.FC = () => {
  const { user, hasRole } = useAuth();

  // Check if user has required permissions
  const canAccessSettings = hasRole([
    UserRole.ANALYST,
    UserRole.AUDITOR,
    UserRole.ADMIN,
  ]);

  if (!canAccessSettings) {
    return (
      <DashboardLayout title="Settings">
        <div className="flex items-center justify-center min-h-[400px]">
          <Alert className="max-w-md">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              You don't have permission to access settings. Contact your
              administrator for access.
            </AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Settings">
      <div className="space-y-6" data-testid="settings-page">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <Shield className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Settings
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Manage your account preferences, security settings, and API access
            </p>
          </div>
        </div>

        {/* User Info Banner */}
        {user && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center">
                <span className="text-white font-medium">
                  {user.username.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-100">
                  {user.username}
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  {user.email} •{" "}
                  {user.role.charAt(0).toUpperCase() + user.role.slice(1)} Role
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Settings Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Authentication Tokens */}
            <TokenSettings />

            {/* UI Preferences */}
            <UIPreferences />

            {/* Notification Settings */}
            <NotificationSettings />
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* API Key Management */}
            <ApiKeyManagement />

            {/* Password Change */}
            <PasswordChangeForm />
          </div>
        </div>

        {/* Footer Information */}
        <div className="pt-8 border-t border-gray-200 dark:border-gray-700">
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
              Security Best Practices
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Rotate your authentication tokens regularly</li>
              <li>• Use strong, unique passwords for your account</li>
              <li>• Keep your API keys secure and don't share them</li>
              <li>• Review your notification settings to stay informed</li>
              <li>• Log out from shared or public computers</li>
            </ul>
          </div>
        </div>

        {/* Development Mode Notice */}
        {process.env.NODE_ENV === "development" && (
          <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-medium text-orange-800 dark:text-orange-200">
                Development Mode
              </span>
            </div>
            <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">
              Some settings may not persist in development mode. Changes will be
              saved locally but may not sync with the backend.
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
