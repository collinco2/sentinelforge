/**
 * 🛡️ AuthContext - Global Authentication State Management
 *
 * Provides authentication state and methods throughout the application:
 * - User authentication status
 * - Current user information and role
 * - Login/logout functionality
 * - Session persistence and restoration
 * - Role-based permission checking
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { User, UserRole } from "../services/auth";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  hasRole: (requiredRoles: UserRole[]) => boolean;
  canOverrideRiskScores: () => boolean;
  canViewAuditTrail: () => boolean;
  canManageUserRoles: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize authentication state
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check for existing session
      const response = await fetch("/api/session", {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const sessionData = await response.json();
        if (sessionData.authenticated && sessionData.user) {
          setUser(sessionData.user);
          // Store session token for API requests
          if (sessionData.session_token) {
            localStorage.setItem("session_token", sessionData.session_token);
          }
        } else {
          setUser(null);
          localStorage.removeItem("session_token");
        }
      } else {
        setUser(null);
        localStorage.removeItem("session_token");
      }
    } catch (err) {
      console.error("Failed to initialize auth:", err);
      setError("Failed to initialize authentication");
      setUser(null);
      localStorage.removeItem("session_token");
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (
    username: string,
    password: string,
  ): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);

        // Store session token for API requests
        if (data.session_token) {
          localStorage.setItem("session_token", data.session_token);
        }

        return true;
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Login failed");
        return false;
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("Network error during login");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);

    try {
      // Get session token for logout request
      const sessionToken = localStorage.getItem("session_token");

      await fetch("/api/logout", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(sessionToken && { "X-Session-Token": sessionToken }),
        },
      });
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      // Always clear local state regardless of API response
      setUser(null);
      setError(null);
      localStorage.removeItem("session_token");
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const sessionToken = localStorage.getItem("session_token");
      const response = await fetch("/api/session", {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(sessionToken && { "X-Session-Token": sessionToken }),
        },
      });

      if (response.ok) {
        const sessionData = await response.json();
        if (sessionData.authenticated && sessionData.user) {
          setUser(sessionData.user);
        } else {
          setUser(null);
          localStorage.removeItem("session_token");
        }
      } else {
        setUser(null);
        localStorage.removeItem("session_token");
      }
    } catch (err) {
      console.error("Failed to refresh user:", err);
      setError("Failed to refresh user information");
    } finally {
      setIsLoading(false);
    }
  };

  // Permission checking methods
  const hasRole = (requiredRoles: UserRole[]): boolean => {
    if (!user) return false;
    return requiredRoles.includes(user.role);
  };

  const canOverrideRiskScores = (): boolean => {
    return hasRole([UserRole.ANALYST, UserRole.ADMIN]);
  };

  const canViewAuditTrail = (): boolean => {
    return hasRole([UserRole.AUDITOR, UserRole.ADMIN]);
  };

  const canManageUserRoles = (): boolean => {
    return hasRole([UserRole.ADMIN]);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    logout,
    refreshUser,
    hasRole,
    canOverrideRiskScores,
    canViewAuditTrail,
    canManageUserRoles,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
}

// Export for backward compatibility with existing useAuth hook
export { AuthProvider as default };
