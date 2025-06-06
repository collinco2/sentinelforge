import React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Moon, Bell, Search, LogOut, User } from "lucide-react";
import { UserRoleSelector } from "./UserRoleSelector";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useAuth } from "../hooks/useAuth";

interface TopbarProps {
  className?: string;
  title?: string;
}

export function Topbar({ className, title = "Dashboard" }: TopbarProps) {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    // Redirect to login page
    window.location.href = "/login";
  };

  return (
    <div
      className={cn(
        "sticky top-0 z-10 w-full h-16 px-4 border-b border-border bg-card/80 backdrop-blur flex items-center justify-between",
        className,
      )}
    >
      <div className="flex items-center">
        <h1 className="text-xl font-semibold text-foreground">{title}</h1>
      </div>

      <div className="flex items-center space-x-4">
        {/* User Role Selector */}
        <UserRoleSelector />

        <div className="flex items-center space-x-2">
          <div className="relative hidden md:flex items-center">
            <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search..."
              className="pl-9 pr-4 py-2 h-9 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-input"
            />
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground"
            aria-label="Toggle theme"
          >
            <Moon size={20} />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground"
            aria-label="Notifications"
          >
            <Bell size={20} />
          </Button>

          {/* User Menu */}
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground"
                aria-label="User menu"
              >
                <User size={20} />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-2" align="end">
              <div className="space-y-2">
                {user && (
                  <div className="px-2 py-1.5 text-sm">
                    <div className="font-medium text-foreground">
                      {user.username}
                    </div>
                    <div className="text-muted-foreground">{user.role}</div>
                  </div>
                )}
                <div className="border-t border-border my-1"></div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  onClick={handleLogout}
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </Button>
              </div>
            </PopoverContent>
          </Popover>

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-muted-foreground"
            aria-label="Search"
          >
            <Search size={20} />
          </Button>
        </div>
      </div>
    </div>
  );
}
