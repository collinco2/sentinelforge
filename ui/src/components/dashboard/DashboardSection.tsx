import React from "react";
import { cn } from "@/lib/utils";

export interface DashboardSectionProps {
  children: React.ReactNode;
  className?: string;
  columns?: 1 | 2 | 3 | 4;
  gap?: "sm" | "md" | "lg";
  title?: string;
  description?: string;
}

/**
 * DashboardSection - Layout container for dashboard content
 *
 * Features:
 * - Responsive grid layout with configurable columns
 * - Customizable gap spacing
 * - Optional section title and description
 * - Full dark mode support
 * - Flexible content arrangement
 */
export function DashboardSection({
  children,
  className,
  columns = 2,
  gap = "md",
  title,
  description,
}: DashboardSectionProps) {
  const getGridCols = (cols: number) => {
    switch (cols) {
      case 1:
        return "grid-cols-1";
      case 2:
        return "grid-cols-1 lg:grid-cols-2";
      case 3:
        return "grid-cols-1 md:grid-cols-2 lg:grid-cols-3";
      case 4:
        return "grid-cols-1 md:grid-cols-2 lg:grid-cols-4";
      default:
        return "grid-cols-1 lg:grid-cols-2";
    }
  };

  const getGapSize = (gapSize: "sm" | "md" | "lg") => {
    switch (gapSize) {
      case "sm":
        return "gap-3";
      case "lg":
        return "gap-8";
      default:
        return "gap-6";
    }
  };

  return (
    <section className={cn("space-y-4", className)}>
      {(title || description) && (
        <div className="space-y-2">
          {title && (
            <h2 className="text-2xl md:text-3xl font-bold text-foreground dark:text-foreground">
              {title}
            </h2>
          )}
          {description && (
            <p className="text-muted-foreground dark:text-muted-foreground">
              {description}
            </p>
          )}
        </div>
      )}

      <div className={cn("grid", getGridCols(columns), getGapSize(gap))}>
        {children}
      </div>
    </section>
  );
}

/**
 * DashboardContainer - Main container for dashboard pages
 */
export interface DashboardContainerProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
}

export function DashboardContainer({
  children,
  className,
  maxWidth = "2xl",
}: DashboardContainerProps) {
  const getMaxWidth = (size: string) => {
    switch (size) {
      case "sm":
        return "max-w-3xl";
      case "md":
        return "max-w-5xl";
      case "lg":
        return "max-w-6xl";
      case "xl":
        return "max-w-7xl";
      case "2xl":
        return "max-w-7xl";
      case "full":
        return "max-w-full";
      default:
        return "max-w-7xl";
    }
  };

  return (
    <div
      className={cn(
        "min-h-screen bg-background/95 dark:bg-background/95 p-4 md:p-6 transition-colors duration-200",
        className,
      )}
    >
      <div className={cn("mx-auto space-y-6", getMaxWidth(maxWidth))}>
        {children}
      </div>
    </div>
  );
}

/**
 * DashboardHeader - Header section for dashboard pages
 */
export interface DashboardHeaderProps {
  title?: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function DashboardHeader({
  title,
  description,
  actions,
  className,
}: DashboardHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4",
        className,
      )}
    >
      <div className="space-y-1">
        {title && (
          <h1 className="text-3xl md:text-4xl font-bold text-foreground dark:text-foreground">
            {title}
          </h1>
        )}
        {description && (
          <p className="text-lg text-muted-foreground dark:text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

/**
 * DashboardGrid - Flexible grid layout for dashboard content
 */
export interface DashboardGridProps {
  children: React.ReactNode;
  className?: string;
  responsive?: boolean;
  minItemWidth?: string;
  gap?: "sm" | "md" | "lg";
}

export function DashboardGrid({
  children,
  className,
  responsive = true,
  minItemWidth = "300px",
  gap = "md",
}: DashboardGridProps) {
  const getGapSize = (gapSize: "sm" | "md" | "lg") => {
    switch (gapSize) {
      case "sm":
        return "gap-3";
      case "lg":
        return "gap-8";
      default:
        return "gap-6";
    }
  };

  const gridStyle = responsive
    ? { gridTemplateColumns: `repeat(auto-fit, minmax(${minItemWidth}, 1fr))` }
    : undefined;

  return (
    <div
      className={cn(
        "grid",
        responsive ? "" : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
        getGapSize(gap),
        className,
      )}
      style={gridStyle}
    >
      {children}
    </div>
  );
}

/**
 * DashboardCard - Basic card wrapper for dashboard content
 */
export interface DashboardCardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
  hover?: boolean;
}

export function DashboardCard({
  children,
  className,
  padding = "md",
  hover = false,
}: DashboardCardProps) {
  const getPadding = (size: "sm" | "md" | "lg") => {
    switch (size) {
      case "sm":
        return "p-3";
      case "lg":
        return "p-6 md:p-8";
      default:
        return "p-4 md:p-6";
    }
  };

  return (
    <div
      className={cn(
        "rounded-2xl shadow-sm border border-border/50 dark:border-border/50 bg-card dark:bg-card transition-colors duration-200",
        getPadding(padding),
        hover &&
          "hover:shadow-md hover:border-border dark:hover:border-border transition-all duration-200",
        className,
      )}
    >
      {children}
    </div>
  );
}

/**
 * DashboardMetrics - Container for metric widgets
 */
export interface DashboardMetricsProps {
  children: React.ReactNode;
  className?: string;
  columns?: 2 | 3 | 4;
}

export function DashboardMetrics({
  children,
  className,
  columns = 4,
}: DashboardMetricsProps) {
  const getGridCols = (cols: number) => {
    switch (cols) {
      case 2:
        return "grid-cols-1 md:grid-cols-2";
      case 3:
        return "grid-cols-1 md:grid-cols-2 lg:grid-cols-3";
      case 4:
        return "grid-cols-1 md:grid-cols-2 lg:grid-cols-4";
      default:
        return "grid-cols-1 md:grid-cols-2 lg:grid-cols-4";
    }
  };

  return (
    <div className={cn("grid gap-4 md:gap-6", getGridCols(columns), className)}>
      {children}
    </div>
  );
}

export default DashboardSection;
