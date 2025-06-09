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

import React, { useState } from "react";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageHeader, BREADCRUMB_CONFIGS } from "../components/PageHeader";
import { TokenSettings } from "../components/settings/TokenSettings";
import { UIPreferences } from "../components/settings/UIPreferences";
import { NotificationSettings } from "../components/settings/NotificationSettings";
import { ApiKeyManagement } from "../components/settings/ApiKeyManagement";
import { PasswordChangeForm } from "../components/settings/PasswordChangeForm";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { Alert, AlertDescription } from "../components/ui/alert";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { Shield, AlertCircle, Key, Palette, Bell, Lock } from "lucide-react";

export const SettingsPage: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState("api-tokens");

  // Check if user has required permissions
  const canAccessSettings = hasRole([
    UserRole.ANALYST,
    UserRole.AUDITOR,
    UserRole.ADMIN,
  ]);

  // Get breadcrumbs based on active tab
  const getBreadcrumbs = () => {
    const tabBreadcrumbs: Record<
      string,
      Array<{ label: string; href?: string }>
    > = {
      "api-tokens": BREADCRUMB_CONFIGS.SETTINGS_API_TOKENS,
      "ui-preferences": BREADCRUMB_CONFIGS.SETTINGS_UI_PREFERENCES,
      notifications: BREADCRUMB_CONFIGS.SETTINGS_NOTIFICATIONS,
      security: BREADCRUMB_CONFIGS.SETTINGS_SECURITY,
    };

    return tabBreadcrumbs[activeTab] || BREADCRUMB_CONFIGS.SETTINGS_API_TOKENS;
  };

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
        {/* Page Header with Breadcrumbs */}
        <PageHeader
          title="Settings"
          description="Manage your account preferences, security settings, and API access"
          breadcrumbs={getBreadcrumbs()}
          icon={Shield}
        />

        {/* User Info Banner */}
        {user && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start sm:items-center gap-3">
              <div className="h-12 w-12 sm:h-10 sm:w-10 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-medium text-lg sm:text-base">
                  {user.username.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-blue-900 dark:text-blue-100 text-base sm:text-sm">
                  {user.username}
                </p>
                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 text-sm text-blue-700 dark:text-blue-300">
                  <span className="truncate">{user.email}</span>
                  <span className="hidden sm:inline">•</span>
                  <span className="text-xs sm:text-sm">
                    {user.role.charAt(0).toUpperCase() + user.role.slice(1)}{" "}
                    Role
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Settings Tabs */}
        <Tabs
          defaultValue="api-tokens"
          className="w-full"
          onValueChange={setActiveTab}
        >
          <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 bg-muted">
            <TabsTrigger
              value="api-tokens"
              className="flex items-center gap-2 data-[state=active]:bg-background data-[state=active]:text-foreground"
              aria-label="API Keys and Tokens settings"
            >
              <Key className="h-4 w-4" />
              <span className="hidden sm:inline">API & Tokens</span>
              <span className="sm:hidden">API</span>
              <span className="sr-only">API Keys and Tokens settings</span>
            </TabsTrigger>
            <TabsTrigger
              value="ui-preferences"
              className="flex items-center gap-2 data-[state=active]:bg-background data-[state=active]:text-foreground"
              aria-label="User Interface Preferences settings"
            >
              <Palette className="h-4 w-4" />
              <span className="hidden sm:inline">UI Preferences</span>
              <span className="sm:hidden">UI</span>
              <span className="sr-only">
                User Interface Preferences settings
              </span>
            </TabsTrigger>
            <TabsTrigger
              value="notifications"
              className="flex items-center gap-2 data-[state=active]:bg-background data-[state=active]:text-foreground"
              aria-label="Notification and Alert settings"
            >
              <Bell className="h-4 w-4" />
              <span className="hidden sm:inline">Notifications</span>
              <span className="sm:hidden">Alerts</span>
              <span className="sr-only">Notification and Alert settings</span>
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className="flex items-center gap-2 data-[state=active]:bg-background data-[state=active]:text-foreground"
              aria-label="Security and Password settings"
            >
              <Lock className="h-4 w-4" />
              <span className="hidden sm:inline">Security</span>
              <span className="sm:hidden">Security</span>
              <span className="sr-only">Security and Password settings</span>
            </TabsTrigger>
          </TabsList>

          {/* API & Tokens Tab */}
          <TabsContent value="api-tokens" className="mt-6">
            <div className="space-y-6 lg:grid lg:grid-cols-2 lg:gap-6 lg:space-y-0">
              <div className="space-y-6">
                <TokenSettings />
              </div>
              <div className="space-y-6">
                <ApiKeyManagement />
              </div>
            </div>
          </TabsContent>

          {/* UI Preferences Tab */}
          <TabsContent value="ui-preferences" className="mt-6">
            <div className="max-w-2xl">
              <UIPreferences />
            </div>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="mt-6">
            <div className="max-w-2xl">
              <NotificationSettings />
            </div>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="mt-6">
            <div className="max-w-2xl">
              <PasswordChangeForm />
            </div>
          </TabsContent>
        </Tabs>

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
