import React, { useState, useMemo, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageTransition } from "../components/PageTransition";
import { StatCard } from "../components/StatCard";
import { IocTable } from "../components/IocTable";
import { ThreatChart } from "../components/ThreatChart";
import { ThreatTypeChart } from "../components/ThreatTypeChart";
import {
  ThreatTimelineChart,
  TimelineDataPoint,
} from "../components/ThreatTimelineChart";
import {
  FilterSidebar,
  IocFilters,
  defaultFilters,
} from "../components/FilterSidebar";
import { Card, CardContent } from "../components/ui/card";
import { ShieldAlert, Eye, Flag, Server, AlertCircle } from "lucide-react";
import { IOCData } from "../components/IocTable";
import { IocDetailModal } from "../components/IocDetailModal";
import { useIocs, analyzeIocs } from "../hooks/useIocs";

export function Dashboard() {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Modal state
  const [isIocModalOpen, setIocModalOpen] = useState(false);
  const [selectedIocId, setSelectedIocId] = useState<string | null>(null);

  // Filter state
  const [filters, setFilters] = useState<IocFilters>(defaultFilters);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // New sorting and pagination states
  const [sortColumn, setSortColumn] = useState<keyof IOCData>("timestamp");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 10; // Fixed page size for now

  // Fetch IOC data with filters
  const { iocs, isLoading, isError } = useIocs(filters);

  // Check for IOC ID in query params for direct opening
  useEffect(() => {
    const directIocId = searchParams.get("iocId");
    if (directIocId) {
      setSelectedIocId(directIocId);
      setIocModalOpen(true);
    }
  }, [searchParams]);

  // Client-side sorting function
  const sortedIocs = useMemo(() => {
    if (isLoading || !iocs.length) return [];

    return [...iocs].sort((a, b) => {
      if (sortColumn === "timestamp") {
        return sortDirection === "asc"
          ? new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          : new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      }

      if (sortColumn === "severity") {
        const severityOrder = { low: 0, medium: 1, high: 2, critical: 3 };
        return sortDirection === "asc"
          ? severityOrder[a.severity] - severityOrder[b.severity]
          : severityOrder[b.severity] - severityOrder[a.severity];
      }

      if (sortColumn === "confidence") {
        return sortDirection === "asc"
          ? a.confidence - b.confidence
          : b.confidence - a.confidence;
      }

      // Default string comparison for other fields
      return sortDirection === "asc"
        ? (a[sortColumn]?.toString() ?? "").localeCompare(
            b[sortColumn]?.toString() ?? "",
          )
        : (b[sortColumn]?.toString() ?? "").localeCompare(
            a[sortColumn]?.toString() ?? "",
          );
    });
  }, [iocs, sortColumn, sortDirection, isLoading]);

  // Apply pagination to the sorted data
  const paginatedIocs = useMemo(() => {
    const startIndex = currentPage * pageSize;
    return sortedIocs.slice(startIndex, startIndex + pageSize);
  }, [sortedIocs, currentPage, pageSize]);

  // Handle sort change from the IocTable
  const handleSortChange = (
    column: keyof IOCData,
    direction: "asc" | "desc",
  ) => {
    setSortColumn(column);
    setSortDirection(direction);
    // Reset to first page when sorting changes
    setCurrentPage(0);
  };

  // Handle page change from the IocTable
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Analyze IOC data for stats and charts
  const iocsAnalysis = useMemo(() => analyzeIocs(iocs), [iocs]);

  // Generate data for ThreatTypeChart from IOC types
  const threatTypeData = useMemo(() => {
    return Object.entries(iocsAnalysis.byType)
      .filter(([_, count]) => count > 0)
      .map(([label, count]) => ({ label, count }));
  }, [iocsAnalysis]);

  // If no threat type data is available, use placeholder data
  const chartData = useMemo(() => {
    if (threatTypeData.length === 0 && !isLoading) {
      return [
        { label: "Phishing", count: 40 },
        { label: "Malware", count: 25 },
        { label: "C2", count: 20 },
        { label: "Recon", count: 15 },
      ];
    }
    return threatTypeData;
  }, [threatTypeData, isLoading]);

  // Generate timeline data from the actual IOCs for the last 14 days
  const timelineData = useMemo(() => {
    if (isLoading || !iocs.length) {
      // Return empty array during loading
      return [];
    }

    const data: TimelineDataPoint[] = [];
    const today = new Date();
    const dateCounts: Record<string, number> = {};

    // Initialize last 14 days with zero counts
    for (let i = 13; i >= 0; i--) {
      const date = new Date();
      date.setDate(today.getDate() - i);
      const dateStr = date.toISOString().split("T")[0]; // Format as YYYY-MM-DD
      dateCounts[dateStr] = 0;
    }

    // Count IOCs by date
    iocs.forEach((ioc) => {
      if (ioc.timestamp) {
        try {
          const iocDate = new Date(ioc.timestamp);
          const dateStr = iocDate.toISOString().split("T")[0];

          // Only count if in the last 14 days
          if (dateCounts[dateStr] !== undefined) {
            dateCounts[dateStr] = (dateCounts[dateStr] || 0) + 1;
          }
        } catch (e) {
          // Skip invalid dates
        }
      }
    });

    // Convert to timeline data format
    Object.entries(dateCounts)
      .sort(([dateA], [dateB]) => dateA.localeCompare(dateB))
      .forEach(([date, count]) => {
        data.push({ date, count });
      });

    return data.length ? data : generateFallbackTimelineData();
  }, [iocs, isLoading]);

  // Fallback timeline data generator function
  const generateFallbackTimelineData = () => {
    const data: TimelineDataPoint[] = [];
    const today = new Date();

    for (let i = 13; i >= 0; i--) {
      const date = new Date();
      date.setDate(today.getDate() - i);

      // Generate realistic pattern with some randomness
      let baseCount = 5 + Math.floor(i / 2);

      // Add weekly pattern
      if (date.getDay() === 0 || date.getDay() === 6) {
        baseCount = Math.floor(baseCount * 0.7);
      }

      // Add randomness
      const randomFactor = 0.5 + Math.random();
      const count = Math.max(1, Math.floor(baseCount * randomFactor));

      data.push({
        date: date.toISOString().split("T")[0],
        count,
      });
    }

    return data;
  };

  const handleFilterChange = (newFilters: IocFilters) => {
    console.log("Filters changed:", newFilters);
    setFilters(newFilters);
    // Reset to first page when filters change
    setCurrentPage(0);
  };

  // Count active filters
  const getActiveFilterCount = () => {
    let count = 0;

    // Count active type filters
    Object.values(filters.types).forEach((isActive) => {
      if (isActive) count++;
    });

    // Count active severity filters
    Object.values(filters.severities).forEach((isActive) => {
      if (isActive) count++;
    });

    // Count confidence range filter (if not default)
    if (filters.confidenceRange[0] > 0 || filters.confidenceRange[1] < 100) {
      count++;
    }

    // Count date filters
    if (filters.dateRange?.from) count++;
    if (filters.dateRange?.to) count++;

    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  // Handle modal closing
  const handleModalClose = (open: boolean) => {
    setIocModalOpen(open);

    if (!open) {
      setSelectedIocId(null);

      // Remove the iocId query parameter when closing the modal
      const newParams = new URLSearchParams(searchParams);
      newParams.delete("iocId");

      // Update URL without full page reload
      window.history.replaceState(
        {},
        "",
        newParams.toString()
          ? `${window.location.pathname}?${newParams.toString()}`
          : window.location.pathname,
      );
    }
  };

  // Custom navigation handler for the modal
  const handleNavigation = (url: string) => {
    navigate(url);
  };

  // Log the paginated IOCs for debugging
  console.log("Dashboard: visibleIocs being passed to table", paginatedIocs);

  // Open modal when selectedIocId changes
  useEffect(() => {
    if (selectedIocId) {
      setIocModalOpen(true);

      // Update URL with query parameter without navigation
      const newParams = new URLSearchParams();
      newParams.set("iocId", selectedIocId);

      // Update URL without full page reload
      window.history.replaceState(
        {},
        "",
        `${window.location.pathname}?${newParams.toString()}`,
      );
    }
  }, [selectedIocId]);

  return (
    <DashboardLayout title="Threat Intelligence Dashboard">
      <PageTransition>
        {/* Mobile Toggle Button (only visible on mobile) */}
        <div className="md:hidden p-2 mb-4">
          <button
            onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
            className="px-4 py-2 bg-zinc-800 text-gray-200 rounded flex items-center text-sm"
          >
            Filters{" "}
            {activeFilterCount > 0 && (
              <span className="ml-2 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>

        <div className="flex flex-col md:flex-row">
          {/* Sidebar - Hidden on mobile unless toggled */}
          <div
            className={`${isMobileSidebarOpen ? "block" : "hidden"} md:block md:sticky md:top-0 md:h-screen`}
          >
            <FilterSidebar
              filters={filters}
              onFilterChange={handleFilterChange}
              className="md:max-h-[calc(100vh-2rem)] md:overflow-y-auto"
            />
          </div>

          {/* Main Content */}
          <div className="flex-1 p-0 md:p-4 space-y-6">
            {/* Stats Section */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <StatCard
                title="Critical Threats"
                value={String(iocsAnalysis.bySeverity.critical ?? 0)}
                icon={ShieldAlert}
                variant="critical"
                change={isLoading ? undefined : 0}
                changePeriod="last 24 hours"
                className="min-h-[96px]"
                isLoading={isLoading}
              />

              <StatCard
                title="Active IOCs"
                value={String(iocsAnalysis.total ?? 0)}
                icon={Eye}
                variant="default"
                change={isLoading ? undefined : (iocsAnalysis.recentCount ?? 0)}
                changePeriod="added today"
                className="min-h-[96px]"
                isLoading={isLoading}
              />

              <StatCard
                title="High Severity"
                value={String(iocsAnalysis.bySeverity.high ?? 0)}
                icon={Flag}
                variant="warning"
                change={isLoading ? undefined : 0}
                className="min-h-[96px]"
                isLoading={isLoading}
              />

              <StatCard
                title="Avg Confidence"
                value={`${iocsAnalysis.avgConfidence ?? 0}%`}
                icon={Server}
                variant="success"
                change={isLoading ? undefined : 0}
                changePeriod="current score"
                className="min-h-[96px]"
                isLoading={isLoading}
              />
            </div>

            {/* Error Message */}
            {isError && (
              <div className="bg-red-900/30 border border-red-800 text-red-300 p-4 rounded-md mb-6 flex items-start">
                <AlertCircle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-medium">Error fetching IOC data</h3>
                  <p className="text-sm opacity-80">
                    There was a problem connecting to the API. Please check your
                    connection and try again.
                  </p>
                </div>
              </div>
            )}

            {/* Timeline Chart Section */}
            <Card className="bg-card shadow-sm border-border">
              <CardContent className="p-6">
                <h2 className="text-xl font-semibold mb-4">
                  IOC Activity Timeline
                </h2>
                <div className={`relative ${isLoading ? "opacity-50" : ""}`}>
                  <ThreatTimelineChart
                    data={timelineData}
                    height={250}
                    className="mt-2"
                  />
                  {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/30">
                      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Chart Section - Grid with two charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Threat Types Distribution */}
              <Card className="bg-card shadow-sm border-border">
                <CardContent className="p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    Threat Types Distribution
                  </h2>
                  <div
                    className={`h-[300px] relative ${isLoading ? "opacity-50" : ""}`}
                  >
                    <ThreatTypeChart data={chartData} className="h-[300px]" />
                    {isLoading && (
                      <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/30">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Threat Trend Analysis */}
              <Card className="bg-card shadow-sm border-border">
                <CardContent className="p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    Threat Trend Analysis
                  </h2>
                  <div
                    className={`h-[300px] relative ${isLoading ? "opacity-50" : ""}`}
                  >
                    <ThreatChart />
                    {isLoading && (
                      <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/30">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* IOC Table Section */}
            <Card className="bg-card shadow-sm border-border">
              <CardContent className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold">
                    Active Indicators of Compromise
                  </h2>
                  {activeFilterCount > 0 && (
                    <div className="text-sm text-gray-400">
                      <span className="bg-blue-600/20 text-blue-400 px-2 py-1 rounded-full">
                        {activeFilterCount}{" "}
                        {activeFilterCount === 1 ? "filter" : "filters"} active
                      </span>
                    </div>
                  )}
                </div>
                <IocTable
                  className="w-full"
                  onRowClick={(ioc) => {
                    console.log("[Dashboard] Row clicked:", ioc);
                    setSelectedIocId(ioc.value);
                  }}
                  noInternalModal={true}
                  data={paginatedIocs}
                  isLoading={isLoading}
                  externalControl={true}
                  sortColumn={sortColumn}
                  sortDirection={sortDirection}
                  onSortChange={handleSortChange}
                  currentPage={currentPage}
                  pageSize={pageSize}
                  totalCount={sortedIocs.length}
                  onPageChange={handlePageChange}
                />
              </CardContent>
            </Card>
          </div>
        </div>

        {/* IOC Detail Modal - now using iocId instead of the full object */}
        <IocDetailModal
          iocId={selectedIocId}
          isOpen={isIocModalOpen}
          onOpenChange={handleModalClose}
          sourceContext="dashboard"
          onNavigate={handleNavigation}
        />
      </PageTransition>
    </DashboardLayout>
  );
}
