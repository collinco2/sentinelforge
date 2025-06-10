import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageHeader, BREADCRUMB_CONFIGS } from "../components/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Alert, AlertDescription } from "../components/ui/alert";
import {
  HeartPulse,
  ArrowLeft,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Activity,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { useHealthCheck } from "../hooks/useHealthCheck";
import ProgressModal from "../components/health/ProgressModal";

export const FeedHealthPage: React.FC = () => {
  const { hasRole } = useAuth();
  const navigate = useNavigate();
  const {
    isLoading,
    error,
    isProgressModalOpen,
    startHealthCheckWithProgress,
    handleProgressComplete,
    handleProgressClose,
    fetchCachedHealth,
    summary,
    feeds,
    isHealthDataStale,
  } = useHealthCheck();

  const canViewHealth = hasRole([UserRole.ANALYST, UserRole.ADMIN]);

  useEffect(() => {
    if (canViewHealth) {
      fetchCachedHealth();
    }
  }, [canViewHealth, fetchCachedHealth]);

  const handleRefresh = () => {
    startHealthCheckWithProgress();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "ok":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "timeout":
      case "unauthorized":
      case "rate_limited":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case "unreachable":
      case "server_error":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      ok: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      timeout:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      unauthorized:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      rate_limited:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      unreachable: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
      server_error: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    };

    return (
      <Badge className={variants[status] || "bg-gray-100 text-gray-800"}>
        {status.replace("_", " ")}
      </Badge>
    );
  };

  const formatResponseTime = (ms: number | null) => {
    if (ms === null) return "N/A";
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatLastChecked = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 1) return "Just now";
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  if (!canViewHealth) {
    return (
      <DashboardLayout title="Feed Health">
        <div className="flex items-center justify-center min-h-[400px]">
          <Alert className="max-w-md">
            <HeartPulse className="h-4 w-4" />
            <AlertDescription>
              You don't have permission to view feed health. Contact your
              administrator for access.
            </AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Feed Health">
      <div className="space-y-6" data-testid="feed-health-page">
        {/* Back Button */}
        <div className="flex items-center mb-4">
          <Button
            variant="ghost"
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>

        {/* Page Header with Breadcrumbs */}
        <PageHeader
          title="Feed Health"
          description="Monitor threat intelligence feed availability and performance"
          breadcrumbs={BREADCRUMB_CONFIGS.FEEDS_HEALTH}
          icon={HeartPulse}
          actions={
            <div className="flex items-center gap-2">
              {isHealthDataStale && (
                <Badge variant="outline" className="text-yellow-600">
                  Data may be stale
                </Badge>
              )}
              <Button
                onClick={handleRefresh}
                disabled={isLoading}
                className="flex items-center gap-2"
                data-testid="refresh-health-button"
              >
                <Activity className="h-4 w-4" />
                Check Health
              </Button>
            </div>
          }
        />

        {/* Health Summary */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm text-gray-600">Total Feeds</p>
                    <p className="text-2xl font-bold">{summary.total_feeds}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">Healthy Feeds</p>
                    <p className="text-2xl font-bold">
                      {summary.healthy_feeds}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <HeartPulse className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">Health Score</p>
                    <p className="text-2xl font-bold">
                      {summary.health_percentage}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm text-gray-600">Avg Response</p>
                    <p className="text-2xl font-bold">
                      {(() => {
                        const validTimes = feeds
                          .filter((f) => f.response_time_ms !== null)
                          .map((f) => f.response_time_ms as number);
                        const avgTime =
                          validTimes.length > 0
                            ? validTimes.reduce((a, b) => a + b, 0) /
                              validTimes.length
                            : 0;
                        return formatResponseTime(avgTime);
                      })()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Feed Health List */}
        <Card>
          <CardHeader>
            <CardTitle>Feed Status Details</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-500">
                <XCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Error loading feed health data</p>
                <p className="text-sm">{error}</p>
                <Button
                  variant="outline"
                  onClick={handleRefresh}
                  className="mt-4 flex items-center gap-2"
                >
                  <Activity className="h-4 w-4" />
                  Try Again
                </Button>
              </div>
            ) : feeds.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <HeartPulse className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No feed health data available</p>
                <p className="text-sm mb-4">
                  Run a health check to see feed status
                </p>
                <Button
                  onClick={handleRefresh}
                  className="flex items-center gap-2"
                >
                  <Activity className="h-4 w-4" />
                  Check Feed Health
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {feeds.map((feed) => (
                  <div
                    key={feed.feed_id}
                    className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getStatusIcon(feed.status)}
                          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                            {feed.feed_name}
                          </h3>
                          {getStatusBadge(feed.status)}
                          {!feed.is_active && (
                            <Badge variant="secondary">Inactive</Badge>
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400">
                          <div>
                            <span className="font-medium">URL:</span>
                            <p className="truncate">{feed.url}</p>
                          </div>
                          <div>
                            <span className="font-medium">Response Time:</span>
                            <p>{formatResponseTime(feed.response_time_ms)}</p>
                          </div>
                          <div>
                            <span className="font-medium">Last Checked:</span>
                            <p>{formatLastChecked(feed.last_checked)}</p>
                          </div>
                        </div>

                        {feed.error_message && (
                          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-700 dark:text-red-300">
                            <strong>Error:</strong> {feed.error_message}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Progress Modal for Health Checks */}
        <ProgressModal
          isOpen={isProgressModalOpen}
          onClose={handleProgressClose}
          onComplete={handleProgressComplete}
        />
      </div>
    </DashboardLayout>
  );
};
