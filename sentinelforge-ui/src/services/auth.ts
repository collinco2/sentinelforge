/**
 * 🛡️ SentinelForge Authentication and RBAC Service
 *
 * This service handles user authentication, role-based access control,
 * and permission checking for the SentinelForge React UI.
 */

export enum UserRole {
  VIEWER = "viewer",
  ANALYST = "analyst",
  AUDITOR = "auditor",
  ADMIN = "admin",
}

export interface User {
  user_id: number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  permissions: {
    can_override_risk_scores: boolean;
    can_view_audit_trail: boolean;
  };
}

export interface AuthError {
  error: string;
  message: string;
  user_role?: string;
}

class AuthService {
  private currentUser: User | null = null;
  private authToken: string | null = null;

  constructor() {
    // Try to restore auth from localStorage
    this.restoreAuth();
  }

  /**
   * Set demo user for testing purposes
   */
  setDemoUser(userId: number): void {
    this.authToken = `demo-${userId}`;
    localStorage.setItem("auth_token", this.authToken);
    localStorage.setItem("demo_user_id", userId.toString());
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    if (this.currentUser) {
      return this.currentUser;
    }

    try {
      const response = await fetch("/api/user/current", {
        headers: this.getAuthHeaders(),
      });

      if (response.ok) {
        this.currentUser = await response.json();
        return this.currentUser;
      } else if (response.status === 401) {
        this.logout();
        return null;
      } else {
        console.error("Failed to get current user:", response.statusText);
        return null;
      }
    } catch (error) {
      console.error("Error getting current user:", error);
      return null;
    }
  }

  /**
   * Check if user has any of the required roles
   */
  hasRole(requiredRoles: UserRole[]): boolean {
    if (!this.currentUser) {
      return false;
    }
    return requiredRoles.includes(this.currentUser.role);
  }

  /**
   * Check if user can override risk scores
   */
  canOverrideRiskScores(): boolean {
    return this.currentUser?.permissions?.can_override_risk_scores ?? false;
  }

  /**
   * Check if user can view audit trail
   */
  canViewAuditTrail(): boolean {
    return this.currentUser?.permissions?.can_view_audit_trail ?? false;
  }

  /**
   * Get role display name
   */
  getRoleDisplayName(role: UserRole): string {
    const roleNames = {
      [UserRole.VIEWER]: "Viewer",
      [UserRole.ANALYST]: "Analyst",
      [UserRole.AUDITOR]: "Auditor",
      [UserRole.ADMIN]: "Administrator",
    };
    return roleNames[role] || role;
  }

  /**
   * Get role color for UI display
   */
  getRoleColor(role: UserRole): string {
    const roleColors = {
      [UserRole.VIEWER]: "bg-gray-500",
      [UserRole.ANALYST]: "bg-blue-500",
      [UserRole.AUDITOR]: "bg-purple-500",
      [UserRole.ADMIN]: "bg-red-500",
    };
    return roleColors[role] || "bg-gray-500";
  }

  /**
   * Get authentication headers for API requests
   */
  getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Add demo user header for testing
    const demoUserId = localStorage.getItem("demo_user_id");
    if (demoUserId) {
      headers["X-Demo-User-ID"] = demoUserId;
    }

    // Add session token if available
    if (this.authToken) {
      headers["X-Session-Token"] = this.authToken;
    }

    return headers;
  }

  /**
   * Login with username and password
   */
  async login(username: string, password: string): Promise<User | AuthError> {
    try {
      const credentials = btoa(`${username}:${password}`);
      const response = await fetch("/api/user/current", {
        headers: {
          Authorization: `Basic ${credentials}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const user = await response.json();
        this.currentUser = user;
        this.authToken = credentials;
        this.saveAuth();
        return user;
      } else {
        const error = await response.json();
        return error as AuthError;
      }
    } catch (error) {
      return {
        error: "Network Error",
        message: "Failed to connect to authentication server",
      };
    }
  }

  /**
   * Logout current user
   */
  logout(): void {
    this.currentUser = null;
    this.authToken = null;
    localStorage.removeItem("auth_token");
    localStorage.removeItem("demo_user_id");
    localStorage.removeItem("current_user");
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.currentUser !== null || this.authToken !== null;
  }

  /**
   * Save authentication state to localStorage
   */
  private saveAuth(): void {
    if (this.authToken) {
      localStorage.setItem("auth_token", this.authToken);
    }
    if (this.currentUser) {
      localStorage.setItem("current_user", JSON.stringify(this.currentUser));
    }
  }

  /**
   * Restore authentication state from localStorage
   */
  private restoreAuth(): void {
    this.authToken = localStorage.getItem("auth_token");
    const savedUser = localStorage.getItem("current_user");
    if (savedUser) {
      try {
        this.currentUser = JSON.parse(savedUser);
      } catch (error) {
        console.error("Failed to parse saved user:", error);
        localStorage.removeItem("current_user");
      }
    }
  }

  /**
   * Handle API response errors related to authentication
   */
  handleApiError(response: Response): boolean {
    if (response.status === 401) {
      this.logout();
      return true;
    }
    return false;
  }

  /**
   * Create demo users for testing
   */
  getDemoUsers(): Array<{ id: number; username: string; role: UserRole }> {
    return [
      { id: 1, username: "admin", role: UserRole.ADMIN },
      { id: 2, username: "analyst", role: UserRole.ANALYST },
      { id: 3, username: "auditor", role: UserRole.AUDITOR },
      { id: 4, username: "viewer", role: UserRole.VIEWER },
    ];
  }
}

// Export singleton instance
export const authService = new AuthService();

// Export utility functions
export const hasRole = (requiredRoles: UserRole[]) =>
  authService.hasRole(requiredRoles);
export const canOverrideRiskScores = () => authService.canOverrideRiskScores();
export const canViewAuditTrail = () => authService.canViewAuditTrail();
export const getCurrentUser = () => authService.getCurrentUser();
export const getAuthHeaders = () => authService.getAuthHeaders();
