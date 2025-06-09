import React from "react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import {
  Home,
  BarChart2,
  Shield,
  AlertCircle,
  AlertTriangle,
  Settings,
  PanelLeft,
  Users,
  Database,
  UploadCloud,
  HeartPulse,
  Eye,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { useSidebar } from "../hooks/useSidebar";

interface SidebarProps {
  className?: string;
}

interface NavItem {
  icon: React.ElementType;
  label: string;
  path: string;
  requiredRoles?: UserRole[];
}

export function Sidebar({ className }: SidebarProps) {
  const { hasRole } = useAuth();
  const { isCollapsed, toggle } = useSidebar();

  // Detect if running in development mode
  const isDevelopment = process.env.NODE_ENV === "development";

  // Flattened navigation items with role-based access
  const allNavItems: NavItem[] = [
    { icon: Home, label: "Dashboard", path: "/dashboard" },
    { icon: BarChart2, label: "Threat Dashboard", path: "/threat-dashboard" },
    { icon: Eye, label: "Threat Monitor", path: "/threat-monitor" },
    { icon: Shield, label: "IOC Analysis", path: "/ioc-analysis" },
    { icon: Database, label: "IOC Management", path: "/ioc-management" },
    { icon: AlertTriangle, label: "Alerts", path: "/alerts" },
    { icon: AlertCircle, label: "Threats", path: "/threats" },

    // Feed-related items (flattened from previous nested structure)
    {
      icon: Database,
      label: "Feeds",
      path: "/feeds",
      requiredRoles: [UserRole.ANALYST, UserRole.ADMIN],
    },
    {
      icon: UploadCloud,
      label: "Upload",
      path: "/feed-upload",
      requiredRoles: [UserRole.ANALYST, UserRole.ADMIN],
    },
    {
      icon: HeartPulse,
      label: "Feed Health",
      path: "/feed-health",
      requiredRoles: [UserRole.ANALYST, UserRole.ADMIN],
    },

    // Settings and admin items
    { icon: Settings, label: "Settings", path: "/settings" },
    {
      icon: Users,
      label: "Role Management",
      path: "/role-management",
      requiredRoles: [UserRole.ADMIN],
    },
  ];

  // Filter navigation items based on user roles
  const navItems = allNavItems.filter((item) => {
    if (!item.requiredRoles) return true;
    return hasRole(item.requiredRoles);
  });

  return (
    <TooltipProvider>
      <div
        className={cn(
          "flex flex-col bg-card border-r border-border transition-all duration-300 h-screen",
          isCollapsed ? "w-16" : "w-64",
          className,
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-border">
          {!isCollapsed && (
            <div className="font-semibold text-lg text-foreground">
              <div>SentinelForge</div>
              {isDevelopment && (
                <div className="text-xs text-amber-600 dark:text-amber-400 font-normal">
                  🔧 Development Mode
                </div>
              )}
            </div>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="ml-auto"
                onClick={toggle}
                aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                <PanelLeft
                  size={20}
                  className={cn(
                    "transition-transform duration-200",
                    isCollapsed ? "rotate-180" : "rotate-0",
                  )}
                />
                <span className="sr-only">
                  {isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                </span>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>Toggle Sidebar</p>
            </TooltipContent>
          </Tooltip>
        </div>

        <nav className="flex-1 py-4 overflow-y-auto">
          <ul className="space-y-1 px-2">
            {navItems.map((item) => (
              <li key={item.path}>
                {isCollapsed ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <NavLink
                        to={item.path}
                        className={({ isActive }) =>
                          cn(
                            "flex items-center justify-center w-full text-sm font-medium rounded-md transition-colors px-2 py-3",
                            "hover:bg-muted hover:text-foreground",
                            isActive
                              ? "bg-muted text-primary font-semibold"
                              : "text-muted-foreground",
                          )
                        }
                      >
                        <item.icon size={20} />
                      </NavLink>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <p>{item.label}</p>
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center w-full text-sm font-medium rounded-md transition-colors px-3 py-2",
                        "hover:bg-muted hover:text-foreground",
                        isActive
                          ? "bg-muted text-primary font-semibold"
                          : "text-muted-foreground",
                      )
                    }
                  >
                    <item.icon size={20} className="mr-3" />
                    <span>{item.label}</span>
                  </NavLink>
                )}
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
            {!isCollapsed && (
              <div className="ml-3">
                <p className="text-sm font-medium">User</p>
                <p className="text-xs text-muted-foreground">Analyst</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
