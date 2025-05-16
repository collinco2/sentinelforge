import React, { useEffect, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { IocDetailModal } from "../components/IocDetailModal";
import { IOCData } from "../components/IocTable";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useIocs } from "../hooks/useIocs";

export function IocDetailPage() {
  // Get the IOC ID from the URL
  const { iocId } = useParams<{ iocId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // From query params
  const sourceContext = searchParams.get("from") || "detail-page";
  const severityFilter = searchParams.get("severity");

  // State
  const [ioc, setIoc] = useState<IOCData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(true);

  // Get all IOCs to find the one we need
  const { iocs, isLoading } = useIocs({
    types: {
      domain: false,
      ip: false,
      file: false,
      url: false,
      email: false,
    },
    severities: {
      critical: false,
      high: false,
      medium: false,
      low: false,
    },
    confidenceRange: [0, 100],
  });

  // Find the IOC that matches the ID
  useEffect(() => {
    if (!isLoading && iocs.length > 0 && iocId) {
      const foundIoc = iocs.find((i) => i.id === iocId);
      if (foundIoc) {
        setIoc(foundIoc);
      }
    }
  }, [iocs, iocId, isLoading]);

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

  return (
    <DashboardLayout title="IOC Details">
      <div className="p-4 md:p-6">
        <Button variant="outline" className="mb-6" onClick={handleBackClick}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>

        <Card className="bg-card shadow-sm border-border">
          <CardContent className="p-6">
            <h1 className="text-2xl font-semibold mb-4">IOC Details</h1>
            {isLoading ? (
              <div className="h-24 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : ioc ? (
              <div>
                <p className="text-gray-400 mb-6">
                  Viewing detailed information for IOC:{" "}
                  <code className="bg-zinc-800 p-1 rounded">{ioc.value}</code>
                </p>

                {/* Modal rendered here to handle direct URL access */}
                <IocDetailModal
                  ioc={ioc}
                  isOpen={isModalOpen}
                  onOpenChange={handleModalClose}
                  sourceContext={sourceContext}
                />
              </div>
            ) : (
              <div className="text-red-400 p-4 bg-red-900/20 rounded-md">
                <p>IOC with ID {iocId} not found.</p>
                <p className="mt-2 text-sm text-gray-400">
                  The requested indicator of compromise might have been removed
                  or is not accessible.
                </p>
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
