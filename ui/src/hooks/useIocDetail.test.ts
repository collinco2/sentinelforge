import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react-hooks";
import { waitFor } from "@testing-library/react";
import { useIocDetail } from "./useIocDetail";
import axios from "axios";
import useSWR from "swr";

// Mock axios
vi.mock("axios");

// Mock SWR
vi.mock("swr");

// Mock API response data
const mockApiResponse = {
  id: 1,
  ioc_type: "domain",
  ioc_value: "malicious-example.com",
  score: 8.5,
  first_seen: "2023-05-15 12:34:56",
  last_seen: "2023-06-15 10:22:43",
  alerts: [
    { id: "1", name: "Network scan detected", timestamp: "2 hours ago" },
    {
      id: "2",
      name: "Suspicious outbound connection",
      timestamp: "4 hours ago",
    },
  ],
  scoring_rationale: {
    factors: [
      {
        name: "Domain Reputation",
        weight: 0.7,
        description: "Poor reputation score",
      },
      {
        name: "Age of Domain",
        weight: 0.3,
        description: "Recently registered",
      },
    ],
    model_version: "v2.3",
    model_last_updated: "7 days ago",
  },
  mitre_techniques: [
    { id: "T1566", name: "Phishing", confidence: "high" },
    { id: "T1071", name: "Application Layer Protocol", confidence: "medium" },
  ],
  mitre_tactics: [
    { id: "TA0001", name: "Initial Access" },
    { id: "TA0011", name: "Command and Control" },
  ],
};

describe("useIocDetail hook", () => {
  const mutate = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();

    // Setup axios mock
    (axios.get as any).mockResolvedValue({ data: mockApiResponse });

    // Default SWR mock for success case
    (useSWR as any).mockImplementation((key: string | null) => {
      if (!key) {
        return {
          data: undefined,
          error: undefined,
          isLoading: false,
          mutate,
        };
      }

      return {
        data: mockApiResponse,
        error: undefined,
        isLoading: false,
        mutate,
      };
    });
  });

  it("returns correct data structure", async () => {
    const { result } = renderHook(() => useIocDetail("1"));

    // Wait for data to be available
    await waitFor(() => {
      expect(result.current.iocDetail).toBeDefined();
    });

    // Then check the structure
    expect(result.current).toHaveProperty("iocDetail");
    expect(result.current).toHaveProperty("isLoading");
    expect(result.current).toHaveProperty("isError");
    expect(result.current).toHaveProperty("error");
    expect(result.current).toHaveProperty("mutate");
  });

  it("transforms API data correctly", async () => {
    // Create a custom response with expected property mappings
    const mockTransformedResponse = {
      ...mockApiResponse,
      // Add properties expected by the transform function
      attack_techniques: mockApiResponse.mitre_techniques,
      tactics: mockApiResponse.mitre_tactics,
    };

    // Update the SWR mock for this test only
    (useSWR as any).mockImplementation(() => {
      return {
        data: mockTransformedResponse,
        error: undefined,
        isLoading: false,
        mutate,
      };
    });

    const { result } = renderHook(() => useIocDetail("1"));

    // Wait for data to be available
    await waitFor(() => {
      expect(result.current.iocDetail).toBeDefined();
    });

    // Then check the transformation details
    const ioc = result.current.iocDetail!;
    expect(ioc.id).toBe("1");
    expect(ioc.value).toBe("malicious-example.com");
    expect(ioc.type).toBe("domain");
    expect(ioc.severity).toBe("critical");
    expect(ioc.confidence).toBe(85);
    expect(ioc.first_observed).toBe("2023-05-15 12:34:56");
    expect(ioc.last_seen).toBe("2023-06-15 10:22:43");

    // Check scoring rationale and other extended properties
    expect(ioc.scoring_rationale).toBeDefined();
    expect(ioc.scoring_rationale?.factors).toHaveLength(2);
    expect(ioc.alerts).toHaveLength(2);
    expect(ioc.mitre_techniques).toHaveLength(2);
    expect(ioc.mitre_tactics).toHaveLength(2);
  });

  it("handles errors correctly", async () => {
    // Setup SWR mock for error case
    (useSWR as any).mockImplementation(() => {
      return {
        data: undefined,
        error: new Error("IOC not found"),
        isLoading: false,
        mutate,
      };
    });

    const { result } = renderHook(() => useIocDetail("999"));

    // Should return error state
    expect(result.current.isError).toBe(true);
    expect(result.current.error).toBeDefined();
  });

  it("returns null when no iocId is provided", async () => {
    // Setup SWR mock for null case
    (useSWR as any).mockImplementation(() => {
      return {
        data: undefined,
        error: undefined,
        isLoading: false,
        mutate,
      };
    });

    const { result } = renderHook(() => useIocDetail(null));

    // Should not be loading and should have null data
    expect(result.current.isLoading).toBe(false);
    expect(result.current.iocDetail).toBeNull();
  });
});
