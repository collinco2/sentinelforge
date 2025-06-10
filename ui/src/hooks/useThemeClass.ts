/**
 * 🎨 useThemeClass Hook - Centralized SentinelForge Theme Management
 *
 * Provides consistent theme classes and utilities for both light and dark themes:
 * - Senior UI Designer approved color tokens
 * - WCAG 2.1 compliant readability enhancements
 * - Component-specific styling utilities
 * - Complete light and dark mode support
 * - Severity-based color coding system
 * - Automatic theme detection and responsive styling
 */

import { useCallback } from "react";
import { cn } from "@/lib/utils";
import { useTheme } from "./useTheme";

export interface ThemeClasses {
  // Layout classes
  background: string;
  backgroundMuted: string;
  card: string;
  panel: string;
  modal: string;

  // Text classes
  textPrimary: string;
  textMuted: string;
  textLow: string;

  // Interactive classes
  border: string;
  ring: string;

  // Button variants
  buttonPrimary: string;
  buttonSecondary: string;
  buttonGhost: string;
  buttonOutline: string;

  // Input classes
  input: string;
  textarea: string;
  select: string;

  // Sidebar classes
  sidebar: string;
  sidebarItem: string;
  sidebarItemActive: string;

  // Table classes
  table: string;
  tableHeader: string;
  tableRow: string;
  tableCell: string;

  // Tag classes
  tag: string;

  // Chart classes
  chartAccent: string;
  chartBackground: string;
}

/**
 * Hook to get SentinelForge theme classes with light/dark mode support
 */
export function useThemeClass(): ThemeClasses {
  const { actualTheme } = useTheme();

  const getThemeClasses = useCallback((): ThemeClasses => {
    const isDark = actualTheme === "dark";

    return {
      // Layout classes with responsive light/dark styling
      background: isDark
        ? "bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white"
        : "bg-gradient-to-br from-gray-50 via-white to-gray-50 text-slate-900",
      backgroundMuted: isDark
        ? "bg-slate-800/30"
        : "bg-gray-50/50",
      card: isDark
        ? "bg-slate-800/50 border-slate-700 backdrop-blur-sm text-white rounded-2xl shadow-xl"
        : "bg-white border-gray-200 text-slate-900 rounded-2xl shadow-sm",
      panel: isDark
        ? "bg-slate-800/50 border-slate-700 backdrop-blur-sm text-white rounded-2xl"
        : "bg-white border-gray-200 text-slate-900 rounded-2xl",
      modal: isDark
        ? "bg-slate-800/50 border-slate-700 text-white rounded-2xl shadow-xl backdrop-blur-sm"
        : "bg-white border-gray-200 text-slate-900 rounded-2xl shadow-lg",

      // Text classes with responsive light/dark styling
      textPrimary: isDark ? "text-white" : "text-slate-900",
      textMuted: isDark ? "text-slate-300" : "text-slate-600",
      textLow: isDark ? "text-slate-400" : "text-slate-500",

      // Interactive classes with theme-aware styling
      border: isDark ? "border-slate-600" : "border-gray-200",
      ring: "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2",

      // Button variants matching sign-in page styling
      buttonPrimary: cn(
        "bg-purple-600 hover:bg-purple-700 text-white rounded-lg",
        "transition-all duration-200 shadow-lg",
        "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
      ),
      buttonSecondary: isDark
        ? cn(
            "bg-slate-700/50 border-slate-600 text-slate-300 hover:text-white",
            "hover:bg-slate-700 transition-all duration-200 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          )
        : cn(
            "bg-gray-100 border-gray-300 text-slate-700 hover:text-slate-900",
            "hover:bg-gray-200 transition-all duration-200 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          ),
      buttonGhost: isDark
        ? cn(
            "text-slate-400 hover:text-white hover:bg-slate-700",
            "transition-all duration-200 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          )
        : cn(
            "text-slate-600 hover:text-slate-900 hover:bg-gray-100",
            "transition-all duration-200 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          ),
      buttonOutline: isDark
        ? cn(
            "border-slate-600 bg-transparent text-slate-300 hover:text-white",
            "hover:bg-slate-700 transition-all duration-200 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          )
        : cn(
            "border-gray-300 bg-transparent text-slate-700 hover:text-slate-900",
            "hover:bg-gray-50 transition-all duration-200 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          ),
      
      // Input classes with responsive light/dark styling
      input: isDark
        ? cn(
            "bg-slate-700/50 border-slate-600 text-white rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
            "placeholder:text-slate-400"
          )
        : cn(
            "bg-white border-gray-300 text-slate-900 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
            "placeholder:text-slate-500"
          ),
      textarea: isDark
        ? cn(
            "bg-slate-700/50 border-slate-600 text-white rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
            "placeholder:text-slate-400 resize-none"
          )
        : cn(
            "bg-white border-gray-300 text-slate-900 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
            "placeholder:text-slate-500 resize-none"
          ),
      select: isDark
        ? cn(
            "bg-slate-700/50 border-slate-600 text-white rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          )
        : cn(
            "bg-white border-gray-300 text-slate-900 rounded-lg",
            "focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          ),

      // Sidebar classes with responsive light/dark styling
      sidebar: isDark
        ? "bg-slate-800/50 border-r border-slate-700 backdrop-blur-sm"
        : "bg-white border-r border-gray-200",
      sidebarItem: isDark
        ? cn(
            "text-slate-400 hover:text-white",
            "hover:bg-slate-700/50 transition-all duration-200",
            "rounded-lg"
          )
        : cn(
            "text-slate-600 hover:text-slate-900",
            "hover:bg-gray-100 transition-all duration-200",
            "rounded-lg"
          ),
      sidebarItemActive: isDark
        ? cn("bg-slate-700/50 text-white", "border-l-4 border-purple-500")
        : cn("bg-purple-50 text-purple-900", "border-l-4 border-purple-500"),

      // Table classes with responsive light/dark styling
      table: isDark
        ? "bg-slate-800/50 border border-slate-700 backdrop-blur-sm rounded-lg"
        : "bg-white border border-gray-200 rounded-lg",
      tableHeader: isDark
        ? "bg-slate-700/50 text-white font-medium"
        : "bg-gray-50 text-slate-900 font-medium",
      tableRow: isDark
        ? "border-b border-slate-700 hover:bg-slate-700/30"
        : "border-b border-gray-200 hover:bg-gray-50",
      tableCell: isDark ? "text-white p-4" : "text-slate-900 p-4",

      // Tag classes with responsive light/dark styling
      tag: isDark
        ? "bg-slate-700/50 text-slate-300 border border-slate-600 rounded-full px-2 py-1 text-xs"
        : "bg-gray-100 text-slate-700 border border-gray-300 rounded-full px-2 py-1 text-xs",

      // Chart classes with responsive light/dark colors
      chartAccent: isDark ? "#7DF9FF" : "#6D4AFF", // chart-primary color for charts
      chartBackground: isDark ? "#1A102E" : "#FFFFFF", // background color for charts
    };
  }, [actualTheme]);

  return getThemeClasses();
}

/**
 * Utility function to get theme-specific colors for charts and visualizations
 * Supports both light and dark themes with WCAG compliant colors
 */
export function getChartTheme(isDark: boolean = true) {
  if (isDark) {
    return {
      background: "#1A102E",
      accent: "#7DF9FF", // chart-primary
      primary: "#6D4AFF",
      secondary: "#A177FF",
      text: "#F4F1FF",
      textMuted: "#C1B3DF",
      textLow: "#9889BA",
      border: "#40305F",
      grid: "#3C314E", // chart-muted
      critical: "#FF4D6D",
      high: "#FFAD60",
      medium: "#FFE062",
      low: "#92FFD0",
    };
  } else {
    return {
      background: "#FFFFFF",
      accent: "#6D4AFF", // primary purple
      primary: "#6D4AFF",
      secondary: "#A177FF",
      text: "#0F172A", // slate-900
      textMuted: "#475569", // slate-600
      textLow: "#94A3B8", // slate-400
      border: "#E2E8F0", // slate-200
      grid: "#F1F5F9", // slate-100
      critical: "#DC2626", // red-600
      high: "#EA580C", // orange-600
      medium: "#CA8A04", // yellow-600
      low: "#059669", // emerald-600
    };
  }
}

/**
 * Utility function to get status badge colors - WCAG compliant with dark mode support
 */
export function getStatusBadgeClass(status: "success" | "warning" | "error" | "info" | "default") {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";

  switch (status) {
    case "success":
      return cn(baseClasses, "bg-low/20 dark:bg-low/20 text-low dark:text-low border border-low/30 dark:border-low/30");
    case "warning":
      return cn(baseClasses, "bg-high/20 dark:bg-high/20 text-high dark:text-high border border-high/30 dark:border-high/30");
    case "error":
      return cn(baseClasses, "bg-critical/20 dark:bg-critical/20 text-critical dark:text-critical border border-critical/30 dark:border-critical/30");
    case "info":
      return cn(baseClasses, "bg-accent/20 dark:bg-accent/20 text-accent dark:text-accent border border-accent/30 dark:border-accent/30");
    default:
      return cn(baseClasses, "bg-tag-bg dark:bg-tag-bg text-tag-text dark:text-tag-text border border-border dark:border-border");
  }
}

/**
 * Utility function to get risk score badge colors - WCAG compliant severity system with dark mode support
 */
export function getRiskScoreBadgeClass(score: number) {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";

  if (score >= 90) {
    return cn(baseClasses, "bg-critical/20 dark:bg-critical/20 text-critical dark:text-critical border border-critical/30 dark:border-critical/30");
  } else if (score >= 70) {
    return cn(baseClasses, "bg-high/20 dark:bg-high/20 text-high dark:text-high border border-high/30 dark:border-high/30");
  } else if (score >= 40) {
    return cn(baseClasses, "bg-medium/20 dark:bg-medium/20 text-medium dark:text-medium border border-medium/30 dark:border-medium/30");
  } else {
    return cn(baseClasses, "bg-low/20 dark:bg-low/20 text-low dark:text-low border border-low/30 dark:border-low/30");
  }
}

/**
 * Utility function to get severity badge colors with dark mode support
 */
export function getSeverityBadgeClass(severity: "critical" | "high" | "medium" | "low") {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";

  switch (severity) {
    case "critical":
      return cn(baseClasses, "bg-critical/20 dark:bg-critical/20 text-critical dark:text-critical border border-critical/30 dark:border-critical/30");
    case "high":
      return cn(baseClasses, "bg-high/20 dark:bg-high/20 text-high dark:text-high border border-high/30 dark:border-high/30");
    case "medium":
      return cn(baseClasses, "bg-medium/20 dark:bg-medium/20 text-medium dark:text-medium border border-medium/30 dark:border-medium/30");
    case "low":
      return cn(baseClasses, "bg-low/20 dark:bg-low/20 text-low dark:text-low border border-low/30 dark:border-low/30");
    default:
      return cn(baseClasses, "bg-tag-bg dark:bg-tag-bg text-tag-text dark:text-tag-text border border-border dark:border-border");
  }
}

export default useThemeClass;
