/**
 * 🛡️ Role Management Page - Admin-only User Role Management
 *
 * This page provides a dedicated interface for administrators to manage
 * user roles and view audit trails in the SentinelForge system.
 */

import React from "react";
import { Sidebar } from "../components/Sidebar";
import { Topbar } from "../components/Topbar";
import { RoleManagementPanel } from "../components/RoleManagementPanel";

export function RoleManagementPage() {
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <Topbar title="Role Management" />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <RoleManagementPanel />
        </main>
      </div>
    </div>
  );
}
