import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageHeader, BREADCRUMB_CONFIGS } from "../components/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { UploadCloud, ArrowLeft, FileText, Database } from "lucide-react";
import { UploadFeedModal } from "../components/UploadFeedModal";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";
import { Alert, AlertDescription } from "../components/ui/alert";

export const FeedUploadPage: React.FC = () => {
  const { hasRole } = useAuth();
  const navigate = useNavigate();
  const [showUploadModal, setShowUploadModal] = useState(false);

  const canUpload = hasRole([UserRole.ANALYST, UserRole.ADMIN]);

  const handleUploadSuccess = () => {
    setShowUploadModal(false);
  };

  if (!canUpload) {
    return (
      <DashboardLayout title="Feed Upload">
        <div className="flex items-center justify-center min-h-[400px]">
          <Alert className="max-w-md">
            <UploadCloud className="h-4 w-4" />
            <AlertDescription>
              You don't have permission to upload feeds. Contact your
              administrator for access.
            </AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Feed Upload">
      <div className="space-y-6" data-testid="feed-upload-page">
        {/* Back Button */}
        <div className="flex items-center mb-4">
          <Button
            variant="ghost"
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>

        {/* Page Header with Breadcrumbs */}
        <PageHeader
          title="Feed Upload"
          description="Upload threat intelligence feeds from files or external sources"
          breadcrumbs={BREADCRUMB_CONFIGS.FEEDS_UPLOAD}
          icon={UploadCloud}
        />

        {/* Upload Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* File Upload */}
          <Card
            className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => setShowUploadModal(true)}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                File Upload
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Upload IOCs from CSV, JSON, or STIX files directly from your
                computer.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span>•</span>
                  <span>Supports CSV, JSON, STIX formats</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span>•</span>
                  <span>Automatic deduplication</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span>•</span>
                  <span>Validation and error reporting</span>
                </div>
              </div>
              <Button className="w-full mt-4" data-testid="file-upload-button">
                <UploadCloud className="h-4 w-4 mr-2" />
                Choose Files
              </Button>
            </CardContent>
          </Card>

          {/* Feed Management */}
          <Card
            className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate("/feed-management")}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-green-600" />
                Manage Feeds
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300 mb-4">
                Configure automated threat intelligence feeds from external
                sources.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span>•</span>
                  <span>Automated feed ingestion</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span>•</span>
                  <span>Schedule and monitor imports</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span>•</span>
                  <span>Feed health monitoring</span>
                </div>
              </div>
              <Button variant="outline" className="w-full mt-4">
                <Database className="h-4 w-4 mr-2" />
                Manage Feeds
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Recent Uploads */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Uploads</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500">
              <UploadCloud className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No recent uploads</p>
              <p className="text-sm">
                Upload your first file to see activity here
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Help Section */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Guidelines</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-2">Supported Formats</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>
                    • <strong>CSV:</strong> value,type,source,confidence
                  </li>
                  <li>
                    • <strong>JSON:</strong> Array of IOC objects
                  </li>
                  <li>
                    • <strong>STIX:</strong> STIX 2.0/2.1 bundles
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium mb-2">Best Practices</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Include source attribution</li>
                  <li>• Validate data before upload</li>
                  <li>• Use appropriate confidence scores</li>
                  <li>• Review import logs for errors</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Upload Modal */}
        <UploadFeedModal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          onSuccess={handleUploadSuccess}
        />
      </div>
    </DashboardLayout>
  );
};
