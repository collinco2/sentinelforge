import React from "react";
import { useNavigate } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { AlertTable } from "../components/AlertTable";
import { Button } from "../components/ui/button";

export function AlertsPage() {
  const navigate = useNavigate();

  return (
    <DashboardLayout title="Alert Management">
      <div className="p-6">
        <div className="flex flex-col space-y-4 md:space-y-0 md:flex-row md:justify-between md:items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-200 mb-2">
              Alert Management
            </h1>
            <p className="text-gray-400">
              Monitor and manage security alerts from various sources
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => navigate("/alerts/timeline")}
              className="flex items-center gap-1"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="mr-1"
              >
                <path d="M3 3v18h18" />
                <path d="m19 9-5 5-4-4-3 3" />
              </svg>
              Timeline View
            </Button>
          </div>
        </div>

        <div className="bg-card shadow-sm border-border rounded-lg">
          <div className="p-6">
            <AlertTable />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
