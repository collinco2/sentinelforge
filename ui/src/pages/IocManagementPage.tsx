import React, { useState } from "react";
import { DashboardLayout } from "../layout/DashboardLayout";
import { IocTable, IOCData } from "../components/IocTable";
import { IocDetailModal } from "../components/IocDetailModal";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Plus,
  Upload,
  Download,
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { useIocs } from "../hooks/useIocs";
import { defaultFilters } from "../components/FilterSidebar";
import { toast } from "../lib/toast";

interface IocFormData {
  value: string;
  type: "ip" | "domain" | "file" | "url" | "email";
  severity: "low" | "medium" | "high" | "critical";
  source: string;
  tags: string;
  description: string;
}

const initialFormData: IocFormData = {
  value: "",
  type: "ip",
  severity: "medium",
  source: "",
  tags: "",
  description: "",
};

export function IocManagementPage() {
  const { hasRole } = useAuth();
  const { iocs, isLoading, mutate } = useIocs(defaultFilters);

  // State management
  const [selectedIoc, setSelectedIoc] = useState<IOCData | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [formData, setFormData] = useState<IocFormData>(initialFormData);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Permission checks
  const canModify = hasRole([UserRole.ANALYST, UserRole.ADMIN]);
  // const canDelete = hasRole([UserRole.ADMIN]); // TODO: Implement delete functionality

  // Filter IOCs based on search and filters
  const filteredIocs = iocs.filter((ioc) => {
    const matchesSearch = ioc.value
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === "all" || ioc.type === typeFilter;
    const matchesSeverity =
      severityFilter === "all" || ioc.severity === severityFilter;
    return matchesSearch && matchesType && matchesSeverity;
  });

  // Handle IOC row click
  const handleIocRowClick = (ioc: IOCData) => {
    setSelectedIoc(ioc);
    setIsDetailModalOpen(true);
  };

  // Handle form input changes
  const handleInputChange = (field: keyof IocFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Handle create IOC
  const handleCreateIoc = async () => {
    if (!canModify) {
      toast.error("You don't have permission to create IOCs");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch("/api/iocs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify({
          ioc_type: formData.type,
          ioc_value: formData.value,
          severity: formData.severity,
          source: formData.source,
          tags: formData.tags
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean),
          description: formData.description,
        }),
      });

      if (response.ok) {
        toast.success("IOC created successfully");
        setIsCreateModalOpen(false);
        setFormData(initialFormData);
        mutate();
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to create IOC");
      }
    } catch (error) {
      toast.error("Failed to create IOC");
      console.error("Error creating IOC:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle bulk import
  const handleBulkImport = () => {
    // TODO: Implement bulk import functionality
    toast.info("Bulk import functionality coming soon");
  };

  // Handle export
  const handleExport = () => {
    // TODO: Implement export functionality
    toast.info("Export functionality coming soon");
  };

  return (
    <DashboardLayout title="IOC Management">
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              IOC Management
            </h1>
            <p className="text-muted-foreground">
              Manage Indicators of Compromise (IOCs) for threat intelligence
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {canModify && (
              <Dialog
                open={isCreateModalOpen}
                onOpenChange={setIsCreateModalOpen}
              >
                <DialogTrigger asChild>
                  <Button className="bg-purple-600 hover:bg-purple-700 text-white">
                    <Plus className="h-4 w-4 mr-2" />
                    Add IOC
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>Create New IOC</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="ioc-value">IOC Value</Label>
                      <Input
                        id="ioc-value"
                        placeholder="e.g., 192.168.1.1, malicious.com"
                        value={formData.value}
                        onChange={(e) =>
                          handleInputChange("value", e.target.value)
                        }
                      />
                    </div>

                    <div>
                      <Label htmlFor="ioc-type">Type</Label>
                      <Select
                        value={formData.type}
                        onValueChange={(value) =>
                          handleInputChange("type", value)
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ip">IP Address</SelectItem>
                          <SelectItem value="domain">Domain</SelectItem>
                          <SelectItem value="url">URL</SelectItem>
                          <SelectItem value="file">File Hash</SelectItem>
                          <SelectItem value="email">Email</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="ioc-severity">Severity</Label>
                      <Select
                        value={formData.severity}
                        onValueChange={(value) =>
                          handleInputChange("severity", value)
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="critical">Critical</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="ioc-source">Source</Label>
                      <Input
                        id="ioc-source"
                        placeholder="e.g., Manual Entry, OSINT"
                        value={formData.source}
                        onChange={(e) =>
                          handleInputChange("source", e.target.value)
                        }
                      />
                    </div>

                    <div>
                      <Label htmlFor="ioc-tags">Tags (comma-separated)</Label>
                      <Input
                        id="ioc-tags"
                        placeholder="e.g., malware, phishing, apt"
                        value={formData.tags}
                        onChange={(e) =>
                          handleInputChange("tags", e.target.value)
                        }
                      />
                    </div>

                    <div>
                      <Label htmlFor="ioc-description">Description</Label>
                      <Textarea
                        id="ioc-description"
                        placeholder="Additional context about this IOC"
                        value={formData.description}
                        onChange={(e) =>
                          handleInputChange("description", e.target.value)
                        }
                        rows={3}
                      />
                    </div>

                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setIsCreateModalOpen(false)}
                        disabled={isSubmitting}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleCreateIoc}
                        disabled={isSubmitting || !formData.value}
                      >
                        {isSubmitting ? "Creating..." : "Create IOC"}
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            )}

            <Button variant="outline" onClick={handleBulkImport}>
              <Upload className="h-4 w-4 mr-2" />
              Import
            </Button>

            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>

            <Button variant="outline" onClick={() => mutate()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total IOCs</p>
                  <p className="text-2xl font-bold">{iocs.length}</p>
                </div>
                <AlertCircle className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Critical</p>
                  <p className="text-2xl font-bold text-red-500">
                    {iocs.filter((ioc) => ioc.severity === "critical").length}
                  </p>
                </div>
                <AlertCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">High</p>
                  <p className="text-2xl font-bold text-orange-500">
                    {iocs.filter((ioc) => ioc.severity === "high").length}
                  </p>
                </div>
                <AlertCircle className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Active Filters
                  </p>
                  <p className="text-2xl font-bold">
                    {(searchTerm ? 1 : 0) +
                      (typeFilter !== "all" ? 1 : 0) +
                      (severityFilter !== "all" ? 1 : 0)}
                  </p>
                </div>
                <Filter className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search IOCs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="ip">IP</SelectItem>
                    <SelectItem value="domain">Domain</SelectItem>
                    <SelectItem value="url">URL</SelectItem>
                    <SelectItem value="file">File</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={severityFilter}
                  onValueChange={setSeverityFilter}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Severity" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Severities</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Active Filters Display */}
            {(searchTerm ||
              typeFilter !== "all" ||
              severityFilter !== "all") && (
              <div className="flex flex-wrap gap-2 mt-4">
                {searchTerm && (
                  <Badge
                    variant="secondary"
                    className="flex items-center gap-1"
                  >
                    Search: {searchTerm}
                    <button
                      onClick={() => setSearchTerm("")}
                      className="ml-1 hover:bg-muted rounded-full p-0.5"
                    >
                      ×
                    </button>
                  </Badge>
                )}
                {typeFilter !== "all" && (
                  <Badge
                    variant="secondary"
                    className="flex items-center gap-1"
                  >
                    Type: {typeFilter}
                    <button
                      onClick={() => setTypeFilter("all")}
                      className="ml-1 hover:bg-muted rounded-full p-0.5"
                    >
                      ×
                    </button>
                  </Badge>
                )}
                {severityFilter !== "all" && (
                  <Badge
                    variant="secondary"
                    className="flex items-center gap-1"
                  >
                    Severity: {severityFilter}
                    <button
                      onClick={() => setSeverityFilter("all")}
                      className="ml-1 hover:bg-slate-700 rounded-full p-0.5"
                    >
                      ×
                    </button>
                  </Badge>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* IOC Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>IOC List ({filteredIocs.length} items)</span>
              {!canModify && (
                <Badge variant="outline" className="text-xs">
                  Read-only access
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <IocTable
              data={filteredIocs}
              isLoading={isLoading}
              onRowClick={handleIocRowClick}
              noInternalModal={true}
              className="w-full"
            />
          </CardContent>
        </Card>
      </div>

      {/* IOC Detail Modal */}
      <IocDetailModal
        ioc={selectedIoc}
        isOpen={isDetailModalOpen}
        onOpenChange={setIsDetailModalOpen}
        sourceContext="ioc-management"
      />
    </DashboardLayout>
  );
}
