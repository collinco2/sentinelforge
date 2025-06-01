import { useState, useEffect, useCallback } from "react";

// Define the data structure
export interface AlertTimelineDataPoint {
  date: string;
  count: number;
}

// Define the API response structure
interface TimelineApiResponseItem {
  date: string;
  timestamp: number;
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface UseAlertTimelineParams {
  groupBy?: "day" | "hour";
  startDate?: number;
  endDate?: number;
}

export function useAlertTimeline({
  groupBy = "day",
  startDate,
  endDate,
}: UseAlertTimelineParams = {}) {
  const [data, setData] = useState<AlertTimelineDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasAttemptedFetch, setHasAttemptedFetch] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query parameters
      const params = new URLSearchParams();
      params.append("group_by", groupBy);
      if (startDate) params.append("start_date", startDate.toString());
      if (endDate) params.append("end_date", endDate.toString());

      console.log("[useAlertTimeline] Fetching timeline data with params:", {
        groupBy,
        startDate,
        endDate,
      });

      // Fetch from timeline API
      const response = await fetch(
        `http://localhost:5101/api/alerts/timeline?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch (${response.status})`);
      }

      const responseData: TimelineApiResponseItem[] = await response.json();

      // Log the raw response for inspection
      console.log("[useAlertTimeline] API Response:", responseData);

      if (!responseData || !Array.isArray(responseData)) {
        console.error("[useAlertTimeline] Invalid API response format:", responseData);
        throw new Error("Invalid API response format");
      }

      if (responseData.length === 0) {
        console.log("[useAlertTimeline] API returned empty data set");
        setData([]);
        setError(null);
        setHasAttemptedFetch(true);
        return;
      }

      // Log the first item structure to examine date formatting
      if (responseData.length > 0) {
        console.log("[useAlertTimeline] First item structure:", responseData[0]);
      }

      // Transform the response data to match AlertTimelineDataPoint interface
      const formatted = responseData.map((item: TimelineApiResponseItem) => ({
        // Prefer timestamp if available (convert to string), fallback to date string
        date: item.timestamp ? item.timestamp.toString() : item.date || "",
        count: Number(item.total) || 0, // Default to 0 if total is missing or falsy
      }));

      setData(formatted);
      setError(null);
      setHasAttemptedFetch(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      console.error("[useAlertTimeline] Timeline fetch error:", err);
      setError(`Failed to load alert timeline data: ${errorMessage}`);
      setData([]);
      setHasAttemptedFetch(true);
    } finally {
      setLoading(false);
    }
  }, [groupBy, startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = () => {
    fetchData();
  };

  return {
    data,
    loading,
    error,
    hasAttemptedFetch,
    refetch,
  };
} 