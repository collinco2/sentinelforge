import React, { useState, useMemo } from "react";
import { DashboardLayout } from "../layout/DashboardLayout";
import { StatCard } from "../components/StatCard";
import { IocTable } from "../components/IocTable";
import { ThreatChart } from "../components/ThreatChart";
import { ThreatTypeChart } from "../components/ThreatTypeChart";
import { ThreatTimelineChart, TimelineDataPoint } from "../components/ThreatTimelineChart";
import { FilterSidebar, IocFilters, defaultFilters } from "../components/FilterSidebar";
import { Card, CardContent } from "../components/ui/card";
import { ShieldAlert, Eye, Flag, Server, AlertCircle } from "lucide-react";
import { IOCData } from "../components/IocTable";
import { IocDetailModal } from "../components/IocDetailModal";
import { useIocs, analyzeIocs } from "../hooks/useIocs";

export function Dashboard() {
  // Modal state
  const [isIocModalOpen, setIocModalOpen] = useState(false);
  const [selectedIoc, setSelectedIoc] = useState<IOCData | null>(null);
  
  // Filter state
  const [filters, setFilters] = useState<IocFilters>(defaultFilters);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Fetch IOC data
  const { iocs, isLoading, isError } = useIocs(filters);
  
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
    if (threatTypeData.length === 0) {
      return [
        { label: 'Phishing', count: 40 },
        { label: 'Malware', count: 25 },
        { label: 'C2', count: 20 },
        { label: 'Recon', count: 15 }
      ];
    }
    return threatTypeData;
  }, [threatTypeData]);

  // Generate mock timeline data for the last 14 days
  const timelineData = useMemo(() => {
    const data: TimelineDataPoint[] = [];
    const today = new Date();
    
    // Create data for the last 14 days
    for (let i = 13; i >= 0; i--) {
      const date = new Date();
      date.setDate(today.getDate() - i);
      
      // Generate a somewhat realistic pattern with increasing trend and some randomness
      let baseCount = 5 + Math.floor(i / 2); // Gradual increase
      
      // Add weekly pattern (weekends lower)
      if (date.getDay() === 0 || date.getDay() === 6) {
        baseCount = Math.floor(baseCount * 0.7); // Weekend drop
      }
      
      // Add randomness
      const randomFactor = 0.5 + Math.random();
      const count = Math.max(1, Math.floor(baseCount * randomFactor));
      
      data.push({
        date: date.toISOString().split('T')[0], // Format as YYYY-MM-DD
        count
      });
    }
    
    return data;
  }, []);

  const handleIocRowClick = (ioc: IOCData) => {
    setSelectedIoc(ioc);
    setIocModalOpen(true);
  };

  const handleFilterChange = (newFilters: IocFilters) => {
    setFilters(newFilters);
  };

  // Count active filters
  const getActiveFilterCount = () => {
    let count = 0;
    
    // Count active type filters
    Object.values(filters.types).forEach(isActive => {
      if (isActive) count++;
    });
    
    // Count active severity filters
    Object.values(filters.severities).forEach(isActive => {
      if (isActive) count++;
    });
    
    // Count confidence range filter (if not default)
    if (filters.confidenceRange[0] > 0 || filters.confidenceRange[1] < 100) {
      count++;
    }
    
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <DashboardLayout title="Threat Intelligence Dashboard">
      {/* Mobile Toggle Button (only visible on mobile) */}
      <div className="md:hidden p-2 mb-4">
        <button
          onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
          className="px-4 py-2 bg-zinc-800 text-gray-200 rounded flex items-center text-sm"
        >
          Filters {activeFilterCount > 0 && <span className="ml-2 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">{activeFilterCount}</span>}
        </button>
      </div>

      <div className="flex flex-col md:flex-row">
        {/* Sidebar - Hidden on mobile unless toggled */}
        <div className={`${isMobileSidebarOpen ? 'block' : 'hidden'} md:block md:sticky md:top-0 md:h-screen`}>
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
              value={String((iocsAnalysis.bySeverity.critical ?? 0))} 
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
              value={String((iocsAnalysis.bySeverity.high ?? 0))} 
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
                <p className="text-sm opacity-80">There was a problem connecting to the API. Please check your connection and try again.</p>
              </div>
            </div>
          )}
          
          {/* Timeline Chart Section */}
          <Card className="bg-card shadow-sm border-border">
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">IOC Activity Timeline</h2>
              <div className={`relative ${isLoading ? 'opacity-50' : ''}`}>
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
                <h2 className="text-xl font-semibold mb-4">Threat Types Distribution</h2>
                <div className={`h-[300px] relative ${isLoading ? 'opacity-50' : ''}`}>
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
                <h2 className="text-xl font-semibold mb-4">Threat Trend Analysis</h2>
                <div className={`h-[300px] relative ${isLoading ? 'opacity-50' : ''}`}>
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
                <h2 className="text-xl font-semibold">Active Indicators of Compromise</h2>
                {activeFilterCount > 0 && (
                  <div className="text-sm text-gray-400">
                    <span className="bg-blue-600/20 text-blue-400 px-2 py-1 rounded-full">
                      {activeFilterCount} {activeFilterCount === 1 ? 'filter' : 'filters'} active
                    </span>
                  </div>
                )}
              </div>
              <IocTable 
                className="w-full" 
                onRowClick={handleIocRowClick}
                noInternalModal={true}
                data={iocs}
                isLoading={isLoading}
              />
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* IOC Detail Modal - now managed at Dashboard level */}
      {selectedIoc && (
        <IocDetailModal 
          ioc={selectedIoc} 
          isOpen={isIocModalOpen} 
          onOpenChange={(open) => {
            setIocModalOpen(open);
            if (!open) setSelectedIoc(null);
          }} 
        />
      )}
    </DashboardLayout>
  );
} 