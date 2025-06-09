import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageTransition } from "../components/PageTransition";
import { DashboardToggle } from "../components/DashboardToggle";
import { IocTable, IOCData } from "../components/IocTable";
import { IocDetailModal } from "../components/IocDetailModal";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import {
  DashboardContainer,
  DashboardSection,
  DashboardMetrics,
  StatWidget,
  FeedCard,
  SeverityBadge,
} from "../components/dashboard";
import {
  BarChart3,
  TrendingUp,
  Shield,
  AlertTriangle,
  Clock,
  Database,
  Activity,
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

// Dashboard view type
type DashboardView = "overview" | "detailed";

export function ThreatDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const scrollPositionRef = useRef<number>(0);

  // State management
  const [currentView, setCurrentView] = useState<DashboardView>("overview");
  const [selectedIocId, setSelectedIocId] = useState<string | null>(null);
  const [isIocModalOpen, setIsIocModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dashboard mode synchronization
  useEffect(() => {
    const currentPath = location.pathname;
    const savedView = localStorage.getItem("dashboardView");

    // If we're on the wrong dashboard for the saved preference, redirect
    if (savedView === "admin" && currentPath === "/threat-dashboard") {
      // Save current scroll position before redirecting
      scrollPositionRef.current = window.scrollY;
      navigate("/dashboard", { replace: true });
      return;
    }

    // Update localStorage to reflect current view
    if (currentPath === "/threat-dashboard") {
      localStorage.setItem("dashboardView", "analyst");
    }
  }, [location.pathname, navigate]);

  // Preserve scroll position when switching dashboards
  useEffect(() => {
    const handleBeforeUnload = () => {
      scrollPositionRef.current = window.scrollY;
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    // Restore scroll position if coming from dashboard switch
    const savedScrollPosition = sessionStorage.getItem(
      "dashboardScrollPosition",
    );
    if (savedScrollPosition) {
      setTimeout(() => {
        window.scrollTo(0, parseInt(savedScrollPosition, 10));
        sessionStorage.removeItem("dashboardScrollPosition");
      }, 100);
    }

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Save scroll position when component unmounts (dashboard switch)
  useEffect(() => {
    return () => {
      sessionStorage.setItem(
        "dashboardScrollPosition",
        window.scrollY.toString(),
      );
    };
  }, []);

  // Initialize dashboard data
  useEffect(() => {
    const initializeDashboard = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Simulate data loading
        await new Promise((resolve) => setTimeout(resolve, 500));
        setIsLoading(false);
      } catch (err) {
        console.error("Error initializing threat dashboard:", err);
        setError("Failed to load threat dashboard data");
        setIsLoading(false);
      }
    };

    initializeDashboard();
  }, []);

  // Handle IOC selection
  const handleIocSelect = (ioc: IOCData) => {
    setSelectedIocId(ioc.id);
    setIsIocModalOpen(true);
  };

  // Handle modal close
  const handleModalClose = () => {
    setIsIocModalOpen(false);
    setSelectedIocId(null);
  };

  // Handle navigation from modal
  const handleNavigation = (path: string) => {
    navigate(path);
    handleModalClose();
  };

  if (isLoading) {
    return (
      <DashboardLayout title="Threat Intelligence Dashboard">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Threat Intelligence Dashboard">
      <PageTransition>
        <DashboardContainer>
          {/* Dashboard Toggle */}
          <div className="flex justify-center mb-4">
            <DashboardToggle />
          </div>

          {/* Mobile Toggle Button (only visible on mobile) */}
          <div className="md:hidden">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">
                Dashboard View
              </h2>
              <div className="flex rounded-lg bg-muted p-1">
                <Button
                  variant={currentView === "overview" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCurrentView("overview")}
                  className="text-xs"
                >
                  Overview
                </Button>
                <Button
                  variant={currentView === "detailed" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCurrentView("detailed")}
                  className="text-xs"
                >
                  Detailed
                </Button>
              </div>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20 transition-colors duration-200">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              <AlertDescription className="text-red-800 dark:text-red-200">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Overview Cards - Always visible on desktop, conditional on mobile */}
          <div className={`${currentView === "detailed" ? "md:hidden" : ""}`}>
            <DashboardMetrics columns={4}>
              <StatWidget
                title="Total IOCs"
                value={12847}
                description="+2.1% from last month"
                icon={Database}
                trend={{ value: "+2.1%", isPositive: true }}
              />

              <StatWidget
                title="High Risk IOCs"
                value={342}
                description="+12.3% from last week"
                icon={AlertTriangle}
                iconColor="text-red-500 dark:text-red-400"
                trend={{ value: "+12.3%", isPositive: false }}
              />

              <StatWidget
                title="Active Feeds"
                value={18}
                description="2 feeds updated today"
                icon={Activity}
                iconColor="text-green-500 dark:text-green-400"
              />

              <StatWidget
                title="Recent Alerts"
                value={89}
                description="Last 24 hours"
                icon={Clock}
                iconColor="text-blue-500 dark:text-blue-400"
              />
            </DashboardMetrics>
          </div>

          {/* Charts Section - Desktop only or when overview is selected on mobile */}
          <div className={`${currentView === "detailed" ? "md:hidden" : ""}`}>
            <DashboardSection columns={2}>
              {/* IOC Trends Chart */}
              <FeedCard
                title="IOC Trends (Last 30 Days)"
                icon={TrendingUp}
                iconColor="text-foreground dark:text-foreground"
              >
                <div className="h-64 flex items-center justify-center text-muted-foreground dark:text-muted-foreground">
                  <div className="text-center">
                    <BarChart3 className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-sm font-medium">
                      Chart visualization would be rendered here
                    </p>
                    <p className="text-xs text-muted-foreground dark:text-muted-foreground mt-1">
                      Using recharts or similar library
                    </p>
                  </div>
                </div>
              </FeedCard>

              {/* Threat Categories */}
              <FeedCard
                title="Threat Categories"
                icon={Shield}
                iconColor="text-foreground dark:text-foreground"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200">
                    <span className="text-sm font-medium text-foreground dark:text-foreground">
                      Malware
                    </span>
                    <SeverityBadge severity="high" size="sm" />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200">
                    <span className="text-sm font-medium text-foreground dark:text-foreground">
                      Phishing
                    </span>
                    <SeverityBadge severity="medium" size="sm" />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200">
                    <span className="text-sm font-medium text-foreground dark:text-foreground">
                      Suspicious IPs
                    </span>
                    <SeverityBadge severity="low" size="sm" />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200">
                    <span className="text-sm font-medium text-foreground dark:text-foreground">
                      C2 Domains
                    </span>
                    <SeverityBadge severity="critical" size="sm" />
                  </div>
                </div>
              </FeedCard>
            </DashboardSection>
          </div>

          {/* IOC Table Section - Always visible on desktop, conditional on mobile */}
          <div className={`${currentView === "overview" ? "md:hidden" : ""}`}>
            <FeedCard
              title="Indicators of Compromise"
              icon={Database}
              iconColor="text-foreground dark:text-foreground"
            >
              <div className="flex items-center gap-2 mb-4">
                <button className="flex items-center gap-2 px-3 py-2 text-sm border border-border dark:border-border rounded-md hover:bg-muted dark:hover:bg-muted transition-colors duration-200">
                  <Filter className="h-4 w-4" />
                  <span className="hidden sm:inline">Filter</span>
                </button>
                <button className="flex items-center gap-2 px-3 py-2 text-sm border border-border dark:border-border rounded-md hover:bg-muted dark:hover:bg-muted transition-colors duration-200">
                  <Download className="h-4 w-4" />
                  <span className="hidden sm:inline">Export</span>
                </button>
                <button className="flex items-center gap-2 px-3 py-2 text-sm border border-border dark:border-border rounded-md hover:bg-muted dark:hover:bg-muted transition-colors duration-200">
                  <RefreshCw className="h-4 w-4" />
                  <span className="hidden sm:inline">Refresh</span>
                </button>
              </div>
              <IocTable onRowClick={handleIocSelect} />
            </FeedCard>
          </div>

          {/* IOC Detail Modal */}
          <IocDetailModal
            iocId={selectedIocId}
            isOpen={isIocModalOpen}
            onOpenChange={handleModalClose}
            sourceContext="threat-dashboard"
            onNavigate={handleNavigation}
          />
        </DashboardContainer>
      </PageTransition>
    </DashboardLayout>
  );
}
