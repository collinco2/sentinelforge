import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs";
import { cn } from "@/lib/utils";
import { BarChart3, Shield } from "lucide-react";
import { useTheme } from "../hooks/useTheme";

interface DashboardToggleProps {
  className?: string;
}

export function DashboardToggle({ className }: DashboardToggleProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { actualTheme } = useTheme();
  const [currentView, setCurrentView] = useState<"admin" | "analyst">("admin");

  // Determine current view based on route
  useEffect(() => {
    const path = location.pathname;
    if (path === "/threat-dashboard") {
      setCurrentView("analyst");
    } else if (path === "/dashboard") {
      setCurrentView("admin");
    } else {
      // Load from localStorage if not on a dashboard route
      const savedView = localStorage.getItem("dashboardView") as
        | "admin"
        | "analyst"
        | null;
      if (savedView) {
        setCurrentView(savedView);
      }
    }
  }, [location.pathname]);

  // Handle view change
  const handleViewChange = (value: string) => {
    const newView = value as "admin" | "analyst";
    setCurrentView(newView);

    // Save to localStorage
    localStorage.setItem("dashboardView", newView);

    // Navigate to appropriate route with smooth transition
    const targetRoute =
      newView === "analyst" ? "/threat-dashboard" : "/dashboard";

    // Add a small delay for visual feedback
    setTimeout(() => {
      navigate(targetRoute);
    }, 100);
  };

  // Only show toggle on dashboard routes
  const isDashboardRoute =
    location.pathname === "/dashboard" ||
    location.pathname === "/threat-dashboard";

  if (!isDashboardRoute) {
    return null;
  }

  return (
    <div
      className={cn("flex items-center", className)}
      role="group"
      aria-label="Dashboard view selector"
    >
      <Tabs
        value={currentView}
        onValueChange={handleViewChange}
        className="w-auto"
        aria-label="Choose dashboard view"
      >
        <TabsList
          className={cn(
            "grid w-full grid-cols-2 h-9 bg-muted/50 dark:bg-muted/50 p-1 transition-colors duration-200",
            actualTheme === "dark" && "border-border/50",
          )}
          role="tablist"
          aria-orientation="horizontal"
        >
          <TabsTrigger
            value="admin"
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 text-xs font-medium transition-all duration-200",
              "data-[state=active]:bg-background dark:data-[state=active]:bg-background data-[state=active]:text-foreground dark:data-[state=active]:text-foreground data-[state=active]:shadow-sm",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "hover:bg-background/50 dark:hover:bg-background/50 hover:text-foreground dark:hover:text-foreground",
            )}
            aria-label="Switch to Admin Dashboard View - Overview with key metrics and quick access"
            aria-describedby="admin-view-description"
            role="tab"
          >
            <BarChart3 className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="hidden sm:inline">Admin View</span>
            <span className="sm:hidden">Admin</span>
          </TabsTrigger>
          <TabsTrigger
            value="analyst"
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 text-xs font-medium transition-all duration-200",
              "data-[state=active]:bg-background dark:data-[state=active]:bg-background data-[state=active]:text-foreground dark:data-[state=active]:text-foreground data-[state=active]:shadow-sm",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "hover:bg-background/50 dark:hover:bg-background/50 hover:text-foreground dark:hover:text-foreground",
            )}
            aria-label="Switch to Analyst Dashboard View - Detailed threat intelligence and IOC analysis"
            aria-describedby="analyst-view-description"
            role="tab"
          >
            <Shield className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="hidden sm:inline">Analyst View</span>
            <span className="sm:hidden">Analyst</span>
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Hidden descriptions for screen readers */}
      <div className="sr-only">
        <div id="admin-view-description">
          Admin dashboard provides an overview with key metrics, feed health,
          high-risk IOCs, and quick settings access.
        </div>
        <div id="analyst-view-description">
          Analyst dashboard offers detailed threat intelligence analysis with
          comprehensive IOC tables, charts, and filtering capabilities.
        </div>
      </div>
    </div>
  );
}
