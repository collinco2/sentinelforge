/**
 * 🛡️ Role Management Panel - Admin-only User Role Management
 *
 * This component allows administrators to view and manage user roles
 * in the SentinelForge system with comprehensive audit logging.
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Users,
  Shield,
  Eye,
  Settings,
  User,
  AlertCircle,
  Loader2,
  Filter,
  History,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { useToast } from "./ui/use-toast";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import {
  getUsers,
  updateUserRole,
  getRoleChangeAuditLogs,
  User as ApiUser,
  RoleChangeAuditLog,
} from "../services/api";

interface RoleManagementPanelProps {
  className?: string;
}

export function RoleManagementPanel({ className }: RoleManagementPanelProps) {
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<ApiUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<RoleChangeAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("all");
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingUpdate, setPendingUpdate] = useState<{
    userId: number;
    newRole: string;
    username: string;
  } | null>(null);
  const [showAuditLogs, setShowAuditLogs] = useState(false);

  const { user: currentUser, hasRole } = useAuth();
  const { toast } = useToast();

  // Check if current user is admin
  const isAdmin = hasRole([UserRole.ADMIN]);

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getUsers();
      setUsers(response.users);
      setFilteredUsers(response.users);
    } catch (error) {
      console.error("Error loading users:", error);
      toast({
        title: "Error",
        description: "Failed to load users. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const loadAuditLogs = useCallback(async () => {
    try {
      const auditResponse = await getRoleChangeAuditLogs({ limit: 50 });
      setAuditLogs(auditResponse.audit_logs);
    } catch (error) {
      console.error("Error loading audit logs:", error);
    }
  }, []);

  useEffect(() => {
    if (isAdmin) {
      loadUsers();
      loadAuditLogs();
    }
  }, [isAdmin, loadUsers, loadAuditLogs]);

  // Filter users by role
  useEffect(() => {
    if (selectedRole === "all") {
      setFilteredUsers(users);
    } else {
      setFilteredUsers(users.filter((user) => user.role === selectedRole));
    }
  }, [users, selectedRole]);

  const handleRoleChange = (
    userId: number,
    newRole: string,
    username: string,
  ) => {
    // Prevent admin from demoting themselves
    if (currentUser?.user_id === userId && newRole !== "admin") {
      toast({
        title: "Action Not Allowed",
        description: "You cannot change your own role.",
        variant: "destructive",
      });
      return;
    }

    setPendingUpdate({ userId, newRole, username });
    setShowConfirmDialog(true);
  };

  const confirmRoleUpdate = async () => {
    if (!pendingUpdate) return;

    try {
      setUpdating(pendingUpdate.userId);
      setShowConfirmDialog(false);

      await updateUserRole(
        pendingUpdate.userId,
        pendingUpdate.newRole as "viewer" | "analyst" | "auditor" | "admin",
      );

      // Update local state
      setUsers((prev) =>
        prev.map((user) =>
          user.user_id === pendingUpdate.userId
            ? { ...user, role: pendingUpdate.newRole as any }
            : user,
        ),
      );

      // Reload audit logs
      loadAuditLogs();

      toast({
        title: "Role Updated",
        description: `${pendingUpdate.username}'s role has been changed to ${pendingUpdate.newRole}.`,
      });
    } catch (error: any) {
      console.error("Error updating role:", error);
      toast({
        title: "Update Failed",
        description:
          error.response?.data?.message || "Failed to update user role.",
        variant: "destructive",
      });
    } finally {
      setUpdating(null);
      setPendingUpdate(null);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "admin":
        return <Settings className="h-4 w-4" />;
      case "analyst":
        return <Shield className="h-4 w-4" />;
      case "auditor":
        return <Eye className="h-4 w-4" />;
      case "viewer":
        return <User className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "analyst":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "auditor":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
      case "viewer":
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Show access denied if not admin
  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Access Denied
          </h3>
          <p className="text-muted-foreground">
            You need administrator privileges to access role management.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading users...</span>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground flex items-center">
              <Users className="h-6 w-6 mr-2 text-primary" />
              Role Management
            </h2>
            <p className="text-muted-foreground">
              Manage user roles and permissions
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => setShowAuditLogs(!showAuditLogs)}
            className="flex items-center"
          >
            <History className="h-4 w-4 mr-2" />
            {showAuditLogs ? "Hide" : "Show"} Audit Trail
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-foreground">
              <Filter className="h-5 w-5 mr-2 text-primary" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label htmlFor="role-filter" className="text-sm font-medium text-foreground">
                  Filter by Role:
                </label>
                <Select value={selectedRole} onValueChange={setSelectedRole}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Roles</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="analyst">Analyst</SelectItem>
                    <SelectItem value="auditor">Auditor</SelectItem>
                    <SelectItem value="viewer">Viewer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="text-sm text-muted-foreground">
                Showing {filteredUsers.length} of {users.length} users
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Users Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-foreground">Users ({filteredUsers.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Current Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {getRoleIcon(user.role)}
                        <span className="font-medium text-foreground">{user.username}</span>
                        {user.user_id === currentUser?.user_id && (
                          <Badge variant="outline" className="text-xs">
                            You
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{user.email}</TableCell>
                    <TableCell>
                      <Badge className={getRoleColor(user.role)}>
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? "default" : "secondary"}>
                        {user.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(user.created_at)}</TableCell>
                    <TableCell>
                      <Select
                        value={user.role}
                        onValueChange={(newRole) =>
                          handleRoleChange(user.user_id, newRole, user.username)
                        }
                        disabled={updating === user.user_id}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                          {updating === user.user_id && (
                            <Loader2 className="h-4 w-4 animate-spin ml-2" />
                          )}
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="viewer">Viewer</SelectItem>
                          <SelectItem value="analyst">Analyst</SelectItem>
                          <SelectItem value="auditor">Auditor</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Audit Trail */}
        {showAuditLogs && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <History className="h-5 w-5 mr-2" />
                Role Change Audit Trail
              </CardTitle>
            </CardHeader>
            <CardContent>
              {auditLogs.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">
                  No role changes recorded yet.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Admin</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell>{formatDate(log.timestamp)}</TableCell>
                        <TableCell>{log.admin_username}</TableCell>
                        <TableCell>
                          <Badge variant="outline">Role Change</Badge>
                        </TableCell>
                        <TableCell className="max-w-md">
                          <span className="text-sm">{log.justification}</span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Role Change</DialogTitle>
            <DialogDescription>
              Are you sure you want to change{" "}
              <strong>{pendingUpdate?.username}</strong>'s role to{" "}
              <strong>{pendingUpdate?.newRole}</strong>?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowConfirmDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={confirmRoleUpdate}>Confirm Change</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
