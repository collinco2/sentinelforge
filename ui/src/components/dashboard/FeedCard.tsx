import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { cn } from "@/lib/utils";
import { LucideIcon, ExternalLink, AlertCircle } from "lucide-react";
import { StatusBadge, ImportStatusBadge, SeverityBadge } from "./StatusBadge";

export interface FeedCardProps {
  title: string;
  icon: LucideIcon;
  iconColor?: string;
  onViewAll?: () => void;
  viewAllLabel?: string;
  className?: string;
  children: React.ReactNode;
  emptyState?: {
    icon: LucideIcon;
    message: string;
  };
  isLoading?: boolean;
  error?: string;
}

/**
 * FeedCard - Reusable card component for feed-related content
 *
 * Features:
 * - Consistent header with title, icon, and optional "View All" button
 * - Support for loading states and error handling
 * - Empty state display with custom icon and message
 * - Full dark mode support
 * - Responsive design
 */
export function FeedCard({
  title,
  icon: Icon,
  iconColor = "text-muted-foreground dark:text-muted-foreground",
  onViewAll,
  viewAllLabel = "View All",
  className,
  children,
  emptyState,
  isLoading = false,
  error,
}: FeedCardProps) {
  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center py-8 text-center">
          <div className="space-y-2">
            <AlertCircle className="h-8 w-8 mx-auto text-red-500 dark:text-red-400" />
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        </div>
      );
    }

    if (emptyState && React.Children.count(children) === 0) {
      const EmptyIcon = emptyState.icon;
      return (
        <div className="text-center py-8 text-muted-foreground dark:text-muted-foreground">
          <EmptyIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">{emptyState.message}</p>
        </div>
      );
    }

    return children;
  };

  return (
    <Card
      className={cn(
        "rounded-2xl shadow-sm border-border/50 dark:border-border/50 bg-card dark:bg-card transition-colors duration-200",
        className,
      )}
    >
      <CardHeader className="p-4 md:p-6 flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-xl md:text-2xl font-semibold flex items-center gap-2 text-card-foreground dark:text-card-foreground">
          <Icon className={cn("h-6 w-6", iconColor)} />
          {title}
        </CardTitle>
        {onViewAll && (
          <Button
            variant="outline"
            size="sm"
            onClick={onViewAll}
            className="flex items-center gap-2 text-sm border-border dark:border-border hover:bg-muted dark:hover:bg-muted transition-colors duration-200"
          >
            <ExternalLink className="h-4 w-4" />
            {viewAllLabel}
          </Button>
        )}
      </CardHeader>
      <CardContent className="p-4 md:p-6 pt-0 text-card-foreground dark:text-card-foreground">
        {renderContent()}
      </CardContent>
    </Card>
  );
}

/**
 * FeedHealthItem - Component for displaying individual feed health status
 */
export interface FeedHealthItemProps {
  feedName: string;
  status:
    | "ok"
    | "timeout"
    | "unauthorized"
    | "rate_limited"
    | "unreachable"
    | "server_error"
    | "unknown";
  lastChecked?: string;
  className?: string;
}

export function FeedHealthItem({
  feedName,
  status,
  lastChecked,
  className,
}: FeedHealthItemProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case "ok":
        return "success";
      case "timeout":
      case "unauthorized":
      case "rate_limited":
        return "warning";
      case "unreachable":
      case "server_error":
        return "error";
      default:
        return "pending";
    }
  };

  return (
    <div
      className={cn(
        "flex items-center justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200",
        className,
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <span className="font-medium text-foreground dark:text-foreground truncate">
            {feedName}
          </span>
          <StatusBadge variant={getStatusVariant(status) as any} size="sm" />
        </div>
        {lastChecked && (
          <p className="text-xs text-muted-foreground dark:text-muted-foreground">
            Last checked: {lastChecked}
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * IOCItem - Component for displaying individual IOC information
 */
export interface IOCItemProps {
  value: string;
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  feedName: string;
  timestamp: string;
  className?: string;
}

export function IOCItem({
  value,
  type,
  severity,
  feedName,
  timestamp,
  className,
}: IOCItemProps) {
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

  return (
    <div
      className={cn(
        "flex items-center justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200",
        className,
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-2">
          <code className="text-sm font-mono bg-background dark:bg-background px-2 py-1 rounded-md truncate border border-border dark:border-border">
            {value}
          </code>
          <SeverityBadge severity={severity} size="sm" />
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground dark:text-muted-foreground">
          <span className="font-medium">{type}</span>
          <span>•</span>
          <span>{feedName}</span>
          <span>•</span>
          <span>{formatTimeAgo(timestamp)}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * UploadItem - Component for displaying upload/import information
 */
export interface UploadItemProps {
  feedName: string;
  status: "success" | "partial" | "failed" | "pending";
  importedCount: number;
  errorCount?: number;
  timestamp: string;
  className?: string;
}

export function UploadItem({
  feedName,
  status,
  importedCount,
  errorCount = 0,
  timestamp,
  className,
}: UploadItemProps) {
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

  return (
    <div
      className={cn(
        "flex items-center justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200",
        className,
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-2">
          <span className="font-medium truncate text-foreground dark:text-foreground">
            {feedName}
          </span>
          <ImportStatusBadge status={status} size="sm" />
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground dark:text-muted-foreground">
          <span className="font-medium">{importedCount} imported</span>
          {errorCount > 0 && (
            <>
              <span>•</span>
              <span className="text-red-600 dark:text-red-400 font-medium">
                {errorCount} errors
              </span>
            </>
          )}
          <span>•</span>
          <span>{formatTimeAgo(timestamp)}</span>
        </div>
      </div>
    </div>
  );
}

export default FeedCard;
