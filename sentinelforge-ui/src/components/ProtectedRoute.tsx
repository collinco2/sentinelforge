/**
 * 🛡️ ProtectedRoute Component - Role-Based Route Protection
 *
 * Higher-order component that enforces authentication and role-based access control:
 * - Redirects unauthenticated users to login page
 * - Shows 403 error for insufficient permissions
 * - Supports multiple required roles
 * - Provides loading states during authentication checks
 */

import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuthContext } from "../contexts/AuthContext";
import { UserRole } from "../services/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Alert, AlertDescription } from "./ui/alert";
import { Shield, Lock, ArrowLeft, Home } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: UserRole[];
  fallbackPath?: string;
}

export default function ProtectedRoute({
  children,
  requiredRoles = [],
  fallbackPath = "/login",
}: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading, hasRole } = useAuthContext();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
          <p className="text-slate-400">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // Check role-based permissions
  if (requiredRoles.length > 0 && !hasRole(requiredRoles)) {
    return (
      <AccessDeniedPage requiredRoles={requiredRoles} userRole={user?.role} />
    );
  }

  // Render protected content
  return <>{children}</>;
}

interface AccessDeniedPageProps {
  requiredRoles: UserRole[];
  userRole?: UserRole;
}

function AccessDeniedPage({ requiredRoles, userRole }: AccessDeniedPageProps) {
  const getRoleDisplayName = (role: UserRole): string => {
    const roleNames = {
      [UserRole.VIEWER]: "Viewer",
      [UserRole.ANALYST]: "Analyst",
      [UserRole.AUDITOR]: "Auditor",
      [UserRole.ADMIN]: "Administrator",
    };
    return roleNames[role] || role;
  };

  const getRoleColor = (role: UserRole): string => {
    const roleColors = {
      [UserRole.VIEWER]: "bg-gray-500",
      [UserRole.ANALYST]: "bg-blue-500",
      [UserRole.AUDITOR]: "bg-purple-500",
      [UserRole.ADMIN]: "bg-red-500",
    };
    return roleColors[role] || "bg-gray-500";
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="w-full max-w-md">
        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center">
              <Lock className="h-8 w-8 text-red-400" />
            </div>
            <div>
              <CardTitle className="text-2xl text-white">
                Access Denied
              </CardTitle>
              <CardDescription className="text-slate-400 mt-2">
                You don't have permission to access this page
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Current Role */}
            <div className="text-center space-y-2">
              <p className="text-sm text-slate-400">Your current role:</p>
              {userRole && (
                <div className="inline-flex items-center space-x-2">
                  <div
                    className={`w-3 h-3 rounded-full ${getRoleColor(userRole)}`}
                  ></div>
                  <span className="text-white font-medium">
                    {getRoleDisplayName(userRole)}
                  </span>
                </div>
              )}
            </div>

            {/* Required Roles */}
            <div className="space-y-3">
              <Alert className="border-amber-500/50 bg-amber-500/10">
                <Shield className="h-4 w-4 text-amber-400" />
                <AlertDescription className="text-amber-200">
                  <div className="space-y-2">
                    <p className="font-medium">Required permissions:</p>
                    <div className="flex flex-wrap gap-2">
                      {requiredRoles.map((role) => (
                        <span
                          key={role}
                          className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium text-white ${getRoleColor(role)}`}
                        >
                          <div className="w-2 h-2 rounded-full bg-white/30"></div>
                          <span>{getRoleDisplayName(role)}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <Button
                onClick={() => window.history.back()}
                variant="outline"
                className="w-full border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Go Back
              </Button>

              <Button
                onClick={() => (window.location.href = "/dashboard")}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white"
              >
                <Home className="mr-2 h-4 w-4" />
                Return to Dashboard
              </Button>
            </div>

            {/* Contact Info */}
            <div className="text-center text-sm text-slate-400 space-y-1">
              <p>Need access to this feature?</p>
              <p>Contact your administrator to request role permissions.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Convenience wrapper for specific role requirements
export function AdminRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRoles={[UserRole.ADMIN]}>{children}</ProtectedRoute>
  );
}

export function AnalystRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRoles={[UserRole.ANALYST, UserRole.ADMIN]}>
      {children}
    </ProtectedRoute>
  );
}

export function AuditorRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRoles={[UserRole.AUDITOR, UserRole.ADMIN]}>
      {children}
    </ProtectedRoute>
  );
}
