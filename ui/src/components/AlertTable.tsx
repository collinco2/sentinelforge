import React, { useState, useEffect, useCallback } from "react";
import { Button } from "./ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

import { Input } from "./ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { Calendar } from "./ui/calendar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { format } from "date-fns";
import {
  Calendar as CalendarIcon,
  Loader2,
  AlertCircle,
  Search,
  Filter,
  X,
  ChevronUp,
  ChevronDown,
  Clock,
} from "lucide-react";
import { AlertDetailModal } from "./AlertDetailModal";
import { AlertTimelineView } from "./AlertTimelineView";

// Types for our data
interface Alert {
  id: string;
  name: string;
  severity: string;
  timestamp: number;
  formatted_time: string;
  threat_type: string;
  confidence: number;
  description: string;
  source: string;
  risk_score: number; // 0-100 risk assessment
  overridden_risk_score?: number; // 0-100 analyst override
}

export function AlertTable() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isTimelineOpen, setIsTimelineOpen] = useState(false);
  const [timelineAlertId, setTimelineAlertId] = useState<number | null>(null);
  const [total, setTotal] = useState(0);

  // Filtering and pagination state
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  // Sorting state
  const [sortField, setSortField] = useState<
    "id" | "name" | "timestamp" | "risk_score"
  >("id");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    try {
      // Build query parameters for the new API
      const params = new URLSearchParams({
        page: (page + 1).toString(),
        limit: pageSize.toString(),
        sort: sortField,
        order: sortOrder,
      });

      if (searchTerm) {
        params.append("name", searchTerm);
      }

      const response = await fetch(`/api/alerts?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        // New API returns simple array
        setAlerts(data);
        setTotal(data.length);
      } else if (Array.isArray(data.alerts)) {
        // Fallback for old API format
        setAlerts(data.alerts);
        setTotal(data.total || data.alerts.length);
      } else {
        throw new Error("Invalid response format");
      }
    } catch (error) {
      console.error("Error fetching alerts:", error);
      setIsError(true);
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to fetch alerts",
      );
      setAlerts([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, searchTerm, sortField, sortOrder]);

  // Reset pagination when filters or sorting changes
  useEffect(() => {
    setPage(0);
  }, [searchTerm, severityFilter, startDate, endDate, sortField, sortOrder]);

  // Fetch alerts when filters or pagination changes
  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleAlertClick = (alert: Alert) => {
    setSelectedAlert(alert);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedAlert(null);
  };

  const handleAlertUpdate = () => {
    // Refresh alerts when an alert is updated (e.g., risk score override)
    fetchAlerts();
  };

  const handleTimelineClick = (alert: Alert) => {
    setTimelineAlertId(parseInt(alert.id));
    setIsTimelineOpen(true);
  };

  const handleTimelineClose = () => {
    setIsTimelineOpen(false);
    setTimelineAlertId(null);
  };

  const clearFilters = () => {
    setSearchTerm("");
    setSeverityFilter("");
    setStartDate(null);
    setEndDate(null);
  };

  const formatDateToDisplay = (date: Date | null) => {
    return date ? format(date, "PPP") : "Select date";
  };

  // Handle column header click for sorting
  const handleSort = (field: "id" | "name" | "timestamp" | "risk_score") => {
    if (sortField === field) {
      // Toggle sort order if clicking the same field
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      // Switch to new field with ascending order
      setSortField(field);
      setSortOrder("asc");
    }
  };

  // Get sort indicator icon for a column
  const getSortIcon = (field: "id" | "name" | "timestamp" | "risk_score") => {
    if (sortField !== field) {
      return null; // No icon for non-sorted columns
    }
    return sortOrder === "asc" ? (
      <ChevronUp className="h-4 w-4" />
    ) : (
      <ChevronDown className="h-4 w-4" />
    );
  };

  // Get risk score badge color and style
  const getRiskScoreBadge = (alert: Alert) => {
    const effectiveScore = alert.overridden_risk_score ?? alert.risk_score;
    const isOverridden =
      alert.overridden_risk_score !== null &&
      alert.overridden_risk_score !== undefined;

    let badgeClass = "";
    let textClass = "text-white font-medium";

    if (effectiveScore >= 80) {
      badgeClass = "bg-red-500 hover:bg-red-600";
    } else if (effectiveScore >= 50) {
      badgeClass = "bg-orange-500 hover:bg-orange-600";
    } else {
      badgeClass = "bg-green-500 hover:bg-green-600";
    }

    const tooltipText = isOverridden
      ? `Risk Score: ${effectiveScore}/100 (Overridden by analyst from ${alert.risk_score})`
      : `Risk Score: ${effectiveScore}/100`;

    return (
      <div
        className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs ${badgeClass} ${textClass} ${isOverridden ? "font-bold" : ""}`}
        title={tooltipText}
        aria-label={
          isOverridden
            ? `Risk score ${effectiveScore} out of 100, overridden by analyst from ${alert.risk_score}`
            : `Risk score ${effectiveScore} out of 100`
        }
      >
        {effectiveScore > 90 && <span>🔥</span>}
        {effectiveScore}
        {isOverridden && <span className="ml-1">✏️</span>}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Search and Filter Controls */}
      <div className="flex flex-col space-y-4 md:space-y-0 md:flex-row md:justify-between md:items-center">
        <div className="flex flex-wrap gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search alerts..."
              className="w-full md:w-64 pl-8"
              value={searchTerm}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setSearchTerm(e.target.value)
              }
            />
          </div>

          <Button
            variant="outline"
            size="icon"
            onClick={() => setFiltersVisible(!filtersVisible)}
            className="relative"
          >
            <Filter size={18} />
            {(severityFilter || startDate || endDate) && (
              <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-primary"></span>
            )}
          </Button>
        </div>
      </div>

      {/* Filters Panel */}
      {filtersVisible && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg">Filters</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFiltersVisible(false)}
                className="h-8 w-8 p-0"
              >
                <X size={16} />
              </Button>
            </div>
            <CardDescription>
              Refine alerts based on severity and time range
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Severity</label>
                <Select
                  value={severityFilter}
                  onValueChange={setSeverityFilter}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="All Severities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Severities</SelectItem>
                    <SelectItem value="Critical">Critical</SelectItem>
                    <SelectItem value="High">High</SelectItem>
                    <SelectItem value="Medium">Medium</SelectItem>
                    <SelectItem value="Low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Start Date</label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full justify-start text-left font-normal"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {formatDateToDisplay(startDate)}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      {...({
                        mode: "single",
                        selected: startDate,
                        onSelect: setStartDate,
                        initialFocus: true,
                      } as any)}
                    />
                  </PopoverContent>
                </Popover>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">End Date</label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full justify-start text-left font-normal"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {formatDateToDisplay(endDate)}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      {...({
                        mode: "single",
                        selected: endDate,
                        onSelect: setEndDate,
                        initialFocus: true,
                      } as any)}
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            <div className="flex justify-end mt-4">
              <Button variant="outline" size="sm" onClick={clearFilters}>
                Clear Filters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts Table */}
      <div className="bg-card rounded-lg border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">
                  <button
                    className="flex items-center gap-1 hover:text-foreground transition-colors font-medium"
                    onClick={() => handleSort("id")}
                    aria-label="Sort by Alert ID"
                  >
                    Alert ID
                    {getSortIcon("id")}
                  </button>
                </TableHead>
                <TableHead>
                  <button
                    className="flex items-center gap-1 hover:text-foreground transition-colors font-medium"
                    onClick={() => handleSort("name")}
                    aria-label="Sort by Title"
                  >
                    Title
                    {getSortIcon("name")}
                  </button>
                </TableHead>
                <TableHead className="w-[120px]">
                  <button
                    className="flex items-center gap-1 hover:text-foreground transition-colors font-medium"
                    onClick={() => handleSort("risk_score")}
                    aria-label="Sort by Risk Score"
                    title="Sort alerts by risk score (0-100)"
                  >
                    Risk Score
                    {getSortIcon("risk_score")}
                  </button>
                </TableHead>
                <TableHead className="hidden md:table-cell">
                  Description
                </TableHead>
                <TableHead className="w-[140px]">Actions</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    <p className="mt-2 text-sm text-muted-foreground">
                      Loading alerts...
                    </p>
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center">
                    <AlertCircle className="h-6 w-6 mx-auto text-red-500" />
                    <p className="mt-2 text-sm text-red-500">
                      Error loading alerts
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {errorMessage}
                    </p>
                  </TableCell>
                </TableRow>
              ) : alerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center">
                    <AlertCircle className="h-6 w-6 mx-auto text-muted-foreground" />
                    <p className="mt-2 text-sm text-muted-foreground">
                      No alerts found
                    </p>
                  </TableCell>
                </TableRow>
              ) : (
                alerts.map((alert) => (
                  <TableRow key={alert.id} className="hover:bg-muted/50">
                    <TableCell className="font-mono text-xs">
                      {alert.id}
                    </TableCell>
                    <TableCell className="font-medium">{alert.name}</TableCell>
                    <TableCell className="text-center">
                      {getRiskScoreBadge(alert)}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm text-muted-foreground max-w-md truncate">
                      {alert.description}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAlertClick(alert);
                          }}
                          className="h-8 px-2 text-xs"
                        >
                          Details
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleTimelineClick(alert);
                          }}
                          className="h-8 px-2 text-xs"
                        >
                          <Clock className="h-3 w-3 mr-1" />
                          Timeline
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-2 border-t border-border">
          <div className="text-sm text-muted-foreground mb-2 sm:mb-0">
            Showing {total > 0 ? Math.min(page * pageSize + 1, total) : 0} -{" "}
            {Math.min((page + 1) * pageSize, total)} of {total} alerts
          </div>

          <div className="flex items-center gap-2">
            <Select
              value={pageSize.toString()}
              onValueChange={(value) => setPageSize(parseInt(value))}
            >
              <SelectTrigger className="w-[100px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10 per page</SelectItem>
                <SelectItem value="25">25 per page</SelectItem>
                <SelectItem value="50">50 per page</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={(page + 1) * pageSize >= total}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Detail Modal */}
      <AlertDetailModal
        alert={selectedAlert}
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onAlertUpdate={handleAlertUpdate}
      />

      {/* Alert Timeline View */}
      {isTimelineOpen && timelineAlertId && (
        <AlertTimelineView
          alertId={timelineAlertId}
          onClose={handleTimelineClose}
        />
      )}
    </div>
  );
}
