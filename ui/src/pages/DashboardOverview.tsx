import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageTransition } from "../components/PageTransition";
import { DashboardToggle } from "../components/DashboardToggle";
import { Alert, AlertDescription } from "../components/ui/alert";
import {
  DashboardContainer,
  DashboardSection,
  FeedCard,
  IOCItem,
  UploadItem,
} from "../components/dashboard";
// StatusBadge components are imported via dashboard components
import {
  HeartPulse,
  Shield,
  Upload,
  Settings,
  Key,
  Palette,
  AlertCircle,
  Database,
  Activity,
} from "lucide-react";

// Data interfaces
interface FeedHealthSummary {
  total_feeds: number;
  healthy_feeds: number;
  unhealthy_feeds: number;
  health_percentage: number;
}

interface HighRiskIOC {
  id: string;
  value: string;
  type: string;
  severity: string;
  timestamp: string;
  feed_name: string;
  confidence: number;
}

interface RecentUpload {
  id: number;
  feed_name: string;
  file_name: string | null;
  import_status: string;
  imported_count: number;
  error_count: number;
  timestamp: string;
  duration_seconds: number | null;
}

export function DashboardOverview() {
  const navigate = useNavigate();
  const location = useLocation();
  const scrollPositionRef = useRef<number>(0);

  // State for dashboard data
  const [feedHealthSummary, setFeedHealthSummary] =
    useState<FeedHealthSummary | null>(null);
  const [highRiskIOCs, setHighRiskIOCs] = useState<HighRiskIOC[]>([]);
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dashboard mode synchronization
  useEffect(() => {
    const currentPath = location.pathname;
    const savedView = localStorage.getItem("dashboardView");

    // If we're on the wrong dashboard for the saved preference, redirect
    if (savedView === "analyst" && currentPath === "/dashboard") {
      // Save current scroll position before redirecting
      scrollPositionRef.current = window.scrollY;
      navigate("/threat-dashboard", { replace: true });
      return;
    }

    // Update localStorage to reflect current view
    if (currentPath === "/dashboard") {
      localStorage.setItem("dashboardView", "admin");
    }
  }, [location.pathname, navigate]);

  // Preserve scroll position when switching dashboards
  useEffect(() => {
    const handleBeforeUnload = () => {
      scrollPositionRef.current = window.scrollY;
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    // Restore scroll position if coming from dashboard switch
    const savedScrollPosition = sessionStorage.getItem(
      "dashboardScrollPosition",
    );
    if (savedScrollPosition) {
      setTimeout(() => {
        window.scrollTo(0, parseInt(savedScrollPosition, 10));
        sessionStorage.removeItem("dashboardScrollPosition");
      }, 100);
    }

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Save scroll position when component unmounts (dashboard switch)
  useEffect(() => {
    return () => {
      sessionStorage.setItem(
        "dashboardScrollPosition",
        window.scrollY.toString(),
      );
    };
  }, []);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch feed health summary
        const healthResponse = await fetch("/api/feeds/health", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("session_token") || ""}`,
          },
        });

        if (healthResponse.ok) {
          const healthData = await healthResponse.json();
          setFeedHealthSummary(healthData.summary);
        }

        // Fetch high-risk IOCs (top 5 most recent with high/critical severity)
        const iocsResponse = await fetch(
          "/api/iocs?severity=high,critical&limit=5&sort=timestamp&order=desc",
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("session_token") || ""}`,
            },
          },
        );

        if (iocsResponse.ok) {
          const iocsData = await iocsResponse.json();
          setHighRiskIOCs(iocsData.iocs || []);
        }

        // Fetch recent uploads (import logs)
        const uploadsResponse = await fetch("/api/feeds/import-logs?limit=5", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("session_token") || ""}`,
          },
        });

        if (uploadsResponse.ok) {
          const uploadsData = await uploadsResponse.json();
          setRecentUploads(uploadsData.logs || []);
        }
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError("Failed to load dashboard data");
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Helper functions - formatTimeAgo is used by IOCItem and UploadItem components

  if (isLoading) {
    return (
      <DashboardLayout title="Dashboard Overview">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Dashboard Overview">
      <PageTransition>
        <DashboardContainer>
          {/* Dashboard Toggle */}
          <div className="flex justify-center mb-4">
            <DashboardToggle />
          </div>

          {/* Error Alert */}
          {error && (
            <Alert className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20 transition-colors duration-200">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              <AlertDescription className="text-red-800 dark:text-red-200">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Main Dashboard Content */}
          <DashboardSection columns={2}>
            {/* Feed Health Snapshot */}
            <FeedCard
              title="Feed Health Snapshot"
              icon={HeartPulse}
              iconColor="text-green-600 dark:text-green-400"
              onViewAll={() => navigate("/feed-health")}
              emptyState={{
                icon: HeartPulse,
                message: "Feed health data unavailable",
              }}
              isLoading={isLoading}
            >
              {feedHealthSummary && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-2xl font-bold text-foreground">
                        {feedHealthSummary.healthy_feeds}/
                        {feedHealthSummary.total_feeds}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Healthy Feeds
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                        {feedHealthSummary.health_percentage.toFixed(1)}%
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Health Score
                      </p>
                    </div>
                  </div>

                  {feedHealthSummary.unhealthy_feeds > 0 && (
                    <div className="flex items-center gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800 transition-colors duration-200">
                      <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                      <span className="text-sm text-yellow-800 dark:text-yellow-200">
                        {feedHealthSummary.unhealthy_feeds} feed
                        {feedHealthSummary.unhealthy_feeds > 1 ? "s" : ""} need
                        attention
                      </span>
                    </div>
                  )}
                </div>
              )}
            </FeedCard>

            {/* High-Risk IOCs */}
            <FeedCard
              title="High-Risk IOCs"
              icon={Shield}
              iconColor="text-red-600 dark:text-red-400"
              onViewAll={() => navigate("/ioc-management")}
              emptyState={{
                icon: Shield,
                message: "No high-risk IOCs found",
              }}
              isLoading={isLoading}
            >
              <div className="space-y-3">
                {highRiskIOCs.slice(0, 5).map((ioc) => (
                  <IOCItem
                    key={ioc.id}
                    value={ioc.value}
                    type={ioc.type}
                    severity={
                      ioc.severity as "critical" | "high" | "medium" | "low"
                    }
                    feedName={ioc.feed_name}
                    timestamp={ioc.timestamp}
                  />
                ))}
              </div>
            </FeedCard>
          </DashboardSection>

          {/* Second Row */}
          <DashboardSection columns={2}>
            {/* Recent Uploads */}
            <FeedCard
              title="Recent Uploads"
              icon={Upload}
              iconColor="text-blue-600 dark:text-blue-400"
              onViewAll={() => navigate("/feed-management")}
              viewAllLabel="View Logs"
              emptyState={{
                icon: Upload,
                message: "No recent uploads",
              }}
              isLoading={isLoading}
            >
              <div className="space-y-3">
                {recentUploads.map((upload) => (
                  <UploadItem
                    key={upload.id}
                    feedName={upload.feed_name}
                    status={
                      upload.import_status as
                        | "success"
                        | "partial"
                        | "failed"
                        | "pending"
                    }
                    importedCount={upload.imported_count}
                    errorCount={upload.error_count}
                    timestamp={upload.timestamp}
                  />
                ))}
              </div>
            </FeedCard>

            {/* Settings Quick Access */}
            <FeedCard
              title="Settings Quick Access"
              icon={Settings}
              iconColor="text-muted-foreground dark:text-muted-foreground"
            >
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => navigate("/settings?tab=api-tokens")}
                  className="flex flex-col items-center gap-3 h-auto py-6 rounded-xl border border-border/50 dark:border-border/50 hover:bg-muted/50 dark:hover:bg-muted/50 transition-colors duration-200 bg-background dark:bg-background"
                >
                  <Key className="h-8 w-8 text-primary dark:text-primary" />
                  <span className="text-sm font-medium text-foreground dark:text-foreground">
                    API Keys
                  </span>
                </button>

                <button
                  onClick={() => navigate("/settings?tab=api-tokens")}
                  className="flex flex-col items-center gap-3 h-auto py-6 rounded-xl border border-border/50 dark:border-border/50 hover:bg-muted/50 dark:hover:bg-muted/50 transition-colors duration-200 bg-background dark:bg-background"
                >
                  <Database className="h-8 w-8 text-primary dark:text-primary" />
                  <span className="text-sm font-medium text-foreground dark:text-foreground">
                    Tokens
                  </span>
                </button>

                <button
                  onClick={() => navigate("/settings?tab=ui-preferences")}
                  className="flex flex-col items-center gap-3 h-auto py-6 rounded-xl border border-border/50 dark:border-border/50 hover:bg-muted/50 dark:hover:bg-muted/50 transition-colors duration-200 bg-background dark:bg-background"
                >
                  <Palette className="h-8 w-8 text-primary dark:text-primary" />
                  <span className="text-sm font-medium text-foreground dark:text-foreground">
                    UI Preferences
                  </span>
                </button>

                <button
                  onClick={() => navigate("/settings")}
                  className="flex flex-col items-center gap-3 h-auto py-6 rounded-xl border border-border/50 dark:border-border/50 hover:bg-muted/50 dark:hover:bg-muted/50 transition-colors duration-200 bg-background dark:bg-background"
                >
                  <Activity className="h-8 w-8 text-primary dark:text-primary" />
                  <span className="text-sm font-medium text-foreground dark:text-foreground">
                    All Settings
                  </span>
                </button>
              </div>
            </FeedCard>
          </DashboardSection>
        </DashboardContainer>
      </PageTransition>
    </DashboardLayout>
  );
}
