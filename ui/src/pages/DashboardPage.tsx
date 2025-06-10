import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageTransition } from "../components/PageTransition";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Alert, AlertDescription } from "../components/ui/alert";
import { useThemeClass, getStatusBadgeClass, getSeverityBadgeClass } from "../hooks/useThemeClass";
import {
  HeartPulse,
  Shield,
  Upload,
  Settings,
  Key,
  Palette,
  ExternalLink,
  AlertCircle,
  FileText,
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

export function DashboardPage() {
  const navigate = useNavigate();
  const theme = useThemeClass();

  // State for dashboard data
  const [feedHealthSummary, setFeedHealthSummary] =
    useState<FeedHealthSummary | null>(null);
  const [highRiskIOCs, setHighRiskIOCs] = useState<HighRiskIOC[]>([]);
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // Helper functions

  const getImportStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return (
          <Badge className={getStatusBadgeClass("success")}>
            Success
          </Badge>
        );
      case "partial":
        return (
          <Badge className={getStatusBadgeClass("warning")}>
            Partial
          </Badge>
        );
      case "failed":
        return (
          <Badge className={getStatusBadgeClass("error")}>
            Failed
          </Badge>
        );
      default:
        return <Badge className={getStatusBadgeClass("default")}>{status}</Badge>;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const severityLevel = severity.toLowerCase() as "critical" | "high" | "medium" | "low";

    switch (severityLevel) {
      case "critical":
        return <Badge className={getSeverityBadgeClass("critical")}>Critical</Badge>;
      case "high":
        return <Badge className={getSeverityBadgeClass("high")}>High</Badge>;
      case "medium":
        return <Badge className={getSeverityBadgeClass("medium")}>Medium</Badge>;
      case "low":
        return <Badge className={getSeverityBadgeClass("low")}>Low</Badge>;
      default:
        return <Badge className={getStatusBadgeClass("default")}>{severity}</Badge>;
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

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
        <div className="space-y-6">
          {/* Error Alert */}
          {error && (
            <Alert className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              <AlertDescription className="text-red-800 dark:text-red-200">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Feed Health Snapshot */}
            <Card className={theme.card}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <HeartPulse className="h-5 w-5 text-green-600 dark:text-green-400" />
                  Feed Health Snapshot
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/feed-health")}
                  className="flex items-center gap-1"
                >
                  <ExternalLink className="h-3 w-3" />
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                {feedHealthSummary ? (
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
                      <div className="flex items-center gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                        <span className="text-sm text-yellow-800 dark:text-yellow-200">
                          {feedHealthSummary.unhealthy_feeds} feed
                          {feedHealthSummary.unhealthy_feeds > 1 ? "s" : ""}{" "}
                          need attention
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <HeartPulse className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Feed health data unavailable</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* High-Risk IOCs */}
            <Card className={theme.card}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Shield className="h-5 w-5 text-red-600 dark:text-red-400" />
                  High-Risk IOCs
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/ioc-management")}
                  className="flex items-center gap-1"
                >
                  <ExternalLink className="h-3 w-3" />
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                {highRiskIOCs.length > 0 ? (
                  <div className="space-y-3">
                    {highRiskIOCs.slice(0, 5).map((ioc) => (
                      <div
                        key={ioc.id}
                        className="flex items-center justify-between p-2 bg-muted/50 rounded-lg"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <code className="text-xs font-mono bg-background px-1 rounded truncate">
                              {ioc.value}
                            </code>
                            {getSeverityBadge(ioc.severity)}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{ioc.type}</span>
                            <span>•</span>
                            <span>{ioc.feed_name}</span>
                            <span>•</span>
                            <span>{formatTimeAgo(ioc.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No high-risk IOCs found</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Second Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Uploads */}
            <Card className={theme.card}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Upload className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  Recent Uploads
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/feed-management")}
                  className="flex items-center gap-1"
                >
                  <ExternalLink className="h-3 w-3" />
                  View Logs
                </Button>
              </CardHeader>
              <CardContent>
                {recentUploads.length > 0 ? (
                  <div className="space-y-3">
                    {recentUploads.map((upload) => (
                      <div
                        key={upload.id}
                        className="flex items-center justify-between p-2 bg-muted/50 rounded-lg"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium truncate">
                              {upload.feed_name}
                            </span>
                            {getImportStatusBadge(upload.import_status)}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{upload.imported_count} imported</span>
                            {upload.error_count > 0 && (
                              <>
                                <span>•</span>
                                <span className="text-red-600 dark:text-red-400">
                                  {upload.error_count} errors
                                </span>
                              </>
                            )}
                            <span>•</span>
                            <span>{formatTimeAgo(upload.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <Upload className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No recent uploads</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Settings Quick Access */}
            <Card className={theme.card}>
              <CardHeader>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Settings className="h-5 w-5 text-muted-foreground" />
                  Settings Quick Access
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    variant="outline"
                    onClick={() => navigate("/settings?tab=api-tokens")}
                    className="flex flex-col items-center gap-2 h-auto py-4"
                  >
                    <Key className="h-6 w-6 text-primary" />
                    <span className="text-sm">API Keys</span>
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => navigate("/settings?tab=api-tokens")}
                    className="flex flex-col items-center gap-2 h-auto py-4"
                  >
                    <Database className="h-6 w-6 text-primary" />
                    <span className="text-sm">Tokens</span>
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => navigate("/settings?tab=ui-preferences")}
                    className="flex flex-col items-center gap-2 h-auto py-4"
                  >
                    <Palette className="h-6 w-6 text-primary" />
                    <span className="text-sm">UI Preferences</span>
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => navigate("/settings")}
                    className="flex flex-col items-center gap-2 h-auto py-4"
                  >
                    <Activity className="h-6 w-6 text-primary" />
                    <span className="text-sm">All Settings</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
