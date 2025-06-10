import React, { useState, useEffect, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Progress } from "../ui/progress";
import { Badge } from "../ui/badge";
import { Alert, AlertDescription } from "../ui/alert";
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Loader2,
  X,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface FeedHealthResult {
  feed_id: number;
  feed_name: string;
  url: string;
  status:
    | "ok"
    | "timeout"
    | "unauthorized"
    | "rate_limited"
    | "unreachable"
    | "server_error"
    | "unknown";
  http_code?: number;
  response_time_ms: number;
  error_message?: string;
  last_checked: string;
  is_active: boolean;
}

export interface ProgressData {
  status: "starting" | "running" | "completed" | "cancelled" | "error";
  completed_feeds: number;
  total_feeds: number;
  current_feed?: {
    name: string;
    url: string;
    index: number;
  };
  estimated_completion?: number;
}

export interface ProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (results: FeedHealthResult[]) => void;
  feedId?: number; // Optional: check specific feed only
}

/**
 * ProgressModal - Real-time progress indicator for feed health checks
 *
 * Features:
 * - Server-Sent Events for real-time progress updates
 * - Visual progress bar with percentage and ETA
 * - Live feed-by-feed status updates
 * - Individual feed results with status icons
 * - Cancel functionality
 * - Error handling and retry options
 * - Mobile-responsive design
 */
export const ProgressModal: React.FC<ProgressModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  feedId,
}) => {
  const [progress, setProgress] = useState<ProgressData>({
    status: "starting",
    completed_feeds: 0,
    total_feeds: 0,
  });
  const [results, setResults] = useState<FeedHealthResult[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Start health check when modal opens
  useEffect(() => {
    if (isOpen && !sessionId) {
      startHealthCheck();
    }
  }, [isOpen, sessionId]);

  // Cleanup on unmount or close
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const startHealthCheck = async () => {
    try {
      // Check if we should use demo mode
      const useDemo = localStorage.getItem("healthCheckDemo") === "true";
      const endpoint = useDemo
        ? "/api/feeds/health/demo"
        : "/api/feeds/health/start";

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify(feedId ? { feed_id: feedId } : {}),
      });

      if (!response.ok) {
        throw new Error("Failed to start health check");
      }

      const data = await response.json();
      setSessionId(data.session_id);

      // Start listening for progress updates
      connectToProgressStream(data.session_id, useDemo);
    } catch (error) {
      console.error("Error starting health check:", error);
      setErrors((prev) => [...prev, "Failed to start health check"]);
      setProgress((prev) => ({ ...prev, status: "error" }));
    }
  };

  const connectToProgressStream = (
    sessionId: string,
    useDemo: boolean = false,
  ) => {
    const progressUrl = useDemo
      ? `/api/feeds/health/demo/progress/${sessionId}`
      : `/api/feeds/health/progress/${sessionId}`;

    const eventSource = new EventSource(progressUrl, {
      withCredentials: true,
    });

    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "connected":
            setIsConnected(true);
            break;

          case "progress":
            setProgress({
              status: data.status,
              completed_feeds: data.completed_feeds,
              total_feeds: data.total_feeds,
              current_feed: data.current_feed,
              estimated_completion: data.estimated_completion,
            });
            break;

          case "feed_result":
            setResults((prev) => [...prev, data.result]);
            break;

          case "error":
            setErrors((prev) => [...prev, data.error]);
            break;

          case "finished":
            setProgress((prev) => ({ ...prev, status: data.status }));
            setIsConnected(false);
            eventSource.close();

            if (data.status === "completed" && onComplete) {
              onComplete(results);
            }
            break;
        }
      } catch (error) {
        console.error("Error parsing SSE data:", error);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      setErrors((prev) => [...prev, "Connection to progress stream lost"]);
    };
  };

  const cancelHealthCheck = async () => {
    if (!sessionId) return;

    try {
      await fetch(`/api/feeds/health/cancel/${sessionId}`, {
        method: "POST",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setProgress((prev) => ({ ...prev, status: "cancelled" }));
      setIsConnected(false);
    } catch (error) {
      console.error("Error cancelling health check:", error);
    }
  };

  const handleClose = () => {
    if (progress.status === "running") {
      cancelHealthCheck();
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Reset state
    setProgress({ status: "starting", completed_feeds: 0, total_feeds: 0 });
    setResults([]);
    setErrors([]);
    setSessionId(null);
    setIsConnected(false);

    onClose();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "ok":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "timeout":
      case "unauthorized":
      case "rate_limited":
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case "unreachable":
      case "server_error":
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      ok: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      timeout:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      unauthorized:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      rate_limited:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      unreachable: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
      server_error: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
      unknown: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
    };

    return (
      <Badge
        className={cn(
          "text-xs",
          variants[status as keyof typeof variants] || variants.unknown,
        )}
      >
        {status.replace("_", " ")}
      </Badge>
    );
  };

  const progressPercentage =
    progress.total_feeds > 0
      ? Math.round((progress.completed_feeds / progress.total_feeds) * 100)
      : 0;

  const formatETA = (timestamp?: number) => {
    if (!timestamp) return null;

    const now = Date.now() / 1000;
    const secondsRemaining = Math.max(0, timestamp - now);

    if (secondsRemaining < 60) {
      return `${Math.round(secondsRemaining)}s remaining`;
    } else {
      const minutes = Math.round(secondsRemaining / 60);
      return `${minutes}m remaining`;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            Feed Health Check Progress
            {!isConnected && progress.status === "running" && (
              <Badge variant="outline" className="text-xs">
                Reconnecting...
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Progress Overview */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">
                Progress: {progress.completed_feeds} / {progress.total_feeds}{" "}
                feeds
              </span>
              <span className="text-muted-foreground">
                {progressPercentage}%
              </span>
            </div>

            <Progress value={progressPercentage} className="h-2" />

            {progress.estimated_completion && (
              <div className="text-xs text-muted-foreground text-center">
                {formatETA(progress.estimated_completion)}
              </div>
            )}
          </div>

          {/* Current Feed Being Checked */}
          {progress.current_feed && (
            <Alert>
              <Loader2 className="h-4 w-4 animate-spin" />
              <AlertDescription>
                <div className="font-medium">
                  Checking feed {progress.current_feed.index} of{" "}
                  {progress.total_feeds}
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  {progress.current_feed.name}
                </div>
                <div className="text-xs text-muted-foreground truncate">
                  {progress.current_feed.url}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Results List */}
          {results.length > 0 && (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              <h4 className="font-medium text-sm">Completed Checks:</h4>
              {results.map((result) => (
                <div
                  key={result.feed_id}
                  className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {getStatusIcon(result.status)}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {result.feed_name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {result.response_time_ms}ms
                        {result.error_message && ` • ${result.error_message}`}
                      </div>
                    </div>
                  </div>
                  {getStatusBadge(result.status)}
                </div>
              ))}
            </div>
          )}

          {/* Errors */}
          {errors.length > 0 && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="font-medium">Errors occurred:</div>
                <ul className="mt-1 text-sm list-disc list-inside">
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          {progress.status === "running" ? (
            <Button variant="outline" onClick={cancelHealthCheck}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          ) : (
            <Button onClick={handleClose}>
              {progress.status === "completed" ? "Done" : "Close"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ProgressModal;
