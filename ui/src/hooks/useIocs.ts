import useSWR from "swr";
import axios from "axios";
import { IocFilters } from "../components/FilterSidebar";
import { IOCData } from "../components/IocTable";

// Base API URL - Use the full URL for production builds
const API_BASE_URL = "http://localhost:5059/api/iocs";

// Fetcher function for SWR
const fetcher = async (url: string) => {
  console.log("Fetching from:", url);
  const response = await axios.get(url);
  return response.data;
};

// Create query string from filters
const createQueryString = (filters: IocFilters): string => {
  const params = new URLSearchParams();

  // Add type filters if any are selected
  const selectedTypes = Object.entries(filters.types || {})
    .filter(([_, isSelected]) => isSelected)
    .map(([type]) => type);

  if (selectedTypes.length > 0) {
    // Backend expects 'ioc_type' parameter
    params.append("ioc_type", selectedTypes.join(","));
  }

  // Add severity filters if any are selected - Map to score ranges
  const selectedSeverities = Object.entries(filters.severities || {})
    .filter(([_, isSelected]) => isSelected)
    .map(([severity]) => severity);

  if (selectedSeverities.length > 0) {
    // Map severities to score ranges for the API
    // Based on API logic: score > 7.5 = high, score > 5 = medium, else low

    if (selectedSeverities.includes("critical")) {
      // Critical is 8.5-10
      params.append("min_score", "8.5");
    } else if (selectedSeverities.includes("high")) {
      // High is 7.5-8.5
      params.append("min_score", "7.5");
    } else if (selectedSeverities.includes("medium")) {
      // Medium is 5-7.5
      params.append("min_score", "5");
    } else if (selectedSeverities.includes("low")) {
      // Low is 0-5
      params.append("max_score", "5");
    }
  }

  // Add confidence range if not default - Map to score in API
  const confidenceRange = filters.confidenceRange || [0, 100];
  const minConfidence = confidenceRange[0] ?? 0;
  const maxConfidence = confidenceRange[1] ?? 100;

  if (minConfidence > 0) {
    // Convert confidence percentage to score (0-10 scale)
    params.append("min_score", String(minConfidence / 10));
  }
  if (maxConfidence < 100) {
    // Convert confidence percentage to score (0-10 scale)
    params.append("max_score", String(maxConfidence / 10));
  }

  // Add date range filters if specified
  if (filters.dateRange) {
    if (filters.dateRange.from) {
      params.append("from_date", filters.dateRange.from);
    }
    if (filters.dateRange.to) {
      params.append("to_date", filters.dateRange.to);
    }
  }

  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
};

// Transform API data to match our frontend data model
const transformApiResponse = (data: any): IOCData[] => {
  if (!data || !data.iocs || !Array.isArray(data.iocs)) {
    return [];
  }

  return data.iocs.map((ioc: any) => ({
    id: String(ioc.id),
    value: ioc.ioc_value || ioc.value || "",
    type: mapApiType(ioc.ioc_type || ""),
    severity: mapApiSeverityToUi(ioc.score || 0),
    confidence: Math.round((ioc.score || 0) * 10), // Convert 0-10 score to 0-100 confidence
    timestamp: ioc.last_seen || ioc.first_seen || new Date().toISOString(),
  }));
};

// Map API ioc_type to UI type
const mapApiType = (apiType: string): IOCData["type"] => {
  switch (apiType) {
    case "domain":
      return "domain";
    case "ip":
      return "ip";
    case "hash":
      return "file";
    case "url":
      return "url";
    case "email":
      return "email";
    default:
      // Try to match as closely as possible
      if (apiType.includes("file") || apiType.includes("hash")) return "file";
      if (apiType.includes("url")) return "url";
      if (apiType.includes("domain")) return "domain";
      if (apiType.includes("ip")) return "ip";
      if (apiType.includes("email")) return "email";
      return "domain"; // Default fallback
  }
};

// Map API score to UI severity
const mapApiSeverityToUi = (score: number): IOCData["severity"] => {
  if (score >= 8.5) return "critical";
  if (score >= 7.5) return "high";
  if (score >= 5) return "medium";
  return "low";
};

// Interface for the hook return value
interface UseIocsReturn {
  iocs: IOCData[];
  isLoading: boolean;
  isError: any;
  mutate: () => void;
}

// Main hook function
export function useIocs(filters: IocFilters): UseIocsReturn {
  // Ensure filters is always defined
  const safeFilters: IocFilters = filters || { ...defaultFilters };

  // Create query string from filters
  const queryString = createQueryString(safeFilters);

  // Complete URL with query parameters
  const url = `${API_BASE_URL}${queryString}`;

  // Use SWR with proper caching and refresh strategy
  const { data, error, mutate } = useSWR(url, fetcher, {
    revalidateOnFocus: true,
    revalidateOnReconnect: true,
    refreshInterval: 60000, // Refresh every minute
    shouldRetryOnError: true,
    errorRetryCount: 3,
    dedupingInterval: 5000,
    onErrorRetry: (error, key, config, revalidate, { retryCount }) => {
      // Never retry on 404s
      if (error.status === 404) return;

      // Only retry up to 3 times
      if (retryCount >= 3) return;

      // Retry after 5 seconds
      setTimeout(() => revalidate({ retryCount }), 5000);
    },
  });

  // Log fetched data for debugging
  if (data) {
    console.log("Fetched IOCs from API:", data);
  }

  // Transform and return the data
  const transformedData = data ? transformApiResponse(data) : [];

  return {
    iocs: transformedData,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

// Default filters - also defined here for use in hook
const defaultFilters: IocFilters = {
  types: {
    domain: false,
    ip: false,
    file: false,
    url: false,
    email: false,
  },
  severities: {
    critical: false,
    high: false,
    medium: false,
    low: false,
  },
  confidenceRange: [0, 100],
};

// Helper for analyzing IOCs
export function analyzeIocs(iocs: IOCData[]) {
  if (!iocs || iocs.length === 0) {
    return {
      total: 0,
      bySeverity: { critical: 0, high: 0, medium: 0, low: 0 },
      byType: { domain: 0, ip: 0, file: 0, url: 0, email: 0 },
      highestConfidence: 0,
      avgConfidence: 0,
      recentCount: 0, // IOCs in last 24h
    };
  }

  // Count by severity
  const bySeverity = iocs.reduce(
    (acc, ioc) => {
      const severity = ioc.severity || "unknown";
      acc[severity] = (acc[severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  // Count by type
  const byType = iocs.reduce(
    (acc, ioc) => {
      const type = ioc.type || "unknown";
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  // Calculate highest confidence
  const confidences = iocs.map((ioc) => ioc.confidence ?? 0).filter(Boolean);
  const highestConfidence = confidences.length ? Math.max(...confidences) : 0;

  // Calculate average confidence
  const avgConfidence = confidences.length
    ? Math.round(
        confidences.reduce((sum, val) => sum + val, 0) / confidences.length,
      )
    : 0;

  // Count recent IOCs (last 24 hours)
  const now = new Date();
  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const recentCount = iocs.filter((ioc) => {
    if (!ioc.timestamp) return false;
    try {
      return new Date(ioc.timestamp) >= oneDayAgo;
    } catch (e) {
      return false;
    }
  }).length;

  return {
    total: iocs.length,
    bySeverity,
    byType,
    highestConfidence,
    avgConfidence,
    recentCount,
  };
}
