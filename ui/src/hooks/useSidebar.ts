/**
 * 🎛️ useSidebar Hook - Persistent sidebar state management
 *
 * Manages sidebar collapsed/expanded state with:
 * - localStorage persistence across sessions
 * - Responsive behavior for mobile devices
 * - Default collapsed state for non-dashboard pages
 * - Automatic mobile collapse regardless of saved state
 *
 * Features:
 * - Saves state to localStorage under 'sidebarCollapsed'
 * - Auto-collapses on screens < md (768px)
 * - Defaults to collapsed for better UX on first load
 * - Provides toggle functionality with state persistence
 */

import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

const STORAGE_KEY = "sidebarCollapsed";
const MOBILE_BREAKPOINT = 768; // md breakpoint in Tailwind

interface UseSidebarReturn {
  /** Whether the sidebar is currently collapsed */
  isCollapsed: boolean;
  /** Whether the current screen size is mobile */
  isMobile: boolean;
  /** Toggle the sidebar collapsed state */
  toggle: () => void;
  /** Set the sidebar collapsed state directly */
  setCollapsed: (collapsed: boolean) => void;
  /** Close sidebar (useful for mobile overlay clicks) */
  close: () => void;
}

export function useSidebar(): UseSidebarReturn {
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(true); // Default to collapsed
  const [isMobile, setIsMobile] = useState(false);

  // Initialize sidebar state from localStorage or default
  useEffect(() => {
    const initializeSidebar = () => {
      // Check if we're on mobile
      const isMobileScreen = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(isMobileScreen);

      // On mobile, always collapse regardless of saved state
      if (isMobileScreen) {
        setIsCollapsed(true);
        return;
      }

      // For desktop, check localStorage or use default
      try {
        const savedState = localStorage.getItem(STORAGE_KEY);
        if (savedState !== null) {
          setIsCollapsed(JSON.parse(savedState));
        } else {
          // Default behavior: collapsed for non-dashboard pages
          const isDashboard =
            location.pathname === "/dashboard" || location.pathname === "/";
          setIsCollapsed(!isDashboard);
        }
      } catch (error) {
        console.warn("Failed to read sidebar state from localStorage:", error);
        // Fallback to default collapsed state
        setIsCollapsed(true);
      }
    };

    initializeSidebar();
  }, [location.pathname]);

  // Handle window resize for responsive behavior
  useEffect(() => {
    const handleResize = () => {
      const isMobileScreen = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(isMobileScreen);

      // Auto-collapse on mobile regardless of saved state
      if (isMobileScreen && !isCollapsed) {
        setIsCollapsed(true);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [isCollapsed]);

  // Save state to localStorage whenever it changes (but not on mobile)
  useEffect(() => {
    if (!isMobile) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(isCollapsed));
      } catch (error) {
        console.warn("Failed to save sidebar state to localStorage:", error);
      }
    }
  }, [isCollapsed, isMobile]);

  const toggle = () => {
    setIsCollapsed((prev) => !prev);
  };

  const setCollapsed = (collapsed: boolean) => {
    setIsCollapsed(collapsed);
  };

  const close = () => {
    setIsCollapsed(true);
  };

  return {
    isCollapsed,
    isMobile,
    toggle,
    setCollapsed,
    close,
  };
}
