import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

export interface StatWidgetProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  iconColor?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  className?: string;
  size?: "sm" | "md" | "lg";
}

/**
 * StatWidget - Reusable statistics card component
 *
 * Features:
 * - Displays a key metric with title, value, and optional description
 * - Supports icons with customizable colors
 * - Optional trend indicator with positive/negative styling
 * - Responsive sizing (sm, md, lg)
 * - Full dark mode support
 * - Accessible with proper ARIA labels
 */
export function StatWidget({
  title,
  value,
  description,
  icon: Icon,
  iconColor = "text-muted-foreground dark:text-muted-foreground",
  trend,
  className,
  size = "md",
}: StatWidgetProps) {
  const getSizeStyles = (size: "sm" | "md" | "lg") => {
    switch (size) {
      case "sm":
        return {
          card: "rounded-xl",
          header: "p-3 pb-2",
          content: "p-3 pt-0",
          title: "text-xs font-medium",
          value: "text-lg font-bold",
          description: "text-xs",
          icon: "h-4 w-4",
        };
      case "lg":
        return {
          card: "rounded-2xl",
          header: "p-6 pb-3",
          content: "p-6 pt-0",
          title: "text-base font-medium",
          value: "text-3xl md:text-4xl font-bold",
          description: "text-sm",
          icon: "h-6 w-6",
        };
      default: // md
        return {
          card: "rounded-2xl",
          header: "p-4 md:p-6 pb-2",
          content: "p-4 md:p-6 pt-0",
          title: "text-sm font-medium",
          value: "text-2xl md:text-3xl font-bold",
          description: "text-xs",
          icon: "h-5 w-5",
        };
    }
  };

  const styles = getSizeStyles(size);

  const getTrendColor = (isPositive?: boolean) => {
    if (isPositive === undefined)
      return "text-muted-foreground dark:text-muted-foreground";
    return isPositive
      ? "text-green-600 dark:text-green-400"
      : "text-red-600 dark:text-red-400";
  };

  return (
    <Card
      className={cn(
        styles.card,
        "shadow-sm border-border/50 dark:border-border/50 bg-card dark:bg-card transition-colors duration-200",
        className,
      )}
    >
      <CardHeader
        className={cn(
          styles.header,
          "flex flex-row items-center justify-between space-y-0",
        )}
      >
        <CardTitle
          className={cn(
            styles.title,
            "text-muted-foreground dark:text-muted-foreground",
          )}
        >
          {title}
        </CardTitle>
        <Icon className={cn(styles.icon, iconColor)} aria-hidden="true" />
      </CardHeader>
      <CardContent
        className={cn(
          styles.content,
          "text-card-foreground dark:text-card-foreground",
        )}
      >
        <div className={cn(styles.value, "mb-1")}>
          {typeof value === "number" ? value.toLocaleString() : value}
        </div>

        {(description || trend) && (
          <div className="flex items-center justify-between">
            {description && (
              <p
                className={cn(
                  styles.description,
                  "text-muted-foreground dark:text-muted-foreground",
                )}
              >
                {description}
              </p>
            )}

            {trend && (
              <p
                className={cn(
                  styles.description,
                  "font-medium",
                  getTrendColor(trend.isPositive),
                )}
              >
                {trend.value}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * StatWidgetGrid - Container for multiple StatWidget components
 */
export interface StatWidgetGridProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3 | 4;
  className?: string;
}

export function StatWidgetGrid({
  children,
  columns = 4,
  className,
}: StatWidgetGridProps) {
  const getGridCols = (cols: number) => {
    switch (cols) {
      case 1:
        return "grid-cols-1";
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

export default StatWidget;
