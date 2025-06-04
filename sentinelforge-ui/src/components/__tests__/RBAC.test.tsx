/**
 * 🛡️ RBAC React Component Tests
 *
 * This test suite validates the Role-Based Access Control (RBAC) implementation
 * in React components, ensuring proper UI restrictions based on user roles.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AlertDetailModal } from "../AlertDetailModal";
import { UserRoleSelector } from "../UserRoleSelector";
import { UserRole } from "../../services/auth";

import { useAuth } from "../../hooks/useAuth";
import { overrideAlertRiskScore } from "../../services/api";

// Mock dependencies
jest.mock("../../hooks/useAuth", () => ({
  useAuth: jest.fn(),
}));

jest.mock("../../services/api", () => ({
  overrideAlertRiskScore: jest.fn(),
  fetchAuditLogs: jest.fn(),
  getAuthHeaders: jest.fn(() => ({})),
}));

jest.mock("../../components/ui/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockOverrideAlertRiskScore =
  overrideAlertRiskScore as jest.MockedFunction<typeof overrideAlertRiskScore>;

// Mock alert data
const mockAlert = {
  id: 1,
  name: "Test Alert",
  description: "Test alert description",
  severity: "high",
  confidence: 85,
  risk_score: 75,
  overridden_risk_score: null,
  threat_type: "malware",
  source: "test-source",
  timestamp: 1640995200,
  formatted_time: "2022-01-01 00:00:00",
};

// Test user configurations
const testUsers = {
  admin: {
    user_id: 1,
    username: "admin",
    email: "admin@test.com",
    role: UserRole.ADMIN,
    is_active: true,
    created_at: "2024-01-01",
    permissions: {
      can_override_risk_scores: true,
      can_view_audit_trail: true,
    },
  },
  analyst: {
    user_id: 2,
    username: "analyst",
    email: "analyst@test.com",
    role: UserRole.ANALYST,
    is_active: true,
    created_at: "2024-01-01",
    permissions: {
      can_override_risk_scores: true,
      can_view_audit_trail: false,
    },
  },
  auditor: {
    user_id: 3,
    username: "auditor",
    email: "auditor@test.com",
    role: UserRole.AUDITOR,
    is_active: true,
    created_at: "2024-01-01",
    permissions: {
      can_override_risk_scores: false,
      can_view_audit_trail: true,
    },
  },
  viewer: {
    user_id: 4,
    username: "viewer",
    email: "viewer@test.com",
    role: UserRole.VIEWER,
    is_active: true,
    created_at: "2024-01-01",
    permissions: {
      can_override_risk_scores: false,
      can_view_audit_trail: false,
    },
  },
};

describe("RBAC - AlertDetailModal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Risk Score Override Permissions", () => {
    it("should show edit button for analysts", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.analyst,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => true),
        canOverrideRiskScores: jest.fn(() => true),
        canViewAuditTrail: jest.fn(() => false),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should show edit button
      const editButton = screen.getByLabelText("Override risk score");
      expect(editButton).toBeInTheDocument();
      expect(editButton).not.toBeDisabled();
    });

    it("should show edit button for admins", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.admin,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => true),
        canOverrideRiskScores: jest.fn(() => true),
        canViewAuditTrail: jest.fn(() => true),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should show edit button
      const editButton = screen.getByLabelText("Override risk score");
      expect(editButton).toBeInTheDocument();
      expect(editButton).not.toBeDisabled();
    });

    it("should disable edit button for viewers", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.viewer,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => false),
        canOverrideRiskScores: jest.fn(() => false),
        canViewAuditTrail: jest.fn(() => false),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should show disabled edit button with permission message
      const editButton = screen.getByLabelText(
        "Override risk score - insufficient permissions",
      );
      expect(editButton).toBeInTheDocument();
      expect(editButton).toBeDisabled();
    });

    it("should disable edit button for auditors", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.auditor,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => false),
        canOverrideRiskScores: jest.fn(() => false),
        canViewAuditTrail: jest.fn(() => true),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should show disabled edit button
      const editButton = screen.getByLabelText(
        "Override risk score - insufficient permissions",
      );
      expect(editButton).toBeInTheDocument();
      expect(editButton).toBeDisabled();
    });
  });

  describe("Audit Trail Tab Permissions", () => {
    it("should show audit trail tab for auditors", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.auditor,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => true),
        canOverrideRiskScores: jest.fn(() => false),
        canViewAuditTrail: jest.fn(() => true),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should show audit trail tab
      const auditTab = screen.getByText("Audit Trail");
      expect(auditTab).toBeInTheDocument();
    });

    it("should show audit trail tab for admins", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.admin,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => true),
        canOverrideRiskScores: jest.fn(() => true),
        canViewAuditTrail: jest.fn(() => true),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should show audit trail tab
      const auditTab = screen.getByText("Audit Trail");
      expect(auditTab).toBeInTheDocument();
    });

    it("should hide audit trail tab for analysts", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.analyst,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => false),
        canOverrideRiskScores: jest.fn(() => true),
        canViewAuditTrail: jest.fn(() => false),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should not show audit trail tab
      const auditTab = screen.queryByText("Audit Trail");
      expect(auditTab).not.toBeInTheDocument();
    });

    it("should hide audit trail tab for viewers", () => {
      mockUseAuth.mockReturnValue({
        user: testUsers.viewer,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        setDemoUser: jest.fn(),
        hasRole: jest.fn(() => false),
        canOverrideRiskScores: jest.fn(() => false),
        canViewAuditTrail: jest.fn(() => false),
        refreshUser: jest.fn(),
      });

      render(
        <AlertDetailModal
          isOpen={true}
          alert={mockAlert}
          onClose={jest.fn()}
          onAlertUpdate={jest.fn()}
        />,
      );

      // Should not show audit trail tab
      const auditTab = screen.queryByText("Audit Trail");
      expect(auditTab).not.toBeInTheDocument();
    });
  });
});

describe("RBAC - UserRoleSelector", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should display current user role and permissions", () => {
    mockUseAuth.mockReturnValue({
      user: testUsers.analyst,
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: jest.fn(),
      logout: jest.fn(),
      setDemoUser: jest.fn(),
      hasRole: jest.fn(),
      canOverrideRiskScores: jest.fn(() => true),
      canViewAuditTrail: jest.fn(() => false),
      refreshUser: jest.fn(),
    });

    render(<UserRoleSelector />);

    // Should show analyst role
    expect(screen.getByText("Analyst")).toBeInTheDocument();
    expect(screen.getByText("analyst")).toBeInTheDocument();

    // Should show override permission badge
    expect(screen.getByText("Override")).toBeInTheDocument();

    // Should not show audit permission badge
    expect(screen.queryByText("Audit")).not.toBeInTheDocument();
  });

  it("should show all permission badges for admin", () => {
    mockUseAuth.mockReturnValue({
      user: testUsers.admin,
      isLoading: false,
      isAuthenticated: true,
      error: null,
      login: jest.fn(),
      logout: jest.fn(),
      setDemoUser: jest.fn(),
      hasRole: jest.fn(),
      canOverrideRiskScores: jest.fn(() => true),
      canViewAuditTrail: jest.fn(() => true),
      refreshUser: jest.fn(),
    });

    render(<UserRoleSelector />);

    // Should show admin role
    expect(screen.getByText("Administrator")).toBeInTheDocument();

    // Should show both permission badges
    expect(screen.getByText("Override")).toBeInTheDocument();
    expect(screen.getByText("Audit")).toBeInTheDocument();
  });
});
