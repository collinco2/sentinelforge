import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute, {
  AdminRoute,
  AuditorRoute,
} from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import PasswordResetRequestPage from "./pages/PasswordResetRequestPage";
import PasswordResetPage from "./pages/PasswordResetPage";

import { IocDetailPage } from "./pages/IocDetailPage";
import { ShareableIocView } from "./pages/ShareableIocView";
import { AlertTimelinePage } from "./pages/AlertTimelinePage";
import { AlertsPage } from "./pages/AlertsPage";
import { RoleManagementPage } from "./pages/RoleManagementPage";
import { SettingsPage } from "./pages/SettingsPage";
import { IocManagementPage } from "./pages/IocManagementPage";
import { FeedManagementPage } from "./pages/FeedManagementPage";
import { FeedUploadPage } from "./pages/FeedUploadPage";
import { FeedHealthPage } from "./pages/FeedHealthPage";
import { ButtonAccessibilityTest } from "./components/ButtonAccessibilityTest";
import { DarkModeTest } from "./components/DarkModeTest";
import { DashboardOverview } from "./pages/DashboardOverview";
import { ThreatDashboard } from "./pages/ThreatDashboard";
import { ThreatMonitorPage } from "./pages/ThreatMonitorPage";
import "./App.css";

function App() {
  // Log server type for debugging
  React.useEffect(() => {
    const isDev = process.env.NODE_ENV === "development";
    const serverType = isDev
      ? "DEVELOPMENT (npm start)"
      : "PRODUCTION (spa-server.py)";
    console.log(`🚀 SentinelForge UI Server: ${serverType}`);
    console.log(`📍 Environment: ${process.env.NODE_ENV}`);
    console.log(`🌐 URL: ${window.location.origin}`);
  }, []);

  // Initialize theme on app load
  useEffect(() => {
    const initializeTheme = () => {
      const savedTheme = localStorage.getItem("ui-preferences");
      let theme = "system";

      if (savedTheme) {
        try {
          const preferences = JSON.parse(savedTheme);
          theme = preferences.theme || "system";
        } catch (error) {
          console.warn("Failed to parse saved theme preferences:", error);
        }
      }

      applyTheme(theme);
    };

    const applyTheme = (theme: string) => {
      const root = document.documentElement;
      root.classList.remove("dark");

      if (theme === "dark") {
        root.classList.add("dark");
      } else if (theme === "light") {
        // Light mode is default, no class needed
      } else {
        // System theme
        const prefersDark = window.matchMedia(
          "(prefers-color-scheme: dark)",
        ).matches;
        if (prefersDark) {
          root.classList.add("dark");
        }
      }
    };

    initializeTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleSystemThemeChange = () => {
      const savedTheme = localStorage.getItem("ui-preferences");
      if (savedTheme) {
        try {
          const preferences = JSON.parse(savedTheme);
          if (preferences.theme === "system") {
            applyTheme("system");
          }
        } catch (error) {
          console.warn("Failed to parse saved theme preferences:", error);
        }
      }
    };

    mediaQuery.addEventListener("change", handleSystemThemeChange);
    return () =>
      mediaQuery.removeEventListener("change", handleSystemThemeChange);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/forgot-password"
              element={<PasswordResetRequestPage />}
            />
            <Route path="/reset-password" element={<PasswordResetPage />} />
            <Route path="/share/ioc/:iocValue" element={<ShareableIocView />} />

            {/* Protected routes - require authentication */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardOverview />
                </ProtectedRoute>
              }
            />
            <Route
              path="/threat-dashboard"
              element={
                <ProtectedRoute>
                  <ThreatDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/threat-monitor"
              element={
                <ProtectedRoute>
                  <ThreatMonitorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/threat-intel/:iocId"
              element={
                <ProtectedRoute>
                  <IocDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ioc/:iocId"
              element={
                <ProtectedRoute>
                  <IocDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/alerts"
              element={
                <ProtectedRoute>
                  <AlertsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/alerts/timeline"
              element={
                <AuditorRoute>
                  <AlertTimelinePage />
                </AuditorRoute>
              }
            />
            <Route
              path="/ioc-management"
              element={
                <ProtectedRoute>
                  <IocManagementPage />
                </ProtectedRoute>
              }
            />
            {/* Feed routes - /feeds redirects to main feed management */}
            <Route
              path="/feeds"
              element={
                <ProtectedRoute>
                  <Navigate to="/feed-management" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/feed-management"
              element={
                <ProtectedRoute>
                  <FeedManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/feed-upload"
              element={
                <ProtectedRoute>
                  <FeedUploadPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/feed-health"
              element={
                <ProtectedRoute>
                  <FeedHealthPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />

            {/* Development/Testing routes */}
            <Route path="/button-test" element={<ButtonAccessibilityTest />} />
            <Route path="/dark-mode-test" element={<DarkModeTest />} />

            {/* Admin-only routes */}
            <Route
              path="/role-management"
              element={
                <AdminRoute>
                  <RoleManagementPage />
                </AdminRoute>
              }
            />

            {/* Fallback route */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
