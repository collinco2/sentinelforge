/**
 * 🧭 PageHeader Component - Reusable page header with breadcrumbs
 *
 * Provides consistent page headers across SentinelForge with:
 * - Breadcrumb navigation for context
 * - Page title and description
 * - Optional action buttons
 * - Responsive design
 *
 * Features:
 * - Static breadcrumbs for navigation context
 * - Consistent styling with Tailwind classes
 * - Icon support for visual hierarchy
 * - Mobile-responsive layout
 */

import React from "react";
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "./ui/breadcrumb";
import { cn } from "../lib/utils";

interface PageBreadcrumbItem {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  /** Main page title */
  title: string;
  /** Optional page description */
  description?: string;
  /** Breadcrumb items for navigation context */
  breadcrumbs?: PageBreadcrumbItem[];
  /** Optional icon component */
  icon?: React.ComponentType<{ className?: string }>;
  /** Optional action buttons or content */
  actions?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  breadcrumbs = [],
  icon: Icon,
  actions,
  className,
}) => {
  return (
    <div className={cn("space-y-4", className)}>
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <Breadcrumb>
          <BreadcrumbList>
            {breadcrumbs.map((item, index) => (
              <React.Fragment key={index}>
                <BreadcrumbItem>
                  {index === breadcrumbs.length - 1 ? (
                    <BreadcrumbPage className="text-gray-600 dark:text-gray-400 text-sm">
                      {item.label}
                    </BreadcrumbPage>
                  ) : (
                    <span className="text-gray-600 dark:text-gray-400 text-sm">
                      {item.label}
                    </span>
                  )}
                </BreadcrumbItem>
                {index < breadcrumbs.length - 1 && (
                  <BreadcrumbSeparator className="text-gray-400" />
                )}
              </React.Fragment>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
      )}

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {Icon && <Icon className="h-8 w-8 text-blue-600" />}
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              {title}
            </h1>
            {description && (
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {description}
              </p>
            )}
          </div>
        </div>

        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
};

/**
 * Predefined breadcrumb configurations for common SentinelForge pages
 */
export const BREADCRUMB_CONFIGS = {
  // Settings page breadcrumbs
  SETTINGS_API_TOKENS: [
    { label: "Settings" },
    { label: "API & Tokens" },
  ] as PageBreadcrumbItem[],
  SETTINGS_UI_PREFERENCES: [
    { label: "Settings" },
    { label: "UI Preferences" },
  ] as PageBreadcrumbItem[],
  SETTINGS_NOTIFICATIONS: [
    { label: "Settings" },
    { label: "Notifications" },
  ] as PageBreadcrumbItem[],
  SETTINGS_SECURITY: [
    { label: "Settings" },
    { label: "Security" },
  ] as PageBreadcrumbItem[],

  // Feed management breadcrumbs
  FEEDS_MANAGEMENT: [
    { label: "Feeds" },
    { label: "Management" },
  ] as PageBreadcrumbItem[],
  FEEDS_UPLOAD: [
    { label: "Feeds" },
    { label: "Upload" },
  ] as PageBreadcrumbItem[],
  FEEDS_HEALTH: [
    { label: "Feeds" },
    { label: "Health Status" },
  ] as PageBreadcrumbItem[],

  // IOC management breadcrumbs
  IOC_MANAGEMENT: [
    { label: "IOCs" },
    { label: "Management" },
  ] as PageBreadcrumbItem[],
  IOC_ANALYSIS: [
    { label: "IOCs" },
    { label: "Analysis" },
  ] as PageBreadcrumbItem[],

  // Alert management breadcrumbs
  ALERTS_OVERVIEW: [
    { label: "Alerts" },
    { label: "Overview" },
  ] as PageBreadcrumbItem[],
  ALERTS_TIMELINE: [
    { label: "Alerts" },
    { label: "Timeline" },
  ] as PageBreadcrumbItem[],

  // Reports breadcrumbs
  REPORTS_OVERVIEW: [
    { label: "Reports" },
    { label: "Overview" },
  ] as PageBreadcrumbItem[],

  // Role management breadcrumbs
  ROLE_MANAGEMENT: [
    { label: "Administration" },
    { label: "Role Management" },
  ] as PageBreadcrumbItem[],
};

/**
 * Hook to get breadcrumb configuration based on current tab or page context
 */
export const useBreadcrumbs = (
  pageType: keyof typeof BREADCRUMB_CONFIGS,
  activeTab?: string,
): PageBreadcrumbItem[] => {
  const baseBreadcrumbs = BREADCRUMB_CONFIGS[pageType];

  // For settings page, update breadcrumb based on active tab
  if (pageType.startsWith("SETTINGS_") && activeTab) {
    const tabBreadcrumbs: Record<string, PageBreadcrumbItem[]> = {
      "api-tokens": BREADCRUMB_CONFIGS.SETTINGS_API_TOKENS,
      "ui-preferences": BREADCRUMB_CONFIGS.SETTINGS_UI_PREFERENCES,
      notifications: BREADCRUMB_CONFIGS.SETTINGS_NOTIFICATIONS,
      security: BREADCRUMB_CONFIGS.SETTINGS_SECURITY,
    };

    return tabBreadcrumbs[activeTab] || baseBreadcrumbs;
  }

  return baseBreadcrumbs;
};
