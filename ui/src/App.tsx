import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute, {
  AdminRoute,
  AuditorRoute,
} from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import PasswordResetRequestPage from "./pages/PasswordResetRequestPage";
import PasswordResetPage from "./pages/PasswordResetPage";
import { Dashboard } from "./pages/Dashboard";
import { IocDetailPage } from "./pages/IocDetailPage";
import { ShareableIocView } from "./pages/ShareableIocView";
import { AlertTimelinePage } from "./pages/AlertTimelinePage";
import { AlertsPage } from "./pages/AlertsPage";
import { RoleManagementPage } from "./pages/RoleManagementPage";
import { IocManagementPage } from "./pages/IocManagementPage";
import { FeedManagementPage } from "./pages/FeedManagementPage";
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

  return (
    <div className="dark">
      <div className="min-h-screen bg-background text-foreground">
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
              <Route
                path="/share/ioc/:iocValue"
                element={<ShareableIocView />}
              />

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
                    <Dashboard />
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
              <Route
                path="/feed-management"
                element={
                  <ProtectedRoute>
                    <FeedManagementPage />
                  </ProtectedRoute>
                }
              />

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
    </div>
  );
}

export default App;
