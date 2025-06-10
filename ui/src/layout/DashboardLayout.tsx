import React from "react";
import { cn } from "@/lib/utils";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { useSidebar } from "@/hooks/useSidebar";
interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
}

export function DashboardLayout({
  children,
  title = "Dashboard",
  className,
}: DashboardLayoutProps) {
  const { isCollapsed, isMobile, close } = useSidebar();

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Sidebar */}
      <div
        className={cn(
          "transition-all duration-300 ease-in-out",
          isMobile ? "fixed inset-y-0 left-0 z-20" : "relative",
          isMobile && isCollapsed ? "-translate-x-full" : "translate-x-0",
        )}
      >
        <Sidebar />
      </div>

      {/* Main content area */}
      <div
        className={cn(
          "flex flex-col flex-1 transition-all duration-300",
          isMobile
            ? "w-full"
            : isCollapsed
              ? "w-[calc(100%-4rem)]"
              : "w-[calc(100%-16rem)]",
        )}
      >
        <Topbar title={title} />

        <main className={cn("flex-1 overflow-auto p-4 md:p-6", className)}>
          {children}
        </main>

        {/* Overlay for mobile sidebar when expanded */}
        {isMobile && !isCollapsed && (
          <div
            className="fixed inset-0 bg-black/50 z-10"
            onClick={close}
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
}
