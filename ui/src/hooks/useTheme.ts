/**
 * 🎨 useTheme Hook - Theme Management for SentinelForge
 *
 * This hook provides theme management functionality including:
 * - Current theme state (light, dark, system)
 * - Theme switching with localStorage persistence
 * - System theme detection and automatic switching
 * - Smooth transitions between themes
 */

import { useState, useEffect, useCallback } from "react";

export type Theme = "light" | "dark" | "system";

interface UseThemeReturn {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  actualTheme: "light" | "dark";
  isSystemTheme: boolean;
  toggleTheme: () => void;
}

const STORAGE_KEY = "ui-preferences";

/**
 * useTheme Hook - Comprehensive theme management
 *
 * Features:
 * - Persists theme preference to localStorage
 * - Automatically detects system theme changes
 * - Provides smooth transitions between themes
 * - Supports light, dark, and system theme modes
 */
export function useTheme(): UseThemeReturn {
  const [theme, setThemeState] = useState<Theme>("system");
  const [actualTheme, setActualTheme] = useState<"light" | "dark">("light");

  // Get system theme preference
  const getSystemTheme = useCallback((): "light" | "dark" => {
    if (typeof window === "undefined") return "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }, []);

  // Apply theme to document
  const applyTheme = useCallback(
    (themeToApply: Theme) => {
      const root = document.documentElement;

      // Remove existing theme classes
      root.classList.remove("dark");

      let resolvedTheme: "light" | "dark";

      if (themeToApply === "dark") {
        root.classList.add("dark");
        resolvedTheme = "dark";
      } else if (themeToApply === "light") {
        resolvedTheme = "light";
      } else {
        // System theme
        const systemTheme = getSystemTheme();
        if (systemTheme === "dark") {
          root.classList.add("dark");
        }
        resolvedTheme = systemTheme;
      }

      setActualTheme(resolvedTheme);
    },
    [getSystemTheme],
  );

  // Save theme preference to localStorage
  const saveThemePreference = useCallback((newTheme: Theme) => {
    try {
      const existingPreferences = localStorage.getItem(STORAGE_KEY);
      let preferences = { theme: newTheme };

      if (existingPreferences) {
        try {
          const parsed = JSON.parse(existingPreferences);
          preferences = { ...parsed, theme: newTheme };
        } catch (error) {
          console.warn(
            "Failed to parse existing preferences, using defaults:",
            error,
          );
        }
      }

      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      console.warn("Failed to save theme preference:", error);
    }
  }, []);

  // Load theme preference from localStorage
  const loadThemePreference = useCallback((): Theme => {
    try {
      const savedPreferences = localStorage.getItem(STORAGE_KEY);
      if (savedPreferences) {
        const preferences = JSON.parse(savedPreferences);
        return preferences.theme || "system";
      }
    } catch (error) {
      console.warn("Failed to load theme preference:", error);
    }
    return "system";
  }, []);

  // Set theme with persistence
  const setTheme = useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme);
      applyTheme(newTheme);
      saveThemePreference(newTheme);
    },
    [applyTheme, saveThemePreference],
  );

  // Toggle between light and dark (skips system)
  const toggleTheme = useCallback(() => {
    const newTheme = actualTheme === "light" ? "dark" : "light";
    setTheme(newTheme);
  }, [actualTheme, setTheme]);

  // Initialize theme on mount
  useEffect(() => {
    const savedTheme = loadThemePreference();
    setThemeState(savedTheme);
    applyTheme(savedTheme);
  }, [loadThemePreference, applyTheme]);

  // Listen for system theme changes
  useEffect(() => {
    if (typeof window === "undefined") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleSystemThemeChange = () => {
      // Only apply system theme if current theme is set to system
      if (theme === "system") {
        applyTheme("system");
      }
    };

    // Add event listener
    mediaQuery.addEventListener("change", handleSystemThemeChange);

    // Cleanup
    return () => {
      mediaQuery.removeEventListener("change", handleSystemThemeChange);
    };
  }, [theme, applyTheme]);

  return {
    theme,
    setTheme,
    actualTheme,
    isSystemTheme: theme === "system",
    toggleTheme,
  };
}

/**
 * Theme utility functions
 */
export const themeUtils = {
  /**
   * Get the current theme from localStorage
   */
  getCurrentTheme: (): Theme => {
    try {
      const savedPreferences = localStorage.getItem(STORAGE_KEY);
      if (savedPreferences) {
        const preferences = JSON.parse(savedPreferences);
        return preferences.theme || "system";
      }
    } catch (error) {
      console.warn("Failed to get current theme:", error);
    }
    return "system";
  },

  /**
   * Check if dark mode is currently active
   */
  isDarkMode: (): boolean => {
    if (typeof window === "undefined") return false;
    return document.documentElement.classList.contains("dark");
  },

  /**
   * Get system theme preference
   */
  getSystemTheme: (): "light" | "dark" => {
    if (typeof window === "undefined") return "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  },

  /**
   * Apply theme without state management (for one-off usage)
   */
  applyThemeDirectly: (theme: Theme): void => {
    const root = document.documentElement;
    root.classList.remove("dark");

    if (theme === "dark") {
      root.classList.add("dark");
    } else if (theme === "light") {
      // Light mode is default
    } else {
      // System theme
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches
        ? "dark"
        : "light";
      if (systemTheme === "dark") {
        root.classList.add("dark");
      }
    }
  },
};

export default useTheme;
