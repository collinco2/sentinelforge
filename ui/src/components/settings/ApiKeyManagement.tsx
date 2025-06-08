import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import {
  Key,
  Plus,
  Trash2,
  RefreshCw,
  Copy,
  Eye,
  EyeOff,
  Calendar,
  Shield,
} from "lucide-react";
import { toast } from "../../lib/toast";

interface ApiKey {
  id: string;
  name: string;
  key_preview: string;
  created_at: string;
  last_used: string | null;
  access_scope: string[];
  is_active: boolean;
}

export const ApiKeyManagement: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [showFullKey, setShowFullKey] = useState(false);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      const response = await fetch("/api/user/api-keys", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.api_keys || []);
      } else {
        console.error("Failed to fetch API keys");
        toast.error("Failed to load API keys");
      }
    } catch (error) {
      console.error("Error fetching API keys:", error);
      toast.error("Error loading API keys");
    } finally {
      setLoading(false);
    }
  };

  const createApiKey = async () => {
    if (!newKeyName.trim()) {
      toast.error("Please enter a name for the API key");
      return;
    }

    setCreating(true);
    try {
      const response = await fetch("/api/user/api-keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify({
          name: newKeyName.trim(),
          access_scope: ["read", "write"], // Default scope
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setNewlyCreatedKey(data.api_key);
        setNewKeyName("");
        await fetchApiKeys();
        toast.success("API key created successfully");
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to create API key");
      }
    } catch (error) {
      console.error("Error creating API key:", error);
      toast.error("Error creating API key");
    } finally {
      setCreating(false);
    }
  };

  const revokeApiKey = async (keyId: string, keyName: string) => {
    if (
      !window.confirm(
        `Are you sure you want to revoke the API key "${keyName}"? This action cannot be undone.`,
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`/api/user/api-keys/${keyId}`, {
        method: "DELETE",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        await fetchApiKeys();
        toast.success("API key revoked successfully");
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to revoke API key");
      }
    } catch (error) {
      console.error("Error revoking API key:", error);
      toast.error("Error revoking API key");
    }
  };

  const rotateApiKey = async (keyId: string, keyName: string) => {
    if (
      !window.confirm(
        `Are you sure you want to rotate the API key "${keyName}"? The old key will be invalidated.`,
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`/api/user/api-keys/${keyId}/rotate`, {
        method: "POST",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNewlyCreatedKey(data.api_key);
        await fetchApiKeys();
        toast.success("API key rotated successfully");
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to rotate API key");
      }
    } catch (error) {
      console.error("Error rotating API key:", error);
      toast.error("Error rotating API key");
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        toast.success("Copied to clipboard");
      })
      .catch(() => {
        toast.error("Failed to copy to clipboard");
      });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <Card data-testid="api-key-management">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Keys
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="api-key-management">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Keys
          </div>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm" data-testid="create-api-key-button">
                <Plus className="h-4 w-4 mr-2" />
                Create Key
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New API Key</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="key-name">Key Name</Label>
                  <Input
                    id="key-name"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="Enter a descriptive name"
                    data-testid="api-key-name-input"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowCreateDialog(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={createApiKey}
                    disabled={creating}
                    data-testid="confirm-create-key"
                  >
                    {creating ? "Creating..." : "Create Key"}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Newly Created Key Display */}
        {newlyCreatedKey && (
          <div className="p-4 border rounded-lg bg-green-50 dark:bg-green-900/20">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  New API Key Created
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  value={
                    showFullKey
                      ? newlyCreatedKey
                      : `${newlyCreatedKey.substring(0, 8)}...`
                  }
                  readOnly
                  className="font-mono text-sm"
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowFullKey(!showFullKey)}
                >
                  {showFullKey ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(newlyCreatedKey)}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-green-700 dark:text-green-300">
                Save this key securely. You won't be able to see it again.
              </p>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setNewlyCreatedKey(null)}
              >
                Dismiss
              </Button>
            </div>
          </div>
        )}

        {/* API Keys List */}
        {apiKeys.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Key className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No API keys created yet</p>
            <p className="text-sm">Create your first API key to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {apiKeys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{key.name}</span>
                    <Badge variant={key.is_active ? "default" : "secondary"}>
                      {key.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="font-mono">{key.key_preview}</span>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Created {formatDate(key.created_at)}
                    </div>
                    {key.last_used && (
                      <span>Last used {formatDate(key.last_used)}</span>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {key.access_scope.map((scope) => (
                      <Badge key={scope} variant="outline" className="text-xs">
                        {scope}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => rotateApiKey(key.id, key.name)}
                    data-testid={`rotate-key-${key.id}`}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => revokeApiKey(key.id, key.name)}
                    className="text-red-600 hover:text-red-700"
                    data-testid={`revoke-key-${key.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Help Text */}
        <div className="pt-4 border-t">
          <p className="text-xs text-gray-500">
            API keys provide programmatic access to SentinelForge. Keep them
            secure and rotate them regularly. Use the API documentation to learn
            how to authenticate your requests.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
