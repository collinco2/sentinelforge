import useSWR from "swr";
import axios from "axios";
import { IOCData } from "../components/IocTable";

// Extended IOC data interface with additional details
export interface IocDetailData extends IOCData {
  first_observed: string;
  last_seen?: string;
  scoring_rationale?: {
    factors: Array<{
      name: string;
      weight: number;
      description: string;
    }>;
    model_version?: string;
    model_last_updated?: string;
  };
  alerts?: Array<{
    id: string;
    name: string;
    timestamp: string;
    source?: string;
  }>;
  mitre_techniques?: Array<{
    id: string;
    name: string;
    confidence: "high" | "medium" | "low";
  }>;
  mitre_tactics?: Array<{
    id: string;
    name: string;
  }>;
  relationships?: Array<{
    id: string;
    type: string;
    value: string;
    first_seen?: string;
  }>;
}

// Fetcher function for SWR
const fetcher = async (url: string) => {
  try {
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    // Handle axios errors
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        throw new Error("IOC not found");
      } else if (error.response?.status === 403) {
        throw new Error("You don't have permission to view this IOC");
      } else if (error.response?.status === 500) {
        throw new Error("Server error. Please try again later.");
      }
    }
    throw error;
  }
};

// Transform API response to match expected format
const transformResponse = (data: any): IocDetailData => {
  // If IOC data is already in the right format, return it directly
  if (data?.ioc_value && data?.ioc_type) {
    return {
      id: String(data.id),
      value: data.ioc_value || data.value || "",
      type: mapApiType(data.ioc_type || ""),
      severity: mapApiSeverityToUi(data.score || 0),
      confidence: Math.round((data.score || 0) * 10), // Convert 0-10 score to 0-100 confidence
      timestamp:
        data.first_seen || data.first_observed || new Date().toISOString(),
      first_observed: data.first_seen || data.first_observed,
      last_seen: data.last_seen,
      scoring_rationale: data.scoring_rationale || {
        factors:
          data.feature_importance?.map((f: any) => ({
            name: f.feature,
            weight: f.weight,
            description: "",
          })) || [],
        model_version: data.model_version || "v2.3",
        model_last_updated: data.model_last_updated || "7 days ago",
      },
      alerts: data.alerts || [],
      mitre_techniques:
        data.mitre_techniques ||
        data.attack_techniques?.map((t: any) => ({
          id: t.id,
          name: t.name,
          confidence: t.confidence || "medium",
        })) ||
        [],
      mitre_tactics: data.mitre_tactics || data.tactics || [],
      relationships: data.relationships || [],
    };
  }

  // If no data is available, return a minimal object
  return {
    id: "",
    value: "",
    type: "domain",
    severity: "medium",
    confidence: 0,
    timestamp: new Date().toISOString(),
    first_observed: new Date().toISOString(),
  };
};

// Map API type to UI type (same as in useIocs.ts)
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

// Map API score to UI severity (same as in useIocs.ts)
const mapApiSeverityToUi = (score: number): IOCData["severity"] => {
  if (score >= 8.5) return "critical";
  if (score >= 7.5) return "high";
  if (score >= 5) return "medium";
  return "low";
};

interface UseIocDetailReturn {
  iocDetail: IocDetailData | null;
  isLoading: boolean;
  isError: any;
  error: Error | null;
  mutate: () => void;
}

export function useIocDetail(
  iocId: string | null | undefined,
): UseIocDetailReturn {
  // Don't fetch if no ID is provided
  const shouldFetch = !!iocId;
  const url = shouldFetch ? `/api/ioc/${iocId}` : null;

  const { data, error, mutate } = useSWR(url, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
    refreshInterval: 0, // Don't auto-refresh for details
    shouldRetryOnError: true,
    errorRetryCount: 2,
    dedupingInterval: 10000, // 10 seconds
    focusThrottleInterval: 5000,
  });

  // Transform the data if it exists
  const transformedData = data ? transformResponse(data) : null;

  return {
    iocDetail: transformedData,
    isLoading: shouldFetch && !error && !data,
    isError: !!error,
    error: error as Error | null,
    mutate,
  };
}
