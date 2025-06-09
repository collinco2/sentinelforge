import React from "react";
import { Badge } from "./ui/badge";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  Shield,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Info,
} from "lucide-react";

export type StatusVariant =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "success"
  | "warning"
  | "error"
  | "info"
  | "pending"
  | "unknown";

export type ImportStatus = "success" | "partial" | "failed" | "pending";

interface StatusBadgeProps {
  variant: StatusVariant;
  children?: React.ReactNode;
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface ImportStatusBadgeProps {
  status: ImportStatus;
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

// Severity/Status Badge Component
export function StatusBadge({
  variant,
  children,
  showIcon = true,
  size = "md",
  className,
}: StatusBadgeProps) {
  const getVariantStyles = (variant: StatusVariant) => {
    switch (variant) {
      case "critical":
        return {
          className:
            "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800",
          icon: AlertTriangle,
        };
      case "high":
        return {
          className:
            "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/20 dark:text-orange-400 dark:border-orange-800",
          icon: Shield,
        };
      case "medium":
        return {
          className:
            "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800",
          icon: AlertCircle,
        };
      case "low":
        return {
          className:
            "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800",
          icon: Info,
        };
      case "success":
        return {
          className:
            "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800",
          icon: CheckCircle,
        };
      case "warning":
        return {
          className:
            "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800",
          icon: AlertTriangle,
        };
      case "error":
        return {
          className:
            "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800",
          icon: XCircle,
        };
      case "info":
        return {
          className:
            "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800",
          icon: Info,
        };
      case "pending":
        return {
          className:
            "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/20 dark:text-gray-400 dark:border-gray-800",
          icon: Clock,
        };
      default:
        return {
          className: "bg-muted text-muted-foreground border-border",
          icon: Info,
        };
    }
  };

  const getSizeStyles = (size: "sm" | "md" | "lg") => {
    switch (size) {
      case "sm":
        return "text-xs px-2 py-0.5";
      case "lg":
        return "text-sm px-3 py-1.5";
      default:
        return "text-xs px-2.5 py-1";
    }
  };

  const getIconSize = (size: "sm" | "md" | "lg") => {
    switch (size) {
      case "sm":
        return "h-3 w-3";
      case "lg":
        return "h-4 w-4";
      default:
        return "h-3.5 w-3.5";
    }
  };

  const { className: variantClassName, icon: Icon } = getVariantStyles(variant);
  const sizeClassName = getSizeStyles(size);
  const iconSizeClassName = getIconSize(size);

  return (
    <Badge
      className={cn(
        "inline-flex items-center gap-1.5 font-medium border",
        variantClassName,
        sizeClassName,
        className,
      )}
    >
      {showIcon && <Icon className={iconSizeClassName} />}
      {children || variant.charAt(0).toUpperCase() + variant.slice(1)}
    </Badge>
  );
}

// Import Status Badge Component
export function ImportStatusBadge({
  status,
  showIcon = true,
  size = "md",
  className,
}: ImportStatusBadgeProps) {
  const getStatusConfig = (status: ImportStatus) => {
    switch (status) {
      case "success":
        return {
          variant: "success" as StatusVariant,
          label: "Success",
        };
      case "partial":
        return {
          variant: "warning" as StatusVariant,
          label: "Partial",
        };
      case "failed":
        return {
          variant: "error" as StatusVariant,
          label: "Failed",
        };
      case "pending":
        return {
          variant: "pending" as StatusVariant,
          label: "Pending",
        };
      default:
        return {
          variant: "unknown" as StatusVariant,
          label: status,
        };
    }
  };

  const { variant, label } = getStatusConfig(status);

  return (
    <StatusBadge
      variant={variant}
      showIcon={showIcon}
      size={size}
      className={className}
    >
      {label}
    </StatusBadge>
  );
}

// Severity Badge (alias for StatusBadge with severity-specific variants)
export function SeverityBadge({
  severity,
  showIcon = true,
  size = "md",
  className,
}: {
  severity: "critical" | "high" | "medium" | "low";
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  return (
    <StatusBadge
      variant={severity}
      showIcon={showIcon}
      size={size}
      className={className}
    />
  );
}
