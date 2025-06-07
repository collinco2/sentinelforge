import React, { useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { IocDetailModal } from "../components/IocDetailModal";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { ArrowLeft, AlertTriangle, Loader2 } from "lucide-react";
import { useIocDetail } from "../hooks/useIocDetail";

export function IocDetailPage() {
  // Get the IOC ID from the URL
  const { iocId } = useParams<{ iocId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // From query params
  const sourceContext = searchParams.get("from") || "detail-page";

  // State for modal
  const [isModalOpen, setIsModalOpen] = useState(true);

  // Get IOC details directly using our new hook
  const { iocDetail: ioc, isLoading, isError, error } = useIocDetail(iocId);

  // Handle modal close
  const handleModalClose = (open: boolean) => {
    setIsModalOpen(open);
    if (!open) {
      // Navigate back when modal is closed
      navigate("/");
    }
  };

  // Handle back button click
  const handleBackClick = () => {
    navigate("/");
  };

  // Custom navigation handler for the modal
  const handleNavigation = (url: string) => {
    navigate(url);
  };

  return (
    <DashboardLayout title="IOC Details">
      <div className="p-4 md:p-6">
        <Button variant="outline" className="mb-6" onClick={handleBackClick}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>

        <Card className="bg-card shadow-sm border-border">
          <CardContent className="p-6">
            <h1 className="text-2xl font-semibold mb-4">
              {ioc
                ? `IOC Details: ${ioc.value.substring(0, 30)}${ioc.value.length > 30 ? "..." : ""}`
                : "IOC Details"}
            </h1>

            {isLoading ? (
              <div className="h-24 flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                <span className="ml-3 text-gray-400">
                  Loading IOC details...
                </span>
              </div>
            ) : isError ? (
              <div className="text-red-400 p-4 bg-red-900/20 rounded-md">
                <div className="flex items-start">
                  <AlertTriangle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">Error Loading IOC Details</p>
                    <p className="mt-1 text-sm text-gray-400">
                      {error?.message ||
                        `IOC with ID ${iocId} could not be loaded.`}
                    </p>
                  </div>
                </div>
                <Button className="mt-4" onClick={handleBackClick}>
                  Return to Dashboard
                </Button>
              </div>
            ) : ioc ? (
              <div>
                <p className="text-gray-400 mb-6">
                  Viewing detailed information for IOC:{" "}
                  <code className="bg-zinc-800 p-1 rounded">{ioc.value}</code>
                </p>

                {/* Modal with iocId instead of pre-fetched object */}
                <IocDetailModal
                  iocId={iocId}
                  isOpen={isModalOpen}
                  onOpenChange={handleModalClose}
                  sourceContext={sourceContext}
                  onNavigate={handleNavigation}
                />
              </div>
            ) : (
              <div className="text-red-400 p-4 bg-red-900/20 rounded-md">
                <div className="flex items-start">
                  <AlertTriangle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">IOC Not Found</p>
                    <p className="mt-1 text-sm text-gray-400">
                      The requested indicator of compromise might have been
                      removed or is not accessible.
                    </p>
                  </div>
                </div>
                <Button className="mt-4" onClick={handleBackClick}>
                  Return to Dashboard
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
