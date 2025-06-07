import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";

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
  const [isMobileView, setIsMobileView] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Handle responsive sidebar visibility
  useEffect(() => {
    const handleResize = () => {
      setIsMobileView(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      } else {
        setSidebarOpen(true);
      }
    };

    // Set initial state
    handleResize();

    // Add event listener
    window.addEventListener("resize", handleResize);

    // Clean up
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar - hidden on mobile when closed */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-20 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <Sidebar />
      </div>

      {/* Main content area */}
      <div className="flex flex-col flex-1 w-full md:w-[calc(100%-16rem)] md:ml-auto">
        <Topbar title={title} />
        
        <main
          className={cn(
            "flex-1 overflow-auto p-4 md:p-6",
            className
          )}
        >
          {children}
        </main>

        {/* Overlay for mobile sidebar */}
        {isMobileView && sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-10"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
} 