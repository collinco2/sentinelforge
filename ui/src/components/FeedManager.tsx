import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Switch } from "./ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  AlertCircle,
  Download,
  Edit,
  Plus,
  Trash2,
  Clock,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { toast } from "../lib/toast";
import { useThemeClass, getStatusBadgeClass } from "../hooks/useThemeClass";

interface ThreatFeed {
  id: number;
  name: string;
  description: string;
  url: string;
  feed_type: string;
  format_config: Record<string, any>;
  is_active: boolean;
  auto_import: boolean;
  import_frequency: number;
  last_import: string | null;
  last_import_status: string | null;
  last_import_count: number;
  created_by: number;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

interface ImportLog {
  id: number;
  feed_id: number | null;
  feed_name: string;
  import_type: string;
  file_name: string | null;
  file_size: number | null;
  total_records: number;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: string[];
  import_status: string;
  duration_seconds: number | null;
  user_id: number;
  user_name: string;
  justification: string | null;
  timestamp: string;
}

interface FeedHealth {
  feed_id: number;
  feed_name: string;
  url: string;
  status: string;
  http_code: number | null;
  response_time_ms: number | null;
  error_message: string | null;
  last_checked: string;
  checked_by: string;
}

export const FeedManager: React.FC = () => {
  const { hasRole } = useAuth();
  const theme = useThemeClass();
  const [feeds, setFeeds] = useState<ThreatFeed[]>([]);
  const [importLogs, setImportLogs] = useState<ImportLog[]>([]);
  const [feedHealth, setFeedHealth] = useState<FeedHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingFeed, setEditingFeed] = useState<ThreatFeed | null>(null);
  const [importingFeedId, setImportingFeedId] = useState<number | null>(null);

  // Form state for creating/editing feeds
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    url: "",
    feed_type: "csv",
    is_active: true,
    auto_import: false,
    import_frequency: 24,
  });

  const canModify = hasRole([UserRole.ANALYST, UserRole.ADMIN]);
  const canDelete = hasRole([UserRole.ADMIN]);

  useEffect(() => {
    fetchFeeds();
    fetchImportLogs();
    fetchFeedHealth();
  }, []);

  const fetchFeeds = async () => {
    try {
      const response = await fetch("/api/feeds", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFeeds(data.feeds);
      } else {
        toast.error("Failed to fetch feeds");
      }
    } catch (error) {
      toast.error("Error fetching feeds");
    }
  };

  const fetchImportLogs = async () => {
    try {
      const response = await fetch("/api/feeds/import-logs?limit=20", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setImportLogs(data.logs);
      }
    } catch (error) {
      console.error("Error fetching import logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFeedHealth = async () => {
    try {
      const response = await fetch("/api/feeds/health", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFeedHealth(data.health_checks || []);
      }
    } catch (error) {
      console.error("Error fetching feed health:", error);
    }
  };

  const handleCreateFeed = async () => {
    try {
      const response = await fetch("/api/feeds", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Feed created successfully");
        setShowCreateDialog(false);
        resetForm();
        fetchFeeds();
        fetchFeedHealth();
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to create feed");
      }
    } catch (error) {
      toast.error("Error creating feed");
    }
  };

  const handleUpdateFeed = async () => {
    if (!editingFeed) return;

    try {
      const response = await fetch(`/api/feeds/${editingFeed.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Feed updated successfully");
        setEditingFeed(null);
        resetForm();
        fetchFeeds();
        fetchFeedHealth();
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to update feed");
      }
    } catch (error) {
      toast.error("Error updating feed");
    }
  };

  const handleDeleteFeed = async (feedId: number) => {
    if (!window.confirm("Are you sure you want to delete this feed?")) return;

    try {
      const response = await fetch(`/api/feeds/${feedId}`, {
        method: "DELETE",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        toast.success("Feed deleted successfully");
        fetchFeeds();
        fetchFeedHealth();
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to delete feed");
      }
    } catch (error) {
      toast.error("Error deleting feed");
    }
  };

  const handleImportFeed = async (feedId: number) => {
    const justification = window.prompt(
      "Enter justification for this import (optional):",
    );

    setImportingFeedId(feedId);
    try {
      const response = await fetch(`/api/feeds/${feedId}/import`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify({ justification }),
      });

      const result = await response.json();

      if (response.ok) {
        toast.success(
          `Import completed: ${result.imported_count} imported, ${result.skipped_count} skipped, ${result.error_count} errors`,
        );
        fetchFeeds();
        fetchImportLogs();
        fetchFeedHealth();
      } else {
        toast.error(result.error || "Import failed");
      }
    } catch (error) {
      toast.error("Error importing feed");
    } finally {
      setImportingFeedId(null);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      url: "",
      feed_type: "csv",
      is_active: true,
      auto_import: false,
      import_frequency: 24,
    });
  };

  const startEdit = (feed: ThreatFeed) => {
    setEditingFeed(feed);
    setFormData({
      name: feed.name,
      description: feed.description,
      url: feed.url,
      feed_type: feed.feed_type,
      is_active: feed.is_active,
      auto_import: feed.auto_import,
      import_frequency: feed.import_frequency,
    });
  };

  const getStatusIcon = (status: string | null) => {
    switch (status) {
      case "success":
        return (
          <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
        );
      case "partial":
        return (
          <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
        );
      case "failed":
        return <XCircle className="h-4 w-4 text-destructive" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, "success" | "warning" | "error" | "info" | "default"> = {
      success: "success",
      partial: "warning",
      failed: "error",
      pending: "info",
    };

    const statusType = statusMap[status] || "default";

    return (
      <Badge className={getStatusBadgeClass(statusType)}>
        {status}
      </Badge>
    );
  };

  const getHealthStatusChip = (status: string) => {
    switch (status) {
      case "ok":
        return {
          label: "Healthy",
          className:
            "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800",
        };
      case "timeout":
      case "unauthorized":
      case "rate_limited":
        return {
          label: "Stale",
          className:
            "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800",
        };
      case "unreachable":
      case "server_error":
        return {
          label: "Error",
          className:
            "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800",
        };
      default:
        return {
          label: "Unknown",
          className: "bg-muted text-muted-foreground border-border",
        };
    }
  };

  const getFeedHealth = (feedId: number): FeedHealth | null => {
    return feedHealth.find((health) => health.feed_id === feedId) || null;
  };

  const formatHealthTooltip = (health: FeedHealth | null): string => {
    if (!health) {
      return "Health status unknown";
    }

    const parts = [
      `Status: ${health.status}`,
      health.http_code ? `HTTP Code: ${health.http_code}` : null,
      health.response_time_ms
        ? `Response Time: ${health.response_time_ms}ms`
        : null,
      `Last Checked: ${new Date(health.last_checked).toLocaleString()}`,
    ].filter(Boolean);

    if (health.error_message) {
      parts.push(`Error: ${health.error_message}`);
    }

    return parts.join("\n");
  };

  const getSourceLogo = (feedName: string) => {
    const name = feedName.toLowerCase();

    // Known threat intelligence sources
    const sourceMap: Record<
      string,
      { logo?: string; initials: string; color: string; name: string }
    > = {
      // Government Sources
      cisa: { initials: "CI", color: "bg-blue-600", name: "CISA" },
      "us-cert": { initials: "UC", color: "bg-blue-600", name: "US-CERT" },
      fbi: { initials: "FB", color: "bg-blue-800", name: "FBI" },
      dhs: { initials: "DH", color: "bg-blue-700", name: "DHS" },

      // Commercial Sources
      alienvault: {
        initials: "AV",
        color: "bg-purple-600",
        name: "AlienVault OTX",
      },
      otx: { initials: "OT", color: "bg-purple-600", name: "AlienVault OTX" },
      virustotal: { initials: "VT", color: "bg-green-600", name: "VirusTotal" },
      malwarebytes: {
        initials: "MB",
        color: "bg-orange-600",
        name: "Malwarebytes",
      },
      crowdstrike: { initials: "CS", color: "bg-red-600", name: "CrowdStrike" },
      fireeye: { initials: "FE", color: "bg-red-500", name: "FireEye" },
      mandiant: { initials: "MD", color: "bg-red-500", name: "Mandiant" },
      "palo alto": {
        initials: "PA",
        color: "bg-orange-500",
        name: "Palo Alto",
      },
      unit42: { initials: "U4", color: "bg-orange-500", name: "Unit 42" },

      // Open Source / Community
      malwaredomainlist: {
        initials: "MD",
        color: "bg-gray-600",
        name: "MalwareDomainList",
      },
      spamhaus: { initials: "SH", color: "bg-yellow-600", name: "Spamhaus" },
      "abuse.ch": { initials: "AC", color: "bg-indigo-600", name: "Abuse.ch" },
      urlhaus: { initials: "UH", color: "bg-indigo-600", name: "URLhaus" },
      "malware bazaar": {
        initials: "MZ",
        color: "bg-indigo-600",
        name: "Malware Bazaar",
      },
      phishtank: { initials: "PT", color: "bg-cyan-600", name: "PhishTank" },
      openphish: { initials: "OP", color: "bg-cyan-500", name: "OpenPhish" },
      ipsum: { initials: "IP", color: "bg-gray-700", name: "IPsum" },
      emergingthreats: {
        initials: "ET",
        color: "bg-red-700",
        name: "Emerging Threats",
      },
      proofpoint: { initials: "PP", color: "bg-blue-500", name: "Proofpoint" },

      // MISP and TAXII
      misp: { initials: "MI", color: "bg-green-700", name: "MISP" },
      taxii: { initials: "TX", color: "bg-purple-700", name: "TAXII" },
      stix: { initials: "ST", color: "bg-purple-700", name: "STIX" },

      // Custom/Manual
      manual: { initials: "MN", color: "bg-gray-500", name: "Manual Upload" },
      custom: { initials: "CU", color: "bg-gray-500", name: "Custom Feed" },
      internal: {
        initials: "IN",
        color: "bg-slate-600",
        name: "Internal Feed",
      },
    };

    // Try to match feed name with known sources
    for (const [key, source] of Object.entries(sourceMap)) {
      if (name.includes(key)) {
        return source;
      }
    }

    // Fallback: generate initials from feed name
    const words = feedName.split(/[\s\-_]+/).filter((word) => word.length > 0);
    const initials =
      words.length >= 2
        ? `${words[0][0]}${words[1][0]}`.toUpperCase()
        : words[0]
          ? words[0].substring(0, 2).toUpperCase()
          : "TF";

    return {
      initials,
      color: "bg-slate-500",
      name: feedName,
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Threat Feed Management
          </h1>
          <p className="text-muted-foreground">
            Manage external threat intelligence feeds
          </p>
        </div>
        {canModify && (
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button onClick={() => resetForm()}>
                <Plus className="h-4 w-4 mr-2" />
                Add Feed
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Create New Feed</DialogTitle>
              </DialogHeader>
              <FeedForm
                formData={formData}
                setFormData={setFormData}
                onSubmit={handleCreateFeed}
                onCancel={() => setShowCreateDialog(false)}
              />
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Feeds List */}
      <Card className={theme.card}>
        <CardHeader>
          <CardTitle>Registered Feeds ({feeds.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {feeds.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              No feeds configured. Add your first threat feed to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {feeds.map((feed) => (
                <div
                  key={feed.id}
                  className="border border-slate-600 rounded-lg p-4 bg-slate-800/30 hover:bg-slate-700/30 transition-colors"
                >
                  {/* Mobile-optimized layout */}
                  <div className="space-y-4">
                    {/* Header section with source icon, name, and health status */}
                    <div className="flex items-start gap-3">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Avatar className="h-10 w-10 flex-shrink-0 cursor-help">
                              {getSourceLogo(feed.name).logo ? (
                                <AvatarImage
                                  src={getSourceLogo(feed.name).logo}
                                  alt={`${getSourceLogo(feed.name).name} logo`}
                                />
                              ) : null}
                              <AvatarFallback
                                className={`text-white text-sm font-semibold ${getSourceLogo(feed.name).color}`}
                              >
                                {getSourceLogo(feed.name).initials}
                              </AvatarFallback>
                            </Avatar>
                          </TooltipTrigger>
                          <TooltipContent side="top">
                            <div className="text-xs">
                              <div className="font-medium">Source</div>
                              <div>{getSourceLogo(feed.name).name}</div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-foreground truncate text-base">
                            {feed.name}
                          </h3>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge
                                  className={`text-xs font-medium border cursor-help flex-shrink-0 ${
                                    getHealthStatusChip(
                                      getFeedHealth(feed.id)?.status ||
                                        "unknown",
                                    ).className
                                  }`}
                                >
                                  {
                                    getHealthStatusChip(
                                      getFeedHealth(feed.id)?.status ||
                                        "unknown",
                                    ).label
                                  }
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent side="top" className="max-w-xs">
                                <div className="text-xs space-y-1">
                                  <div className="font-medium">
                                    Health Status
                                  </div>
                                  <pre className="whitespace-pre-wrap">
                                    {formatHealthTooltip(
                                      getFeedHealth(feed.id),
                                    )}
                                  </pre>
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>

                        {/* Status badges - stacked on mobile */}
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge
                            variant={feed.is_active ? "default" : "secondary"}
                            className="flex-shrink-0"
                          >
                            {feed.is_active ? "Active" : "Inactive"}
                          </Badge>
                          <Badge variant="outline" className="flex-shrink-0">
                            {feed.feed_type.toUpperCase()}
                          </Badge>
                          {feed.auto_import && (
                            <Badge
                              variant="outline"
                              className="text-blue-600 flex-shrink-0"
                            >
                              Auto Import
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    {feed.description && (
                      <div className="px-1">
                        <p className="text-slate-300 text-sm leading-relaxed">
                          {feed.description}
                        </p>
                      </div>
                    )}

                    {/* Metadata - stacked on mobile for better readability */}
                    <div className="px-1 space-y-2">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="font-medium">Created by:</span>
                        <span>{feed.created_by_username}</span>
                      </div>
                      {feed.last_import && (
                        <div className="flex items-start gap-2 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1 flex-shrink-0 mt-0.5">
                            {getStatusIcon(feed.last_import_status)}
                            <span className="font-medium">Last import:</span>
                          </div>
                          <div className="flex flex-col sm:flex-row sm:items-center sm:gap-1">
                            <span>
                              {new Date(feed.last_import).toLocaleDateString()}
                            </span>
                            <span className="text-xs">
                              ({feed.last_import_count} IOCs)
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Action buttons - full width on mobile, inline on desktop */}
                    <div className="flex flex-col sm:flex-row gap-2 pt-3 border-t border-border">
                      <div className="flex gap-2 flex-1">
                        {canModify && feed.url && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleImportFeed(feed.id)}
                            disabled={importingFeedId === feed.id}
                            className="flex items-center justify-center gap-2 flex-1 sm:flex-initial min-h-[44px]"
                            aria-label={`Import feed ${feed.name}`}
                          >
                            {importingFeedId === feed.id ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
                            ) : (
                              <Download className="h-4 w-4" />
                            )}
                            <span>Import</span>
                          </Button>
                        )}

                        {canModify && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => startEdit(feed)}
                            className="flex items-center justify-center gap-2 flex-1 sm:flex-initial min-h-[44px]"
                            aria-label={`Edit feed ${feed.name}`}
                          >
                            <Edit className="h-4 w-4" />
                            <span>Edit</span>
                          </Button>
                        )}

                        {canDelete && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteFeed(feed.id)}
                            className="text-destructive hover:text-destructive/80 flex items-center justify-center gap-2 flex-1 sm:flex-initial min-h-[44px]"
                            aria-label={`Delete feed ${feed.name}`}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span>Delete</span>
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Import Logs */}
      <Card className={theme.card}>
        <CardHeader>
          <CardTitle>Recent Import Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {importLogs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No import activity yet.
            </div>
          ) : (
            <div className="space-y-3">
              {importLogs.slice(0, 10).map((log) => (
                <div key={log.id} className="p-4 border rounded-lg space-y-3">
                  {/* Header with feed name and status */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="font-medium truncate">
                        {log.feed_name}
                      </span>
                      {getStatusBadge(log.import_status)}
                    </div>
                    <div className="text-sm text-muted-foreground flex-shrink-0">
                      {new Date(log.timestamp).toLocaleString()}
                    </div>
                  </div>

                  {/* Import details */}
                  <div className="space-y-1">
                    <div className="text-sm text-muted-foreground">
                      <span className="font-medium">{log.imported_count}</span>{" "}
                      imported,{" "}
                      <span className="font-medium">{log.skipped_count}</span>{" "}
                      skipped,{" "}
                      <span className="font-medium">{log.error_count}</span>{" "}
                      errors
                      {log.duration_seconds && (
                        <span className="text-muted-foreground/70">
                          {" "}
                          • {log.duration_seconds}s
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      by {log.user_name}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Feed Dialog */}
      {editingFeed && (
        <Dialog open={!!editingFeed} onOpenChange={() => setEditingFeed(null)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Edit Feed: {editingFeed.name}</DialogTitle>
            </DialogHeader>
            <FeedForm
              formData={formData}
              setFormData={setFormData}
              onSubmit={handleUpdateFeed}
              onCancel={() => setEditingFeed(null)}
              isEditing
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

// Feed Form Component
interface FeedFormProps {
  formData: any;
  setFormData: (data: any) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isEditing?: boolean;
}

const FeedForm: React.FC<FeedFormProps> = ({
  formData,
  setFormData,
  onSubmit,
  onCancel,
  isEditing = false,
}) => {
  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="name">Feed Name</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Enter feed name"
        />
      </div>

      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) =>
            setFormData({ ...formData, description: e.target.value })
          }
          placeholder="Enter feed description"
          rows={3}
        />
      </div>

      <div>
        <Label htmlFor="url">Feed URL</Label>
        <Input
          id="url"
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          placeholder="https://example.com/feed.csv"
        />
      </div>

      <div>
        <Label htmlFor="feed_type">Feed Type</Label>
        <Select
          value={formData.feed_type}
          onValueChange={(value) =>
            setFormData({ ...formData, feed_type: value })
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="csv">CSV</SelectItem>
            <SelectItem value="json">JSON</SelectItem>
            <SelectItem value="txt">Text</SelectItem>
            <SelectItem value="stix">STIX</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="is_active"
          checked={formData.is_active}
          onCheckedChange={(checked) =>
            setFormData({ ...formData, is_active: checked })
          }
        />
        <Label htmlFor="is_active">Active</Label>
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="auto_import"
          checked={formData.auto_import}
          onCheckedChange={(checked) =>
            setFormData({ ...formData, auto_import: checked })
          }
        />
        <Label htmlFor="auto_import">Auto Import</Label>
      </div>

      {formData.auto_import && (
        <div>
          <Label htmlFor="import_frequency">Import Frequency (hours)</Label>
          <Input
            id="import_frequency"
            type="number"
            value={formData.import_frequency}
            onChange={(e) =>
              setFormData({
                ...formData,
                import_frequency: parseInt(e.target.value),
              })
            }
            min="1"
            max="168"
          />
        </div>
      )}

      <div className="flex justify-end space-x-2 pt-4">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={onSubmit}>
          {isEditing ? "Update" : "Create"} Feed
        </Button>
      </div>
    </div>
  );
};
