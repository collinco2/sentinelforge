import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { Button } from "../components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "../components/ui/sheet";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { 
  Popover,
  PopoverContent,
  PopoverTrigger 
} from "../components/ui/popover";
import { 
  Calendar 
} from "../components/ui/calendar";
import { 
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { format } from "date-fns";
import { Calendar as CalendarIcon, Loader2, AlertCircle, Search, Filter, X } from "lucide-react";

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
}

interface IOC {
  ioc_value: string;
  value: string;
  ioc_type: string;
  score: number;
  severity: string;
  inferred?: boolean;
}

interface AlertIocsResponse {
  alert_id: string;
  alert_name: string;
  timestamp: number;
  formatted_time: string;
  total_iocs: number;
  iocs: IOC[];
}

const AlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [relatedIocs, setRelatedIocs] = useState<IOC[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [total, setTotal] = useState(0);
  
  // Filtering and pagination state
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  // Reset pagination when filters change
  useEffect(() => {
    setPage(0);
  }, [searchTerm, severityFilter, startDate, endDate]);

  // Fetch alerts when filters or pagination changes
  useEffect(() => {
    fetchAlerts();
  }, [page, pageSize, searchTerm, severityFilter, startDate, endDate]);

  const fetchAlerts = async () => {
    setIsLoading(true);
    setIsError(false);
    try {
      // Build query parameters
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: (page * pageSize).toString(),
      });
      
      if (searchTerm) {
        params.append("search", searchTerm);
      }
      
      if (severityFilter) {
        params.append("severity", severityFilter);
      }

      // Convert dates to timestamps if they exist
      if (startDate) {
        const startTimestamp = Math.floor(startDate.getTime() / 1000);
        params.append("start_date", startTimestamp.toString());
      }

      if (endDate) {
        // Set to end of day for the end date
        const endOfDay = new Date(endDate);
        endOfDay.setHours(23, 59, 59, 999);
        const endTimestamp = Math.floor(endOfDay.getTime() / 1000);
        params.append("end_date", endTimestamp.toString());
      }
      
      const response = await fetch(`/api/alerts?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      if (Array.isArray(data.alerts)) {
        setAlerts(data.alerts);
        setTotal(data.total || data.alerts.length);
      } else {
        throw new Error("Invalid response format");
      }
    } catch (error) {
      console.error("Error fetching alerts:", error);
      setIsError(true);
      setErrorMessage(error instanceof Error ? error.message : "Failed to fetch alerts");
      setAlerts([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAlertIocs = async (alertId: string) => {
    setDrawerLoading(true);
    try {
      const response = await fetch(`/api/alert/${alertId}/iocs`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data: AlertIocsResponse = await response.json();
      setRelatedIocs(data.iocs || []);
    } catch (error) {
      console.error("Error fetching related IOCs:", error);
      setRelatedIocs([]);
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleAlertClick = (alert: Alert) => {
    setSelectedAlert(alert);
    setIsDrawerOpen(true);
    fetchAlertIocs(alert.id);
  };

  const clearFilters = () => {
    setSearchTerm("");
    setSeverityFilter("");
    setStartDate(null);
    setEndDate(null);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return "bg-red-500 hover:bg-red-600";
      case "high":
        return "bg-orange-500 hover:bg-orange-600";
      case "medium":
        return "bg-yellow-500 hover:bg-yellow-600";
      case "low":
        return "bg-blue-500 hover:bg-blue-600";
      default:
        return "bg-gray-500 hover:bg-gray-600";
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "text-green-500";
    if (confidence >= 50) return "text-yellow-500";
    return "text-red-500";
  };

  const getIocTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "domain":
        return "bg-purple-500 hover:bg-purple-600";
      case "ip":
        return "bg-blue-500 hover:bg-blue-600";
      case "url":
        return "bg-green-500 hover:bg-green-600";
      case "hash":
        return "bg-orange-500 hover:bg-orange-600";
      case "email":
        return "bg-teal-500 hover:bg-teal-600";
      default:
        return "bg-gray-500 hover:bg-gray-600";
    }
  };
  
  const formatDateToDisplay = (date: Date | null) => {
    return date ? format(date, "PPP") : "Select date";
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar />
        
        <main className="flex-1 overflow-y-auto p-6">
          <div className="flex flex-col space-y-4 md:space-y-0 md:flex-row md:justify-between md:items-center mb-6">
            <h1 className="text-2xl font-bold">Security Alerts</h1>

            <div className="flex flex-wrap gap-2">
              <Button 
                variant="outline"
                onClick={() => navigate('/alerts/timeline')}
                className="hidden md:flex items-center gap-1"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
                Timeline View
              </Button>
              
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search alerts..."
                  className="w-full md:w-64 pl-8"
                  value={searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
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
          
          {/* Mobile Timeline Link */}
          <div className="md:hidden mb-4">
            <Button 
              variant="outline"
              onClick={() => navigate('/alerts/timeline')}
              className="w-full flex items-center justify-center gap-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
              View Alerts Timeline
            </Button>
          </div>

          {/* Filters Panel */}
          {filtersVisible && (
            <Card className="mb-6">
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
                          {...{
                            mode: "single",
                            selected: startDate,
                            onSelect: setStartDate,
                            initialFocus: true
                          } as any}
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
                          {...{
                            mode: "single",
                            selected: endDate,
                            onSelect: setEndDate,
                            initialFocus: true
                          } as any}
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>

                <div className="flex justify-end mt-4">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={clearFilters}
                  >
                    Clear Filters
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          
          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Alert ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Threat Type</TableHead>
                  </TableRow>
                </TableHeader>
                
                <TableBody>
                  {isLoading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-24 text-center">
                        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                        <p className="mt-2 text-sm text-muted-foreground">Loading alerts...</p>
                      </TableCell>
                    </TableRow>
                  ) : isError ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-24 text-center">
                        <AlertCircle className="h-6 w-6 mx-auto text-red-500" />
                        <p className="mt-2 text-sm text-red-500">Error loading alerts</p>
                        <p className="text-xs text-muted-foreground">{errorMessage}</p>
                      </TableCell>
                    </TableRow>
                  ) : alerts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-24 text-center">
                        <AlertCircle className="h-6 w-6 mx-auto text-muted-foreground" />
                        <p className="mt-2 text-sm text-muted-foreground">No alerts found</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    alerts.map((alert) => (
                      <TableRow 
                        key={alert.id} 
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => handleAlertClick(alert)}
                      >
                        <TableCell className="font-mono text-xs">{alert.id}</TableCell>
                        <TableCell className="font-medium">{alert.name}</TableCell>
                        <TableCell>
                          <Badge variant="secondary" className={`${getSeverityColor(alert.severity)} text-white`}>
                            {alert.severity}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className={`font-semibold ${getConfidenceColor(alert.confidence)}`}>
                            {alert.confidence}%
                          </span>
                        </TableCell>
                        <TableCell>{alert.formatted_time}</TableCell>
                        <TableCell>{alert.source}</TableCell>
                        <TableCell>{alert.threat_type}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
            
            <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-2 border-t border-border">
              <div className="text-sm text-muted-foreground mb-2 sm:mb-0">
                Showing {total > 0 ? Math.min(page * pageSize + 1, total) : 0} - {Math.min((page + 1) * pageSize, total)} of {total} alerts
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
                    <SelectItem value="100">100 per page</SelectItem>
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
        </main>
      </div>
      
      {/* IOCs Detail Drawer */}
      <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedAlert && (
            <SheetHeader className="mb-4">
              <SheetTitle>{selectedAlert.name}</SheetTitle>
              <SheetDescription>
                <div className="flex flex-wrap gap-2 items-center mt-2">
                  <Badge variant="secondary" className={`${getSeverityColor(selectedAlert.severity)} text-white`}>
                    {selectedAlert.severity}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {selectedAlert.formatted_time}
                  </span>
                  <span className="text-sm">
                    Source: <span className="font-medium">{selectedAlert.source}</span>
                  </span>
                  <span className="text-sm">
                    Confidence: <span className={`font-semibold ${getConfidenceColor(selectedAlert.confidence)}`}>
                      {selectedAlert.confidence}%
                    </span>
                  </span>
                </div>
                <p className="text-sm mt-4">{selectedAlert.description}</p>
              </SheetDescription>
            </SheetHeader>
          )}
          
          <div className="mt-6">
            <h3 className="text-lg font-medium mb-4">Related IOCs</h3>
            
            {drawerLoading ? (
              <div className="flex flex-col items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
                <p className="mt-2 text-sm text-muted-foreground">Loading IOCs...</p>
              </div>
            ) : relatedIocs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No IOCs found for this alert</p>
              </div>
            ) : (
              <div className="space-y-4">
                {relatedIocs.map((ioc, index) => (
                  <div key={index} className="p-4 bg-card border border-border rounded-md">
                    <div className="flex flex-wrap items-start justify-between mb-2 gap-2">
                      <div className="font-mono text-sm break-all">{ioc.value || ioc.ioc_value}</div>
                      <Badge variant="outline" className={`${getIocTypeColor(ioc.ioc_type)} text-white ml-2`}>
                        {ioc.ioc_type}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      <div className="text-sm">
                        Score: <span className="font-semibold">{ioc.score.toFixed(1)}</span>
                      </div>
                      {ioc.inferred && (
                        <Badge variant="outline" className="bg-gray-500 text-white">
                          Inferred
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
};

export { AlertsPage }; 