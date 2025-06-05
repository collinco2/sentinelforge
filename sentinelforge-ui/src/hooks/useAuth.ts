/**
 * 🛡️ useAuth Hook - React Authentication and RBAC Hook
 *
 * This hook provides authentication state and role-based access control
 * functionality for React components.
 */

import { useState, useEffect, useCallback } from "react";
import { authService, User, UserRole } from "../services/auth";

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

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load current user from auth service
   */
  const loadUser = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load user");
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Login with username and password
   */
  const login = useCallback(
    async (username: string, password: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await authService.login(username, password);

        if ("error" in result) {
          setError(result.message);
          setUser(null);
          return false;
        } else {
          setUser(result);
          return true;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed");
        setUser(null);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  /**
   * Logout current user
   */
  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    setError(null);
  }, []);

  /**
   * Set demo user for testing
   */
  const setDemoUser = useCallback(
    async (userId: number) => {
      setIsLoading(true);
      setError(null);

      try {
        authService.setDemoUser(userId);
        await loadUser();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to set demo user",
        );
      }
    },
    [loadUser],
  );

  /**
   * Check if user has required roles
   */
  const hasRole = useCallback((requiredRoles: UserRole[]): boolean => {
    return authService.hasRole(requiredRoles);
  }, []);

  /**
   * Check if user can override risk scores
   */
  const canOverrideRiskScores = useCallback((): boolean => {
    return authService.canOverrideRiskScores();
  }, []);

  /**
   * Check if user can view audit trail
   */
  const canViewAuditTrail = useCallback((): boolean => {
    return authService.canViewAuditTrail();
  }, []);

  /**
   * Refresh user data
   */
  const refreshUser = useCallback(async (): Promise<void> => {
    await loadUser();
  }, [loadUser]);

  // Load user on mount
  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return {
    user,
    isLoading,
    isAuthenticated: user !== null,
    error,
    login,
    logout,
    setDemoUser,
    hasRole,
    canOverrideRiskScores,
    canViewAuditTrail,
    refreshUser,
  };
}
