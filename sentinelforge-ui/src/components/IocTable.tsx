import React, { useState, useMemo } from "react";
import { 
  ChevronDown, 
  ChevronUp, 
  ChevronsLeft, 
  ChevronsRight, 
  ChevronLeft, 
  ChevronRight,
  Clock
} from "lucide-react";
import { Button } from "../components/ui/button";
import { cn } from "../lib/utils";
import { IocDetailModal } from "./IocDetailModal";
import { IocTableFilters, IocFilters, defaultFilters } from "./IocTableFilters";

// IOC type definition
export interface IOCData {
  id: string;
  value: string;
  type: "ip" | "domain" | "file" | "url" | "email";
  severity: "low" | "medium" | "high" | "critical";
  confidence: number; // percentage 0-100
  timestamp: string;
}

// Props interface
interface IocTableProps {
  data?: IOCData[];
  isLoading?: boolean;
  className?: string;
  onRowClick?: (ioc: IOCData) => void;
  noInternalModal?: boolean;
}

// Mock data
const MOCK_IOC_DATA: IOCData[] = [
  {
    id: "ioc-1",
    value: "malicious-domain.com",
    type: "domain",
    severity: "high",
    confidence: 85,
    timestamp: "2025-05-13T08:30:00Z",
  },
  {
    id: "ioc-2",
    value: "192.168.1.254",
    type: "ip",
    severity: "medium",
    confidence: 72,
    timestamp: "2025-05-13T07:45:00Z",
  },
  {
    id: "ioc-3",
    value: "ransomware.exe",
    type: "file",
    severity: "critical",
    confidence: 98,
    timestamp: "2025-05-13T09:15:00Z",
  },
  {
    id: "ioc-4",
    value: "phishing@attack.org",
    type: "email",
    severity: "medium",
    confidence: 65,
    timestamp: "2025-05-13T06:50:00Z",
  },
  {
    id: "ioc-5",
    value: "https://malware-delivery.net/payload",
    type: "url",
    severity: "high",
    confidence: 88,
    timestamp: "2025-05-13T08:10:00Z",
  },
  {
    id: "ioc-6",
    value: "suspicious.app.apk",
    type: "file",
    severity: "low",
    confidence: 45,
    timestamp: "2025-05-12T22:30:00Z",
  },
  {
    id: "ioc-7",
    value: "10.0.0.123",
    type: "ip",
    severity: "medium",
    confidence: 68,
    timestamp: "2025-05-13T05:25:00Z",
  },
  {
    id: "ioc-8",
    value: "data-exfil.org",
    type: "domain",
    severity: "high",
    confidence: 91,
    timestamp: "2025-05-13T08:55:00Z",
  },
  {
    id: "ioc-9",
    value: "backdoor.dll",
    type: "file",
    severity: "critical",
    confidence: 95,
    timestamp: "2025-05-13T09:05:00Z",
  },
  {
    id: "ioc-10",
    value: "ceo-spoofed@company.com",
    type: "email",
    severity: "medium",
    confidence: 77,
    timestamp: "2025-05-13T07:20:00Z",
  },
  {
    id: "ioc-11",
    value: "command-control.net",
    type: "domain",
    severity: "critical",
    confidence: 99,
    timestamp: "2025-05-13T09:30:00Z",
  },
  {
    id: "ioc-12",
    value: "https://credential-harvester.com/login",
    type: "url",
    severity: "high",
    confidence: 87,
    timestamp: "2025-05-13T08:40:00Z",
  },
  {
    id: "ioc-13",
    value: "172.16.0.1",
    type: "ip",
    severity: "low",
    confidence: 50,
    timestamp: "2025-05-12T20:15:00Z",
  },
  {
    id: "ioc-14",
    value: "trojan.docx",
    type: "file",
    severity: "high",
    confidence: 83,
    timestamp: "2025-05-13T08:20:00Z",
  },
  {
    id: "ioc-15",
    value: "spam@malicious.org",
    type: "email",
    severity: "low",
    confidence: 55,
    timestamp: "2025-05-12T21:45:00Z",
  }
];

export function IocTable({ 
  data = MOCK_IOC_DATA, 
  isLoading, 
  className,
  onRowClick,
  noInternalModal = false 
}: IocTableProps) {
  // State for sorting
  const [sortField, setSortField] = useState<keyof IOCData>("timestamp");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  
  // State for pagination
  const [currentPage, setCurrentPage] = useState(0);
  const rowsPerPage = 10;
  
  // State for modal - only used if noInternalModal is false
  const [selectedIoc, setSelectedIoc] = useState<IOCData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // State for filters
  const [filters, setFilters] = useState<IocFilters>(defaultFilters);
  
  // Calculate active filter count
  const activeFilterCount = useMemo(() => {
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
    
    // Count date filters
    if (filters.dateRange.from) count++;
    if (filters.dateRange.to) count++;
    
    return count;
  }, [filters]);
  
  // Handle opening modal with IOC details
  const handleRowClick = (ioc: IOCData) => {
    if (onRowClick) {
      // If parent provided onRowClick, use that
      onRowClick(ioc);
    } else {
      // Otherwise use internal modal state
      setSelectedIoc(ioc);
      setIsModalOpen(true);
    }
  };
  
  // Reset to default page when filters change
  React.useEffect(() => {
    setCurrentPage(0);
  }, [filters]);
  
  // Apply filters to data
  const filteredData = useMemo(() => {
    return data.filter(ioc => {
      // Check if any type filter is active and if this IOC matches
      const hasActiveTypeFilters = Object.values(filters.types).some(value => value);
      const matchesTypeFilter = !hasActiveTypeFilters || filters.types[ioc.type];
      if (!matchesTypeFilter) return false;
      
      // Check if any severity filter is active and if this IOC matches
      const hasActiveSeverityFilters = Object.values(filters.severities).some(value => value);
      const matchesSeverityFilter = !hasActiveSeverityFilters || filters.severities[ioc.severity];
      if (!matchesSeverityFilter) return false;
      
      // Check confidence range
      if (
        ioc.confidence < filters.confidenceRange[0] ||
        ioc.confidence > filters.confidenceRange[1]
      ) {
        return false;
      }
      
      // Check date range
      const iocDate = new Date(ioc.timestamp);
      if (filters.dateRange.from) {
        const fromDate = new Date(filters.dateRange.from);
        if (iocDate < fromDate) return false;
      }
      
      if (filters.dateRange.to) {
        const toDate = new Date(filters.dateRange.to);
        // Set to end of day
        toDate.setHours(23, 59, 59, 999);
        if (iocDate > toDate) return false;
      }
      
      return true;
    });
  }, [data, filters]);
  
  // Sort and paginate data
  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => {
      if (sortField === "timestamp") {
        return sortDirection === "asc" 
          ? new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          : new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      }
      
      if (sortField === "severity") {
        const severityOrder = {"low": 0, "medium": 1, "high": 2, "critical": 3};
        return sortDirection === "asc" 
          ? severityOrder[a.severity] - severityOrder[b.severity]
          : severityOrder[b.severity] - severityOrder[a.severity];
      }
      
      // Default string comparison for other fields
      return sortDirection === "asc"
        ? a[sortField].toString().localeCompare(b[sortField].toString())
        : b[sortField].toString().localeCompare(a[sortField].toString());
    });
  }, [filteredData, sortField, sortDirection]);
  
  const paginatedData = useMemo(() => {
    const startIdx = currentPage * rowsPerPage;
    return sortedData.slice(startIdx, startIdx + rowsPerPage);
  }, [sortedData, currentPage]);
  
  const totalPages = Math.ceil(sortedData.length / rowsPerPage);
  
  // Toggle sort direction or set new sort field
  const handleSort = (field: keyof IOCData) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc"); // Default to descending for new sort field
    }
  };
  
  // Reset all filters to default
  const handleResetFilters = () => {
    setFilters(defaultFilters);
  };
  
  // Format timestamp to a more readable format
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString(undefined, { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  // Get severity badge class based on severity level
  const getSeverityBadgeClass = (severity: IOCData["severity"]) => {
    const baseClasses = "text-xs px-2 py-1 rounded-full bg-opacity-20";
    switch (severity) {
      case "critical":
        return `${baseClasses} bg-red-600 text-red-500 border border-red-600/20`;
      case "high":
        return `${baseClasses} bg-orange-600 text-orange-500 border border-orange-600/20`;
      case "medium":
        return `${baseClasses} bg-yellow-600 text-yellow-500 border border-yellow-600/20`;
      case "low":
        return `${baseClasses} bg-blue-600 text-blue-400 border border-blue-600/20`;
      default:
        return `${baseClasses} bg-gray-600 text-gray-400 border border-gray-600/20`;
    }
  };
  
  // Get type badge class based on IOC type
  const getTypeBadgeClass = (type: IOCData["type"]) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (type) {
      case "ip":
        return `${baseClasses} bg-purple-600/20 text-purple-400 border border-purple-600/20`;
      case "domain":
        return `${baseClasses} bg-green-600/20 text-green-400 border border-green-600/20`;
      case "file":
        return `${baseClasses} bg-blue-600/20 text-blue-400 border border-blue-600/20`;
      case "url":
        return `${baseClasses} bg-teal-600/20 text-teal-400 border border-teal-600/20`;
      case "email":
        return `${baseClasses} bg-pink-600/20 text-pink-400 border border-pink-600/20`;
      default:
        return `${baseClasses} bg-gray-600/20 text-gray-400 border border-gray-600/20`;
    }
  };

  // Get confidence bar color based on confidence level
  const getConfidenceBarColor = (confidence: number) => {
    if (confidence > 90) return "bg-red-600";
    if (confidence >= 70) return "bg-yellow-500";
    return "bg-green-500";
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="p-4 border border-zinc-700 rounded-md bg-zinc-800 text-center text-muted-foreground">
        <p>Loading IOC data...</p>
      </div>
    );
  }
  
  return (
    <>
      {/* Filters */}
      <IocTableFilters 
        filters={filters}
        onFiltersChange={setFilters}
        onReset={handleResetFilters}
        activeFilterCount={activeFilterCount}
      />
    
      <div className={cn("overflow-hidden rounded-md border border-zinc-700 bg-zinc-800", className)}>
        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-700">
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                  <div className="flex items-center">
                    IOC Value
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                  <div className="flex items-center">
                    Type
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-left text-sm font-medium text-muted-foreground cursor-pointer"
                  onClick={() => handleSort("severity")}
                >
                  <div className="flex items-center">
                    Severity
                    {sortField === "severity" && (
                      sortDirection === "asc" ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                  <div className="flex items-center">
                    Confidence
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-right text-sm font-medium text-muted-foreground cursor-pointer"
                  onClick={() => handleSort("timestamp")}
                >
                  <div className="flex items-center justify-end">
                    Timestamp
                    {sortField === "timestamp" && (
                      sortDirection === "asc" ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((ioc) => (
                <tr 
                  key={ioc.id} 
                  className="border-b border-zinc-700 hover:bg-zinc-700/50 transition-colors cursor-pointer"
                  onClick={() => handleRowClick(ioc)}
                >
                  <td className="px-4 py-2 text-sm">
                    <div className="font-mono text-foreground">{ioc.value}</div>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <span className={getTypeBadgeClass(ioc.type)}>{ioc.type}</span>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <span className={getSeverityBadgeClass(ioc.severity)}>{ioc.severity}</span>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <div className="flex items-center">
                      <div className="w-full bg-zinc-700 rounded-full h-2 mr-2 max-w-[100px]">
                        <div 
                          className={cn(
                            "h-full rounded-full",
                            getConfidenceBarColor(ioc.confidence)
                          )}
                          style={{ width: `${ioc.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">{ioc.confidence}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-400 text-right">
                    <div className="flex items-center justify-end">
                      <Clock className="mr-1 h-3 w-3" />
                      {formatTimestamp(ioc.timestamp)}
                    </div>
                  </td>
                </tr>
              ))}
              
              {paginatedData.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    {sortedData.length === 0 ? "No IOCs match the current filters" : "No IOC data available"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-zinc-700 px-4 py-3 flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Showing {sortedData.length > 0 ? currentPage * rowsPerPage + 1 : 0} to {Math.min((currentPage + 1) * rowsPerPage, sortedData.length)} of {sortedData.length} entries
            </div>
            <div className="flex items-center space-x-1">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(0)} 
                disabled={currentPage === 0}
                aria-label="First page"
                className="border-zinc-700 bg-zinc-800 hover:bg-zinc-700"
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(currentPage - 1)} 
                disabled={currentPage === 0}
                aria-label="Previous page"
                className="border-zinc-700 bg-zinc-800 hover:bg-zinc-700"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              
              <span className="mx-2 text-sm text-muted-foreground">
                Page {currentPage + 1} of {totalPages}
              </span>
              
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(currentPage + 1)} 
                disabled={currentPage >= totalPages - 1}
                aria-label="Next page"
                className="border-zinc-700 bg-zinc-800 hover:bg-zinc-700"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(totalPages - 1)} 
                disabled={currentPage >= totalPages - 1}
                aria-label="Last page"
                className="border-zinc-700 bg-zinc-800 hover:bg-zinc-700"
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
      
      {/* IOC Detail Modal - only render if not using parent modal */}
      {!noInternalModal && (
        <IocDetailModal 
          ioc={selectedIoc} 
          isOpen={isModalOpen} 
          onOpenChange={setIsModalOpen} 
        />
      )}
    </>
  );
} 