import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Home,
  BarChart2,
  Shield,
  AlertCircle,
  AlertTriangle,
  Settings,
  Menu,
  X,
  Users,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";

interface SidebarProps {
  className?: string;
}

interface NavItem {
  icon: React.ElementType;
  label: string;
  path: string;
  active?: boolean;
}

export function Sidebar({ className }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [activePath, setActivePath] = useState("/dashboard");
  const { hasRole } = useAuth();

  // Base navigation items
  const baseNavItems: NavItem[] = [
    { icon: Home, label: "Dashboard", path: "/dashboard", active: true },
    { icon: Shield, label: "IOC Analysis", path: "/ioc-analysis" },
    { icon: AlertTriangle, label: "Alerts", path: "/alerts" },
    { icon: AlertCircle, label: "Threats", path: "/threats" },
    { icon: BarChart2, label: "Reports", path: "/reports" },
    { icon: Settings, label: "Settings", path: "/settings" },
  ];

  // Add admin-only items
  const navItems: NavItem[] = [
    ...baseNavItems,
    ...(hasRole([UserRole.ADMIN])
      ? [{ icon: Users, label: "Role Management", path: "/role-management" }]
      : []),
  ];

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  const handleNavClick = (path: string) => {
    setActivePath(path);
    // In a real app, you would use router navigation here
  };

  return (
    <div
      className={cn(
        "flex flex-col bg-card border-r border-border transition-all duration-300 h-screen",
        collapsed ? "w-16" : "w-64",
        className,
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-border">
        {!collapsed && (
          <div className="font-semibold text-lg text-foreground">
            SentinelForge
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto"
          onClick={toggleSidebar}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <Menu size={20} /> : <X size={20} />}
        </Button>
      </div>

      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <Button
                variant="ghost"
                className={cn(
                  "w-full justify-start text-sm font-medium",
                  activePath === item.path
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:text-foreground",
                  collapsed ? "justify-center px-0" : "px-3",
                )}
                onClick={() => handleNavClick(item.path)}
              >
                <item.icon size={20} className={cn(collapsed ? "" : "mr-2")} />
                {!collapsed && <span>{item.label}</span>}
              </Button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-border">
        <div className="flex items-center">
          <div
            className="h-8 w-8 rounded-full bg-muted flex items-center justify-center"
            aria-label="Profile"
          >
            <span className="text-xs font-medium">U</span>
          </div>
          {!collapsed && (
            <div className="ml-3">
              <p className="text-sm font-medium">User</p>
              <p className="text-xs text-muted-foreground">Analyst</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
