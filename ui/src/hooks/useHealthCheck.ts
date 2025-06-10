import { useState, useCallback } from "react";
import { FeedHealthResult } from "../components/health/ProgressModal";
import { toast } from "../lib/toast";

export interface HealthCheckSummary {
  total_feeds: number;
  healthy_feeds: number;
  unhealthy_feeds: number;
  health_percentage: number;
}

export interface HealthCheckResult {
  success: boolean;
  summary: HealthCheckSummary;
  feeds: FeedHealthResult[];
  checked_at: string;
  checked_by: string;
  from_cache: boolean;
  cache_age_seconds?: number;
  session_id?: string;
}

/**
 * Custom hook for managing feed health checks with progress tracking
 *
 * Features:
 * - Progress modal state management
 * - Health check result caching
 * - Error handling and user feedback
 * - Background vs. foreground check modes
 */
export const useHealthCheck = () => {
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [healthData, setHealthData] = useState<HealthCheckResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Start health check with progress modal
  const startHealthCheckWithProgress = useCallback(
    (feedId?: number, useDemo: boolean = false) => {
      setIsProgressModalOpen(true);
      setError(null);

      // Store demo flag for the modal to use
      if (useDemo) {
        localStorage.setItem("healthCheckDemo", "true");
      } else {
        localStorage.removeItem("healthCheckDemo");
      }
    },
    [],
  );

  // Handle progress modal completion
  const handleProgressComplete = useCallback((results: FeedHealthResult[]) => {
    // Calculate summary from results
    const total_feeds = results.length;
    const healthy_feeds = results.filter((r) => r.status === "ok").length;
    const unhealthy_feeds = total_feeds - healthy_feeds;
    const health_percentage =
      total_feeds > 0 ? Math.round((healthy_feeds / total_feeds) * 100) : 0;

    const healthResult: HealthCheckResult = {
      success: true,
      summary: {
        total_feeds,
        healthy_feeds,
        unhealthy_feeds,
        health_percentage,
      },
      feeds: results,
      checked_at: new Date().toISOString(),
      checked_by: "current_user", // This would come from auth context
      from_cache: false,
    };

    setHealthData(healthResult);
    toast.success(
      `Health check completed: ${healthy_feeds}/${total_feeds} feeds healthy`,
    );
  }, []);

  // Handle progress modal close
  const handleProgressClose = useCallback(() => {
    setIsProgressModalOpen(false);
  }, []);

  // Fetch cached health data (for immediate display)
  const fetchCachedHealth = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/feeds/health", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: HealthCheckResult = await response.json();
      setHealthData(data);

      if (data.from_cache && data.cache_age_seconds) {
        const ageMinutes = Math.round(data.cache_age_seconds / 60);
        toast.info(`Showing cached data (${ageMinutes} minutes old)`);
      }

      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch health data";
      setError(errorMessage);
      toast.error(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Force refresh health data (triggers new check)
  const forceRefreshHealth = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/feeds/health?force=true", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: HealthCheckResult = await response.json();
      setHealthData(data);
      toast.success("Health data refreshed");
      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to refresh health data";
      setError(errorMessage);
      toast.error(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Check if health data is stale (older than 5 minutes)
  const isHealthDataStale = useCallback(() => {
    if (!healthData || !healthData.checked_at) return true;

    const checkedAt = new Date(healthData.checked_at);
    const now = new Date();
    const ageMinutes = (now.getTime() - checkedAt.getTime()) / (1000 * 60);

    return ageMinutes > 5;
  }, [healthData]);

  // Get health status summary for quick display
  const getHealthSummary = useCallback(() => {
    if (!healthData) return null;

    return {
      ...healthData.summary,
      isStale: isHealthDataStale(),
      lastChecked: healthData.checked_at,
      fromCache: healthData.from_cache,
    };
  }, [healthData, isHealthDataStale]);

  // Get feeds by status for filtering
  const getFeedsByStatus = useCallback(
    (status?: string) => {
      if (!healthData) return [];

      if (!status) return healthData.feeds;

      return healthData.feeds.filter((feed) => feed.status === status);
    },
    [healthData],
  );

  return {
    // State
    healthData,
    isLoading,
    error,
    isProgressModalOpen,

    // Actions
    startHealthCheckWithProgress,
    handleProgressComplete,
    handleProgressClose,
    fetchCachedHealth,
    forceRefreshHealth,

    // Computed values
    getHealthSummary,
    getFeedsByStatus,
    isHealthDataStale: isHealthDataStale(),

    // Quick access to common data
    summary: healthData?.summary || null,
    feeds: healthData?.feeds || [],
    healthyFeeds: getFeedsByStatus("ok"),
    unhealthyFeeds: healthData?.feeds.filter((f) => f.status !== "ok") || [],
  };
};

export default useHealthCheck;
