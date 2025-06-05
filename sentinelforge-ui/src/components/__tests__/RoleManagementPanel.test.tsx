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

    // Check if users are displayed in table
    expect(screen.getByText("admin@test.com")).toBeInTheDocument();
    expect(screen.getByText("analyst1@test.com")).toBeInTheDocument();
    expect(screen.getByText("viewer1@test.com")).toBeInTheDocument();

    // Check if usernames are displayed (use getAllByText since usernames appear multiple times)
    const adminElements = screen.getAllByText("admin");
    const analyst1Elements = screen.getAllByText("analyst1");
    const viewer1Elements = screen.getAllByText("viewer1");

    expect(adminElements.length).toBeGreaterThan(0);
    expect(analyst1Elements.length).toBeGreaterThan(0);
    expect(viewer1Elements.length).toBeGreaterThan(0);
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

    // Initially all users should be visible
    expect(screen.getByText("admin@test.com")).toBeInTheDocument();
    expect(screen.getByText("analyst1@test.com")).toBeInTheDocument();
    expect(screen.getByText("viewer1@test.com")).toBeInTheDocument();

    // Find and click the role filter dropdown (first combobox with "All Roles" text)
    const filterSelect = screen.getByText("All Roles");
    fireEvent.click(filterSelect);

    // Select "analyst" filter
    const analystOption = screen.getByRole("option", { name: "Analyst" });
    fireEvent.click(analystOption);

    // Should show only analyst users after filter is applied
    await waitFor(
      () => {
        expect(screen.getByText("analyst1@test.com")).toBeInTheDocument();
      },
      { timeout: 2000 },
    );

    // Check the user count shows filtered results
    await waitFor(
      () => {
        expect(screen.getByText("Showing 1 of 3 users")).toBeInTheDocument();
      },
      { timeout: 1000 },
    );
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

    // Find the role dropdown for analyst1 (not the current admin user)
    // Look for the analyst1 user's row and find the role select within it
    const analyst1Row = screen.getByText("analyst1@test.com");
    // Find the role select in the same row by using a more specific selector
    const roleSelects = screen.getAllByRole("combobox");
    // The second combobox should be the analyst1's role dropdown (after the filter)
    const analyst1RoleSelect = roleSelects[2]; // Filter + admin + analyst1
    fireEvent.click(analyst1RoleSelect);

    const auditorOption = screen.getByRole("option", { name: "Auditor" });
    fireEvent.click(auditorOption);

    // Should show confirmation dialog
    await waitFor(() => {
      expect(screen.getByText("Confirm Role Change")).toBeInTheDocument();
    });
    // Check that the dialog contains the expected text (may be in separate elements)
    expect(screen.getByText("analyst1")).toBeInTheDocument();
    expect(screen.getByText("auditor")).toBeInTheDocument();
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

    // Find the role dropdown for admin (current user) in the table
    const adminRow = screen.getByText("admin@test.com");
    // Find the admin's role select (should be the first user role dropdown after filter)
    const roleSelects = screen.getAllByRole("combobox");
    const adminRoleSelect = roleSelects[1]; // Filter + admin
    fireEvent.click(adminRoleSelect);

    const viewerOption = screen.getByRole("option", { name: "Viewer" });
    fireEvent.click(viewerOption);

    // Should show error toast instead of confirmation dialog
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

    // Check for audit log content - should show admin username in audit logs
    // Just verify that the audit trail is visible and contains some content
    expect(screen.getByText("Role Change Audit Trail")).toBeInTheDocument();
    // The audit log should contain the justification text which includes admin info
    expect(screen.getByText(/ROLE_CHANGE.*admin/)).toBeInTheDocument();
  });
});
