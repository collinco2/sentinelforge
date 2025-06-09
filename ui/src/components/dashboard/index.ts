/**
 * Dashboard Components - Reusable components for SentinelForge dashboards
 *
 * This module exports all dashboard-related components for easy importing
 * and consistent usage across different dashboard pages.
 */

// Core dashboard components
export { default as StatWidget, StatWidgetGrid } from "./StatWidget";
export type { StatWidgetProps, StatWidgetGridProps } from "./StatWidget";

export {
  default as FeedCard,
  FeedHealthItem,
  IOCItem,
  UploadItem,
} from "./FeedCard";
export type {
  FeedCardProps,
  FeedHealthItemProps,
  IOCItemProps,
  UploadItemProps,
} from "./FeedCard";

export {
  default as DashboardSection,
  DashboardContainer,
  DashboardHeader,
  DashboardGrid,
  DashboardCard,
  DashboardMetrics,
} from "./DashboardSection";
export type {
  DashboardSectionProps,
  DashboardContainerProps,
  DashboardHeaderProps,
  DashboardGridProps,
  DashboardCardProps,
  DashboardMetricsProps,
} from "./DashboardSection";

// Status and badge components
export { StatusBadge, ImportStatusBadge, SeverityBadge } from "./StatusBadge";
export type { StatusVariant, ImportStatus } from "./StatusBadge";

/**
 * Common dashboard patterns and utilities
 */
export const dashboardUtils = {
  /**
   * Format time ago string
   */
  formatTimeAgo: (timestamp: string): string => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  },

  /**
   * Format large numbers with locale-specific formatting
   */
  formatNumber: (value: number): string => {
    return value.toLocaleString();
  },

  /**
   * Calculate percentage with optional decimal places
   */
  formatPercentage: (value: number, decimals: number = 1): string => {
    return `${value.toFixed(decimals)}%`;
  },

  /**
   * Get trend indicator based on current vs previous value
   */
  getTrend: (
    current: number,
    previous: number,
  ): { value: string; isPositive: boolean } => {
    const diff = current - previous;
    const percentage = previous === 0 ? 0 : (diff / previous) * 100;
    const isPositive = diff > 0;
    const sign = isPositive ? "+" : "";

    return {
      value: `${sign}${percentage.toFixed(1)}%`,
      isPositive,
    };
  },

  /**
   * Common dashboard breakpoints
   */
  breakpoints: {
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },

  /**
   * Common dashboard spacing
   */
  spacing: {
    xs: "0.5rem",
    sm: "1rem",
    md: "1.5rem",
    lg: "2rem",
    xl: "3rem",
  },
};

/**
 * Dashboard component presets for common layouts
 */
export const dashboardPresets = {
  /**
   * Standard metrics grid (4 columns on desktop, responsive)
   */
  metricsGrid: {
    columns: 4 as const,
    gap: "md" as const,
  },

  /**
   * Two-column content layout
   */
  contentGrid: {
    columns: 2 as const,
    gap: "lg" as const,
  },

  /**
   * Single column layout for detailed content
   */
  singleColumn: {
    columns: 1 as const,
    gap: "md" as const,
  },

  /**
   * Three-column layout for balanced content
   */
  balancedGrid: {
    columns: 3 as const,
    gap: "md" as const,
  },
};
