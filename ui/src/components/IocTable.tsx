import React, { useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronUp,
  ChevronsLeft,
  ChevronsRight,
  ChevronLeft,
  ChevronRight,
  Clock,
  ExternalLink,
  Link,
  Check,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { cn } from "../lib/utils";
import { IocDetailModal } from "./IocDetailModal";
import { IocTableFilters, IocFilters, defaultFilters } from "./IocTableFilters";
import ExportReportButton from "./ExportReportButton";

// IOC type definition
export interface IOCData {
  id: string;
  value: string;
  type: "ip" | "domain" | "file" | "url" | "email";
  severity: "low" | "medium" | "high" | "critical";
  confidence: number; // percentage 0-100
  timestamp: string;
  first_observed?: string;
}

// Props interface
interface IocTableProps {
  data?: IOCData[];
  isLoading?: boolean;
  className?: string;
  onRowClick?: (ioc: IOCData) => void;
  noInternalModal?: boolean;
  // New sorting and pagination props
  onSortChange?: (column: keyof IOCData, direction: "asc" | "desc") => void;
  sortColumn?: keyof IOCData;
  sortDirection?: "asc" | "desc";
  currentPage?: number;
  pageSize?: number;
  totalCount?: number;
  onPageChange?: (page: number) => void;
  // Flag to determine if sorting/pagination is handled externally
  externalControl?: boolean;
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
  },
];

// Add a helper function for pagination that includes numbered page links
const PaginationControls = ({
  currentPage,
  totalPages,
  onPageChange,
  isLoading = false,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}) => {
  // Show at most 5 pages at a time
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;

    let startPage = Math.max(0, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages - 1, startPage + maxPagesToShow - 1);

    // Adjust startPage if we're near the end
    if (endPage - startPage + 1 < maxPagesToShow) {
      startPage = Math.max(0, endPage - maxPagesToShow + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return pages;
  };

  if (isLoading) {
    return (
      <div className="flex items-center space-x-1 opacity-50">
        <Button
          variant="outline"
          size="sm"
          disabled
          className="border-border dark:border-border bg-secondary dark:bg-secondary"
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled
          className="border-border dark:border-border bg-secondary dark:bg-secondary"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <div className="mx-2 text-sm text-muted-foreground">Loading...</div>

        <Button
          variant="outline"
          size="sm"
          disabled
          className="border-border dark:border-border bg-secondary dark:bg-secondary"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled
          className="border-border dark:border-border bg-secondary dark:bg-secondary"
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-1">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(0)}
        disabled={currentPage === 0}
        aria-label="First page"
        className="border-border dark:border-border bg-secondary dark:bg-secondary hover:bg-muted dark:hover:bg-muted"
      >
        <ChevronsLeft className="h-4 w-4" />
        <span className="sr-only">First Page</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 0}
        aria-label="Previous page"
        className="border-border dark:border-border bg-secondary dark:bg-secondary hover:bg-muted dark:hover:bg-muted"
      >
        <ChevronLeft className="h-4 w-4" />
        <span className="sr-only">Previous Page</span>
      </Button>

      {/* Numbered page buttons */}
      <div className="hidden sm:flex items-center space-x-1">
        {getPageNumbers().map((pageNum) => (
          <Button
            key={pageNum}
            variant={pageNum === currentPage ? "default" : "outline"}
            size="sm"
            onClick={() => onPageChange(pageNum)}
            className={`border-border dark:border-border ${
              pageNum === currentPage
                ? "bg-primary dark:bg-primary text-primary-foreground dark:text-primary-foreground"
                : "bg-secondary dark:bg-secondary hover:bg-muted dark:hover:bg-muted"
            }`}
            aria-current={pageNum === currentPage ? "page" : undefined}
            aria-label={`Page ${pageNum + 1}`}
          >
            {pageNum + 1}
          </Button>
        ))}
      </div>

      {/* Mobile current page indicator */}
      <div className="sm:hidden mx-2 text-sm text-muted-foreground">
        Page {currentPage + 1} of {totalPages}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages - 1}
        aria-label="Next page"
        className="border-border dark:border-border bg-secondary dark:bg-secondary hover:bg-muted dark:hover:bg-muted"
      >
        <ChevronRight className="h-4 w-4" />
        <span className="sr-only">Next Page</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(totalPages - 1)}
        disabled={currentPage >= totalPages - 1}
        aria-label="Last page"
        className="border-border dark:border-border bg-secondary dark:bg-secondary hover:bg-muted dark:hover:bg-muted"
      >
        <ChevronsRight className="h-4 w-4" />
        <span className="sr-only">Last Page</span>
      </Button>
    </div>
  );
};

// Add a SortableColumnHeader component for consistent header styling and behavior
const SortableColumnHeader = ({
  column,
  label,
  currentSortColumn,
  currentSortDirection,
  onSort,
  align = "left",
}: {
  column: keyof IOCData;
  label: string;
  currentSortColumn: keyof IOCData;
  currentSortDirection: "asc" | "desc";
  onSort: (column: keyof IOCData) => void;
  align?: "left" | "right";
}) => {
  const isActive = currentSortColumn === column;

  return (
    <th
      className={`px-4 py-3 text-${align} text-sm font-medium text-muted-foreground cursor-pointer group transition-colors hover:bg-muted/50`}
      onClick={() => onSort(column)}
      aria-sort={
        isActive
          ? currentSortDirection === "asc"
            ? "ascending"
            : "descending"
          : "none"
      }
    >
      <div
        className={`flex items-center ${align === "right" ? "justify-end" : ""}`}
      >
        {label}
        <div className="ml-1 flex items-center">
          {isActive ? (
            currentSortDirection === "asc" ? (
              <ChevronUp className="h-4 w-4 text-primary" />
            ) : (
              <ChevronDown className="h-4 w-4 text-primary" />
            )
          ) : (
            <ChevronDown className="h-4 w-4 opacity-0 group-hover:opacity-30 transition-opacity" />
          )}
        </div>
      </div>
    </th>
  );
};

export function IocTable({
  data = MOCK_IOC_DATA,
  isLoading,
  className,
  onRowClick,
  noInternalModal = false,
  // New sorting and pagination props
  onSortChange,
  sortColumn,
  sortDirection,
  currentPage = 0,
  pageSize = 10,
  totalCount,
  onPageChange,
  // Flag to determine if sorting/pagination is handled externally
  externalControl = false,
}: IocTableProps) {
  // State for sorting
  const [sortField, setSortField] = useState<keyof IOCData>("timestamp");
  const [sortDirectionState, setSortDirectionState] = useState<"asc" | "desc">(
    "desc",
  );

  // State for pagination
  const [currentPageState, setCurrentPageState] = useState(0);
  const rowsPerPage = 10;

  // State for modal - only used if noInternalModal is false
  const [selectedIoc, setSelectedIoc] = useState<IOCData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // State for filters
  const [filters, setFilters] = useState<IocFilters>(defaultFilters);

  // State for sharing
  const [copiedRowId, setCopiedRowId] = useState<string | null>(null);

  // Calculate active filter count
  const activeFilterCount = useMemo(() => {
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
    setCurrentPageState(0);
  }, [filters]);

  // Apply filters to data
  const filteredData = useMemo(() => {
    return data.filter((ioc) => {
      // Check if any type filter is active and if this IOC matches
      const hasActiveTypeFilters = Object.values(filters.types).some(
        (value) => value,
      );
      const matchesTypeFilter =
        !hasActiveTypeFilters || filters.types[ioc.type];
      if (!matchesTypeFilter) return false;

      // Check if any severity filter is active and if this IOC matches
      const hasActiveSeverityFilters = Object.values(filters.severities).some(
        (value) => value,
      );
      const matchesSeverityFilter =
        !hasActiveSeverityFilters || filters.severities[ioc.severity];
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
    if (externalControl) {
      // When externally controlled, don't sort the data here
      return filteredData;
    }

    // Use the internal or external sort parameters
    const effectiveSortField = externalControl
      ? (sortColumn ?? "timestamp")
      : sortField;
    const effectiveSortDir = externalControl
      ? (sortDirection ?? "desc")
      : sortDirectionState;

    return [...filteredData].sort((a, b) => {
      if (effectiveSortField === "timestamp") {
        return effectiveSortDir === "asc"
          ? new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          : new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      }

      if (effectiveSortField === "severity") {
        const severityOrder = { low: 0, medium: 1, high: 2, critical: 3 };
        return effectiveSortDir === "asc"
          ? severityOrder[a.severity] - severityOrder[b.severity]
          : severityOrder[b.severity] - severityOrder[a.severity];
      }

      // Default string comparison for other fields
      return effectiveSortDir === "asc"
        ? (a[effectiveSortField]?.toString() ?? "").localeCompare(
            b[effectiveSortField]?.toString() ?? "",
          )
        : (b[effectiveSortField]?.toString() ?? "").localeCompare(
            a[effectiveSortField]?.toString() ?? "",
          );
    });
  }, [
    filteredData,
    sortField,
    sortDirectionState,
    externalControl,
    sortColumn,
    sortDirection,
  ]);

  const paginatedData = useMemo(() => {
    if (externalControl) {
      // If externally controlled, use the entire dataset provided
      return data;
    }

    // Use internal pagination
    const effectivePageSize = externalControl ? pageSize : rowsPerPage;
    const effectiveCurrentPage = externalControl
      ? currentPage
      : currentPageState;

    const startIdx = effectiveCurrentPage * effectivePageSize;
    return sortedData.slice(startIdx, startIdx + effectivePageSize);
  }, [
    sortedData,
    currentPageState,
    externalControl,
    currentPage,
    pageSize,
    data,
  ]);

  const totalPages = useMemo(() => {
    if (externalControl && totalCount !== undefined) {
      return Math.ceil(totalCount / pageSize);
    }
    return Math.ceil(sortedData.length / rowsPerPage);
  }, [externalControl, totalCount, pageSize, sortedData.length, rowsPerPage]);

  // Toggle sort direction or set new sort field
  const handleSort = (field: keyof IOCData) => {
    if (externalControl && onSortChange) {
      // If externally controlled, call the provided callback
      const newDirection =
        field === sortColumn && sortDirection === "asc" ? "desc" : "asc";
      onSortChange(field, newDirection);
      return;
    }

    // Internal control
    if (sortField === field) {
      setSortDirectionState(sortDirectionState === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirectionState("desc"); // Default to descending for new sort field
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
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Get severity badge class based on severity level - using theme colors
  const getSeverityBadgeClass = (severity: IOCData["severity"]) => {
    const baseClasses = "text-xs px-2 py-1 rounded-full";
    switch (severity) {
      case "critical":
        return `${baseClasses} bg-critical/20 dark:bg-critical/20 text-critical dark:text-critical border border-critical/30 dark:border-critical/30`;
      case "high":
        return `${baseClasses} bg-high/20 dark:bg-high/20 text-high dark:text-high border border-high/30 dark:border-high/30`;
      case "medium":
        return `${baseClasses} bg-medium/20 dark:bg-medium/20 text-medium dark:text-medium border border-medium/30 dark:border-medium/30`;
      case "low":
        return `${baseClasses} bg-low/20 dark:bg-low/20 text-low dark:text-low border border-low/30 dark:border-low/30`;
      default:
        return `${baseClasses} bg-tag-bg dark:bg-tag-bg text-tag-text dark:text-tag-text border border-border dark:border-border`;
    }
  };

  // Get type badge class based on IOC type - using theme colors
  const getTypeBadgeClass = (type: IOCData["type"]) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (type) {
      case "ip":
        return `${baseClasses} bg-accent/20 dark:bg-accent/20 text-accent dark:text-accent border border-accent/30 dark:border-accent/30`;
      case "domain":
        return `${baseClasses} bg-low/20 dark:bg-low/20 text-low dark:text-low border border-low/30 dark:border-low/30`;
      case "file":
        return `${baseClasses} bg-primary/20 dark:bg-primary/20 text-primary dark:text-primary border border-primary/30 dark:border-primary/30`;
      case "url":
        return `${baseClasses} bg-chart-primary/20 dark:bg-chart-primary/20 text-chart-primary dark:text-chart-primary border border-chart-primary/30 dark:border-chart-primary/30`;
      case "email":
        return `${baseClasses} bg-high/20 dark:bg-high/20 text-high dark:text-high border border-high/30 dark:border-high/30`;
      default:
        return `${baseClasses} bg-tag-bg dark:bg-tag-bg text-tag-text dark:text-tag-text border border-border dark:border-border`;
    }
  };

  // Get confidence bar color based on confidence level - using theme colors
  const getConfidenceBarColor = (confidence: number) => {
    if (confidence > 90) return "bg-critical dark:bg-critical";
    if (confidence >= 70) return "bg-medium dark:bg-medium";
    return "bg-low dark:bg-low";
  };

  // Add a new function to share an IOC link
  const handleShareIoc = (
    e: React.MouseEvent<HTMLButtonElement>,
    ioc: IOCData,
  ) => {
    e.stopPropagation(); // Prevent opening the modal

    // Create a deep link URL
    const iocDetailUrl = `/threat-intel/${ioc.id}?from=table`;
    const fullUrl = `${window.location.origin}${iocDetailUrl}`;

    // Copy to clipboard
    navigator.clipboard
      .writeText(fullUrl)
      .then(() => {
        setCopiedRowId(ioc.id);
        setTimeout(() => setCopiedRowId(null), 2000);
      })
      .catch((err) => {
        console.error("Failed to copy URL: ", err);
      });
  };

  // Add a new function to handle viewing details in a new tab
  const handleViewDetails = (
    e: React.MouseEvent<HTMLButtonElement>,
    ioc: IOCData,
  ) => {
    e.stopPropagation(); // Prevent row click behavior

    // Create a deep link URL and open in new tab
    const iocDetailUrl = `/threat-intel/${ioc.id}?from=table`;
    window.open(iocDetailUrl, "_blank");
  };

  // Update pagination handlers
  const handlePageChange = (newPage: number) => {
    if (externalControl && onPageChange) {
      onPageChange(newPage);
    } else {
      setCurrentPageState(newPage);
    }
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
      {/* Filters with export option */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
        <IocTableFilters
          filters={filters}
          onFiltersChange={setFilters}
          onReset={handleResetFilters}
          activeFilterCount={activeFilterCount}
        />

        {/* Export button for table data */}
        {paginatedData.length > 0 && (
          <ExportReportButton
            data={sortedData}
            variant="outline"
            size="default"
            className="bg-background border-input text-foreground hover:bg-accent focus:ring-2 focus:ring-ring focus:outline-none"
          />
        )}
      </div>

      <div
        className={cn(
          "overflow-hidden rounded-md border border-zinc-700 bg-zinc-800",
          className,
        )}
      >
        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-700">
                <SortableColumnHeader
                  column="value"
                  label="IOC Value"
                  currentSortColumn={
                    externalControl ? (sortColumn ?? "timestamp") : sortField
                  }
                  currentSortDirection={
                    externalControl
                      ? (sortDirection ?? "desc")
                      : sortDirectionState
                  }
                  onSort={handleSort}
                />
                <SortableColumnHeader
                  column="type"
                  label="Type"
                  currentSortColumn={
                    externalControl ? (sortColumn ?? "timestamp") : sortField
                  }
                  currentSortDirection={
                    externalControl
                      ? (sortDirection ?? "desc")
                      : sortDirectionState
                  }
                  onSort={handleSort}
                />
                <SortableColumnHeader
                  column="severity"
                  label="Severity"
                  currentSortColumn={
                    externalControl ? (sortColumn ?? "timestamp") : sortField
                  }
                  currentSortDirection={
                    externalControl
                      ? (sortDirection ?? "desc")
                      : sortDirectionState
                  }
                  onSort={handleSort}
                />
                <SortableColumnHeader
                  column="confidence"
                  label="Confidence"
                  currentSortColumn={
                    externalControl ? (sortColumn ?? "timestamp") : sortField
                  }
                  currentSortDirection={
                    externalControl
                      ? (sortDirection ?? "desc")
                      : sortDirectionState
                  }
                  onSort={handleSort}
                />
                <SortableColumnHeader
                  column="timestamp"
                  label="Timestamp"
                  currentSortColumn={
                    externalControl ? (sortColumn ?? "timestamp") : sortField
                  }
                  currentSortDirection={
                    externalControl
                      ? (sortDirection ?? "desc")
                      : sortDirectionState
                  }
                  onSort={handleSort}
                  align="right"
                />
                <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">
                  <div className="flex items-center justify-end">Actions</div>
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((ioc) => (
                <tr
                  key={ioc.value || ioc.id || `ioc-${Math.random()}`}
                  className="bg-card hover:bg-accent/50 text-card-foreground border-b border-border transition-colors cursor-pointer"
                  onClick={() => handleRowClick(ioc)}
                >
                  <td className="px-4 py-2 text-foreground">
                    <code className="font-mono">{ioc.value}</code>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <span className={getTypeBadgeClass(ioc.type)}>
                      {ioc.type}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <span className={getSeverityBadgeClass(ioc.severity)}>
                      {ioc.severity}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <div className="flex items-center">
                      <div className="w-full bg-zinc-700 rounded-full h-2 mr-2 max-w-[100px]">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            getConfidenceBarColor(ioc.confidence),
                          )}
                          style={{ width: `${ioc.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {ioc.confidence}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm text-muted-foreground text-right">
                    <div className="flex items-center justify-end">
                      <Clock className="mr-1 h-3 w-3" />
                      {formatTimestamp(ioc.timestamp)}
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm text-muted-foreground text-right">
                    <div className="flex justify-end items-center space-x-2">
                      <button
                        className="p-1.5 rounded-md text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                        onClick={(e) => handleShareIoc(e, ioc)}
                        aria-label={`Share link to ${ioc.value}`}
                        title="Copy link to share"
                      >
                        {copiedRowId === ioc.id ? (
                          <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
                        ) : (
                          <Link className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        className="p-1.5 rounded-md text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                        onClick={(e) => handleViewDetails(e, ioc)}
                        aria-label={`View details for ${ioc.value}`}
                        title="Open in new tab"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {paginatedData.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-muted-foreground"
                  >
                    {sortedData.length === 0
                      ? "No IOCs match the current filters"
                      : "No IOC data available"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-border px-4 py-3 flex flex-col sm:flex-row gap-4 sm:items-center sm:justify-between">
            <div className="text-sm text-muted-foreground">
              {isLoading ? (
                <span className="animate-pulse">Loading results...</span>
              ) : externalControl && totalCount !== undefined ? (
                <>
                  Showing {totalCount > 0 ? currentPage * pageSize + 1 : 0} to{" "}
                  {Math.min((currentPage + 1) * pageSize, totalCount)} of{" "}
                  {totalCount} entries
                </>
              ) : (
                <>
                  Showing{" "}
                  {sortedData.length > 0
                    ? currentPageState * rowsPerPage + 1
                    : 0}{" "}
                  to{" "}
                  {Math.min(
                    (currentPageState + 1) * rowsPerPage,
                    sortedData.length,
                  )}{" "}
                  of {sortedData.length} entries
                </>
              )}
            </div>

            <PaginationControls
              currentPage={externalControl ? currentPage : currentPageState}
              totalPages={totalPages}
              onPageChange={handlePageChange}
              isLoading={isLoading}
            />
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
