import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { RoleManagementPanel } from "../RoleManagementPanel";
import { UserRole } from "../../services/auth";
import * as api from "../../services/api";

import { useAuth } from "../../hooks/useAuth";

// Mock dependencies
vi.mock("../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../services/api", () => ({
  getUsers: vi.fn(),
  updateUserRole: vi.fn(),
  getRoleChangeAuditLogs: vi.fn(),
}));

vi.mock("../ui/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));
const mockUseAuth = vi.mocked(useAuth);

const mockGetUsers = vi.mocked(api.getUsers);
const mockGetRoleChangeAuditLogs = vi.mocked(api.getRoleChangeAuditLogs);

const mockUsers = [
  {
    user_id: 1,
    username: "admin",
    email: "admin@test.com",
    role: "admin" as const,
    is_active: true,
    created_at: "2023-12-21T10:00:00Z",
  },
  {
    user_id: 2,
    username: "analyst1",
    email: "analyst1@test.com",
    role: "analyst" as const,
    is_active: true,
    created_at: "2023-12-21T11:00:00Z",
  },
  {
    user_id: 3,
    username: "viewer1",
    email: "viewer1@test.com",
    role: "viewer" as const,
    is_active: true,
    created_at: "2023-12-21T12:00:00Z",
  },
];

const mockAuditLogs = [
  {
    id: 1,
    alert_id: -2,
    user_id: 1,
    admin_username: "admin",
    original_score: 0,
    override_score: 0,
    justification:
      "ROLE_CHANGE: User 'analyst1' (ID: 2) role changed from 'viewer' to 'analyst' by admin 'admin' (ID: 1)",
    timestamp: "2023-12-21T13:00:00Z",
    action: "role_change",
    target_user_id: 2,
  },
];

describe("RoleManagementPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetUsers.mockResolvedValue({
      users: mockUsers,
      total: mockUsers.length,
    });
    mockGetRoleChangeAuditLogs.mockResolvedValue({
      audit_logs: mockAuditLogs,
      total: mockAuditLogs.length,
      limit: 50,
      offset: 0,
    });
  });

  it("should show access denied for non-admin users", () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 2,
        username: "analyst",
        email: "analyst@test.com",
        role: UserRole.ANALYST,
        is_active: true,
        created_at: "2023-12-21T10:00:00Z",
        permissions: {
          can_override_risk_scores: true,
          can_view_audit_trail: false,
        },
      },
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      setDemoUser: vi.fn(),
      hasRole: vi.fn(() => false),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => false),
      refreshUser: vi.fn(),
    });

    render(<RoleManagementPanel />);

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(
      screen.getByText(
        "You need administrator privileges to access role management.",
      ),
    ).toBeInTheDocument();
  });

  it("should render users table for admin users", async () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 1,
        username: "admin",
        email: "admin@test.com",
        role: UserRole.ADMIN,
        is_active: true,
        created_at: "2023-12-21T10:00:00Z",
        permissions: {
          can_override_risk_scores: true,
          can_view_audit_trail: true,
        },
      },
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      setDemoUser: vi.fn(),
      hasRole: vi.fn(() => true),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => true),
      refreshUser: vi.fn(),
    });

    render(<RoleManagementPanel />);

    await waitFor(() => {
      expect(screen.getByText("Role Management")).toBeInTheDocument();
    });

    // Check if users are displayed
    expect(screen.getByText("admin")).toBeInTheDocument();
    expect(screen.getByText("analyst1")).toBeInTheDocument();
    expect(screen.getByText("viewer1")).toBeInTheDocument();

    // Check if role badges are displayed
    expect(screen.getByText("admin")).toBeInTheDocument();
    expect(screen.getByText("analyst")).toBeInTheDocument();
    expect(screen.getByText("viewer")).toBeInTheDocument();
  });

  it("should filter users by role", async () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 1,
        username: "admin",
        email: "admin@test.com",
        role: UserRole.ADMIN,
        is_active: true,
        created_at: "2023-12-21T10:00:00Z",
        permissions: {
          can_override_risk_scores: true,
          can_view_audit_trail: true,
        },
      },
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      setDemoUser: vi.fn(),
      hasRole: vi.fn(() => true),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => true),
      refreshUser: vi.fn(),
    });

    render(<RoleManagementPanel />);

    await waitFor(() => {
      expect(screen.getByText("Role Management")).toBeInTheDocument();
    });

    // Find and click the role filter dropdown
    const filterSelect = screen.getByDisplayValue("All Roles");
    fireEvent.click(filterSelect);

    // Select "analyst" filter
    const analystOption = screen.getByText("Analyst");
    fireEvent.click(analystOption);

    // Should show only analyst users
    await waitFor(() => {
      expect(screen.getByText("analyst1")).toBeInTheDocument();
    });
    expect(screen.queryByText("viewer1")).not.toBeInTheDocument();
  });

  it("should show confirmation dialog when changing roles", async () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 1,
        username: "admin",
        email: "admin@test.com",
        role: UserRole.ADMIN,
        is_active: true,
        created_at: "2023-12-21T10:00:00Z",
        permissions: {
          can_override_risk_scores: true,
          can_view_audit_trail: true,
        },
      },
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      setDemoUser: vi.fn(),
      hasRole: vi.fn(() => true),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => true),
      refreshUser: vi.fn(),
    });

    render(<RoleManagementPanel />);

    await waitFor(() => {
      expect(screen.getByText("Role Management")).toBeInTheDocument();
    });

    // Find the role dropdown for analyst1 and change it
    const roleSelects = screen.getAllByDisplayValue("analyst");
    fireEvent.click(roleSelects[0]);

    const auditorOption = screen.getByText("Auditor");
    fireEvent.click(auditorOption);

    // Should show confirmation dialog
    await waitFor(() => {
      expect(screen.getByText("Confirm Role Change")).toBeInTheDocument();
    });
    expect(screen.getByText(/analyst1.*auditor/)).toBeInTheDocument();
  });

  it("should prevent admin from demoting themselves", async () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 1,
        username: "admin",
        email: "admin@test.com",
        role: UserRole.ADMIN,
        is_active: true,
        created_at: "2023-12-21T10:00:00Z",
        permissions: {
          can_override_risk_scores: true,
          can_view_audit_trail: true,
        },
      },
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      setDemoUser: vi.fn(),
      hasRole: vi.fn(() => true),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => true),
      refreshUser: vi.fn(),
    });

    render(<RoleManagementPanel />);

    await waitFor(() => {
      expect(screen.getByText("Role Management")).toBeInTheDocument();
    });

    // Find the role dropdown for admin (current user) and try to change it
    const adminRoleSelects = screen.getAllByDisplayValue("admin");
    fireEvent.click(adminRoleSelects[0]);

    const viewerOption = screen.getByText("Viewer");
    fireEvent.click(viewerOption);

    // Should show error message instead of confirmation dialog
    await waitFor(() => {
      expect(screen.queryByText("Confirm Role Change")).not.toBeInTheDocument();
    });
  });

  it("should show audit trail when toggled", async () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 1,
        username: "admin",
        email: "admin@test.com",
        role: UserRole.ADMIN,
        is_active: true,
        created_at: "2023-12-21T10:00:00Z",
        permissions: {
          can_override_risk_scores: true,
          can_view_audit_trail: true,
        },
      },
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      setDemoUser: vi.fn(),
      hasRole: vi.fn(() => true),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => true),
      refreshUser: vi.fn(),
    });

    render(<RoleManagementPanel />);

    await waitFor(() => {
      expect(screen.getByText("Role Management")).toBeInTheDocument();
    });

    // Click the "Show Audit Trail" button
    const auditButton = screen.getByText("Show Audit Trail");
    fireEvent.click(auditButton);

    // Should show audit trail
    await waitFor(() => {
      expect(screen.getByText("Role Change Audit Trail")).toBeInTheDocument();
    });
    expect(screen.getByText("admin")).toBeInTheDocument(); // admin username in audit log
  });
});
