import React from "react";
import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { AlertDetailModal } from "../AlertDetailModal";
import { UserRoleSelector } from "../UserRoleSelector";
import { UserRole } from "../../services/auth";

import { useAuth } from "../../hooks/useAuth";

// Mock dependencies
vi.mock("../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../services/api", () => ({
  overrideAlertRiskScore: vi.fn(),
  fetchAuditLogs: vi.fn(),
  getAuthHeaders: vi.fn(() => ({})),
}));

vi.mock("../../components/ui/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

const mockUseAuth = vi.mocked(useAuth);

// Mock alert data
const mockAlert = {
  id: 1,
  name: "Test Alert",
  description: "Test alert description",
  severity: "high",
  risk_score: 75,
  overridden_risk_score: null,
  status: "open",
  created_at: "2023-12-21T10:00:00Z",
  updated_at: "2023-12-21T10:00:00Z",
  source: "test",
  category: "malware",
  iocs: [],
  metadata: {},
};

describe("RBAC Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render AlertDetailModal for analysts", () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 1,
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
      hasRole: vi.fn(() => true),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => false),
      refreshUser: vi.fn(),
    });

    render(
      <AlertDetailModal
        isOpen={true}
        alert={mockAlert}
        onClose={vi.fn()}
        onAlertUpdate={vi.fn()}
      />,
    );

    expect(screen.getByText("Test Alert")).toBeInTheDocument();
  });

  it("should render UserRoleSelector", () => {
    mockUseAuth.mockReturnValue({
      user: {
        user_id: 1,
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
      hasRole: vi.fn(),
      canOverrideRiskScores: vi.fn(() => true),
      canViewAuditTrail: vi.fn(() => false),
      refreshUser: vi.fn(),
    });

    render(<UserRoleSelector />);

    expect(screen.getByText("analyst")).toBeInTheDocument();
  });
});
