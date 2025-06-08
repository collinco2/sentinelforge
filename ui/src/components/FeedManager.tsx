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
  AlertCircle,
  Download,
  Edit,
  Plus,
  Trash2,
  Upload,
  Clock,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { toast } from "../lib/toast";

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

export const FeedManager: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [feeds, setFeeds] = useState<ThreatFeed[]>([]);
  const [importLogs, setImportLogs] = useState<ImportLog[]>([]);
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
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "partial":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      success: "bg-green-100 text-green-800",
      partial: "bg-yellow-100 text-yellow-800",
      failed: "bg-red-100 text-red-800",
      pending: "bg-blue-100 text-blue-800",
    };

    return (
      <Badge className={variants[status] || "bg-gray-100 text-gray-800"}>
        {status}
      </Badge>
    );
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
          <h1 className="text-2xl font-bold text-gray-900">
            Threat Feed Management
          </h1>
          <p className="text-gray-600">
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
      <Card>
        <CardHeader>
          <CardTitle>Registered Feeds ({feeds.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {feeds.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No feeds configured. Add your first threat feed to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {feeds.map((feed) => (
                <div
                  key={feed.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {feed.name}
                        </h3>
                        <Badge
                          variant={feed.is_active ? "default" : "secondary"}
                        >
                          {feed.is_active ? "Active" : "Inactive"}
                        </Badge>
                        <Badge variant="outline">
                          {feed.feed_type.toUpperCase()}
                        </Badge>
                        {feed.auto_import && (
                          <Badge variant="outline" className="text-blue-600">
                            Auto Import
                          </Badge>
                        )}
                      </div>

                      {feed.description && (
                        <p className="text-gray-600 text-sm mb-2">
                          {feed.description}
                        </p>
                      )}

                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>Created by {feed.created_by_username}</span>
                        {feed.last_import && (
                          <div className="flex items-center gap-1">
                            {getStatusIcon(feed.last_import_status)}
                            <span>
                              Last import:{" "}
                              {new Date(feed.last_import).toLocaleDateString()}(
                              {feed.last_import_count} IOCs)
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {canModify && feed.url && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleImportFeed(feed.id)}
                          disabled={importingFeedId === feed.id}
                        >
                          {importingFeedId === feed.id ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
                          ) : (
                            <Download className="h-4 w-4" />
                          )}
                          Import
                        </Button>
                      )}

                      {canModify && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => startEdit(feed)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      )}

                      {canDelete && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteFeed(feed.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Import Logs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Import Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {importLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No import activity yet.
            </div>
          ) : (
            <div className="space-y-3">
              {importLogs.slice(0, 10).map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium">{log.feed_name}</span>
                      {getStatusBadge(log.import_status)}
                      <span className="text-sm text-gray-500">
                        by {log.user_name}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      {log.imported_count} imported, {log.skipped_count}{" "}
                      skipped, {log.error_count} errors
                      {log.duration_seconds && ` • ${log.duration_seconds}s`}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(log.timestamp).toLocaleString()}
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
