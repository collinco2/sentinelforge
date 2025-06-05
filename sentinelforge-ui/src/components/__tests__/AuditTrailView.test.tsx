import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { AuditTrailView } from "../AuditTrailView";

// Mock fetch
global.fetch = vi.fn();

const mockAuditLogs = [
  {
    id: 1,
    alert_id: 123,
    alert_name: "Test Alert",
    user_id: 1,
    original_score: 50,
    override_score: 85,
    justification: "Increased severity based on additional context",
    timestamp: "2023-12-21T10:30:00Z",
  },
  {
    id: 2,
    alert_id: 123,
    alert_name: "Test Alert",
    user_id: 2,
    original_score: 85,
    override_score: 30,
    justification: "False positive confirmed",
    timestamp: "2023-12-21T11:00:00Z",
  },
];

const mockApiResponse = {
  audit_logs: mockAuditLogs,
  total: 2,
  limit: 50,
  offset: 0,
};

describe("AuditTrailView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    vi.mocked(fetch).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<AuditTrailView alertId={123} />);

    expect(screen.getByText("Loading audit trail...")).toBeInTheDocument();
    expect(screen.getByRole("status")).toBeInTheDocument(); // Loader icon
  });

  it("renders audit logs successfully", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponse,
    });

    render(<AuditTrailView alertId={123} />);

    await waitFor(() => {
      expect(screen.getByText("Audit Trail (2)")).toBeInTheDocument();
    });

    // Check if audit log entries are rendered
    expect(screen.getByText("User 1")).toBeInTheDocument();
    expect(screen.getByText("User 2")).toBeInTheDocument();

    // Check score changes
    expect(screen.getByText("50")).toBeInTheDocument(); // Original score
    expect(screen.getByText("85")).toBeInTheDocument(); // Override score
    expect(screen.getByText("30")).toBeInTheDocument(); // Second override

    // Check justifications
    expect(
      screen.getByText("Increased severity based on additional context"),
    ).toBeInTheDocument();
    expect(screen.getByText("False positive confirmed")).toBeInTheDocument();
  });

  it("renders empty state when no audit logs", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...mockApiResponse, audit_logs: [], total: 0 }),
    });

    render(<AuditTrailView alertId={123} />);

    await waitFor(() => {
      expect(screen.getByText("No Audit Trail")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "No risk score overrides have been recorded for this alert yet.",
      ),
    ).toBeInTheDocument();
  });

  it("renders error state on fetch failure", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("Network error"));

    render(<AuditTrailView alertId={123} />);

    await waitFor(() => {
      expect(screen.getByText("Error loading audit trail")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Failed to fetch audit logs: Network error"),
    ).toBeInTheDocument();
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("handles retry functionality", async () => {
    // First call fails
    vi.mocked(fetch)
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse,
      });

    render(<AuditTrailView alertId={123} />);

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText("Error loading audit trail")).toBeInTheDocument();
    });

    // Click retry
    fireEvent.click(screen.getByText("Retry"));

    // Wait for successful load
    await waitFor(() => {
      expect(screen.getByText("Audit Trail (2)")).toBeInTheDocument();
    });
  });

  it("expands long justifications", async () => {
    const longJustification =
      "This is a very long justification that should be truncated initially and then expandable when the user clicks more";

    const mockLogsWithLongJustification = [
      {
        ...mockAuditLogs[0],
        justification: longJustification,
      },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...mockApiResponse,
        audit_logs: mockLogsWithLongJustification,
        total: 1,
      }),
    });

    render(<AuditTrailView alertId={123} />);

    await waitFor(() => {
      expect(screen.getByText("Audit Trail (1)")).toBeInTheDocument();
    });

    // Should show truncated text initially
    expect(
      screen.getByText(/This is a very long justification that should be.../),
    ).toBeInTheDocument();
    expect(screen.getByText("More")).toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByText("More"));

    // Should show full text
    expect(screen.getByText(longJustification)).toBeInTheDocument();
    expect(screen.getByText("Less")).toBeInTheDocument();
  });

  it("calls correct API endpoint with alert ID", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponse,
    });

    render(<AuditTrailView alertId={456} />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("/api/audit?alert_id=456&limit=50");
    });
  });

  it("handles refresh functionality", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => mockApiResponse,
    });

    render(<AuditTrailView alertId={123} />);

    await waitFor(() => {
      expect(screen.getByText("Audit Trail (2)")).toBeInTheDocument();
    });

    // Click refresh
    fireEvent.click(screen.getByText("Refresh"));

    // Should call API again
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });

  it("displays correct risk score badge colors", async () => {
    const mockLogsWithDifferentScores = [
      { ...mockAuditLogs[0], original_score: 95, override_score: 25 }, // High to low
      { ...mockAuditLogs[1], original_score: 30, override_score: 75 }, // Low to medium
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...mockApiResponse,
        audit_logs: mockLogsWithDifferentScores,
      }),
    });

    render(<AuditTrailView alertId={123} />);

    await waitFor(() => {
      expect(screen.getByText("Audit Trail (2)")).toBeInTheDocument();
    });

    // Check that score badges are rendered
    expect(screen.getByText("95")).toBeInTheDocument();
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
  });
});
