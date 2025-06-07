/**
 * 🛡️ useAuth Hook - React Authentication and RBAC Hook
 *
 * This hook provides authentication state and role-based access control
 * functionality for React components. Now uses AuthContext for global state.
 */

import { useAuthContext } from "../contexts/AuthContext";
import { User, UserRole } from "../services/auth";

interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  setDemoUser: (userId: number) => void;
  hasRole: (requiredRoles: UserRole[]) => boolean;
  canOverrideRiskScores: () => boolean;
  canViewAuditTrail: () => boolean;
  refreshUser: () => Promise<void>;
}

/**
 * useAuth Hook - Wrapper around AuthContext for backward compatibility
 *
 * This hook provides the same interface as before but now uses the global
 * AuthContext for state management. This ensures consistency across the app.
 */
export function useAuth(): UseAuthReturn {
  const authContext = useAuthContext();

  // Legacy setDemoUser method for backward compatibility
  const setDemoUser = async (userId: number) => {
    // For demo purposes, we'll use the existing demo login functionality
    const demoCredentials = {
      1: { username: "admin", password: "admin123" },
      2: { username: "analyst", password: "analyst123" },
      3: { username: "auditor", password: "auditor123" },
      4: { username: "viewer", password: "viewer123" },
    };

    const credentials = demoCredentials[userId as keyof typeof demoCredentials];
    if (credentials) {
      await authContext.login(credentials.username, credentials.password);
    }
  };

  return {
    user: authContext.user,
    isLoading: authContext.isLoading,
    isAuthenticated: authContext.isAuthenticated,
    error: authContext.error,
    login: authContext.login,
    logout: authContext.logout,
    setDemoUser,
    hasRole: authContext.hasRole,
    canOverrideRiskScores: authContext.canOverrideRiskScores,
    canViewAuditTrail: authContext.canViewAuditTrail,
    refreshUser: authContext.refreshUser,
  };
}
