/**
 * 🛡️ User Role Selector Component
 *
 * This component allows switching between different user roles for testing
 * the RBAC functionality in SentinelForge.
 */

import React from "react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { useAuth } from "../hooks/useAuth";
import { UserRole, authService } from "../services/auth";
import { User, Shield, Eye, Settings } from "lucide-react";

export function UserRoleSelector() {
  const { user, setDemoUser, isLoading } = useAuth();

  const demoUsers = authService.getDemoUsers();

  const handleRoleChange = (userId: string) => {
    setDemoUser(parseInt(userId));
  };

  const getRoleIcon = (role: UserRole) => {
    switch (role) {
      case UserRole.ADMIN:
        return <Settings className="h-4 w-4" />;
      case UserRole.ANALYST:
        return <Shield className="h-4 w-4" />;
      case UserRole.AUDITOR:
        return <Eye className="h-4 w-4" />;
      case UserRole.VIEWER:
        return <User className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getRoleColor = (role: UserRole) => {
    return authService.getRoleColor(role);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
        Loading user...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      {/* Current User Display */}
      {user && (
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className={`${getRoleColor(user.role)} text-white border-none`}
          >
            {getRoleIcon(user.role)}
            <span className="ml-1">
              {authService.getRoleDisplayName(user.role)}
            </span>
          </Badge>
          <span className="text-sm text-gray-300">{user.username}</span>
        </div>
      )}

      {/* Role Selector */}
      <Select
        value={user?.user_id.toString() || ""}
        onValueChange={handleRoleChange}
      >
        <SelectTrigger className="w-[180px] bg-zinc-800 border-zinc-700 text-gray-300">
          <SelectValue placeholder="Select role..." />
        </SelectTrigger>
        <SelectContent className="bg-zinc-800 border-zinc-700">
          {demoUsers.map((demoUser) => (
            <SelectItem
              key={demoUser.id}
              value={demoUser.id.toString()}
              className="text-gray-300 focus:bg-zinc-700 focus:text-white"
            >
              <div className="flex items-center gap-2">
                {getRoleIcon(demoUser.role)}
                <span>{authService.getRoleDisplayName(demoUser.role)}</span>
                <span className="text-xs text-gray-400">
                  ({demoUser.username})
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Permissions Display */}
      {user && (
        <div className="flex items-center gap-1 text-xs">
          {user.permissions.can_override_risk_scores && (
            <Badge
              variant="outline"
              className="bg-blue-500/20 text-blue-300 border-blue-500/30"
            >
              Override
            </Badge>
          )}
          {user.permissions.can_view_audit_trail && (
            <Badge
              variant="outline"
              className="bg-purple-500/20 text-purple-300 border-purple-500/30"
            >
              Audit
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}
