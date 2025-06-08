import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { Upload, Database, Activity, Info } from "lucide-react";
import { FeedManager } from "../components/FeedManager";
import { UploadFeedModal } from "../components/UploadFeedModal";
import { useAuth } from "../hooks/useAuth";
import { UserRole } from "../services/auth";

export const FeedManagementPage: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const canModify = hasRole([UserRole.ANALYST, UserRole.ADMIN]);

  const handleUploadSuccess = () => {
    // Refresh the feed manager
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Feed Management</h1>
          <p className="text-gray-600 mt-2">
            Manage threat intelligence feeds and import IOCs from external
            sources
          </p>
        </div>

        {canModify && (
          <Button onClick={() => setShowUploadModal(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload Feed
          </Button>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">
                  Active Feeds
                </p>
                <p className="text-2xl font-bold text-gray-900">3</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">
                  Recent Imports
                </p>
                <p className="text-2xl font-bold text-gray-900">12</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Upload className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">
                  IOCs Imported
                </p>
                <p className="text-2xl font-bold text-gray-900">1,247</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="feeds" className="space-y-6">
        <TabsList>
          <TabsTrigger value="feeds">Feed Configuration</TabsTrigger>
          <TabsTrigger value="guide">Import Guide</TabsTrigger>
        </TabsList>

        <TabsContent value="feeds" className="space-y-6">
          <FeedManager key={refreshKey} />
        </TabsContent>

        <TabsContent value="guide" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Info className="h-5 w-5 mr-2" />
                Feed Import Guide
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Supported Formats */}
              <div>
                <h3 className="text-lg font-semibold mb-3">
                  Supported Formats
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      CSV Format
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      Comma-separated values with headers. Supports field
                      mapping.
                    </p>
                    <div className="bg-gray-50 p-3 rounded text-sm font-mono">
                      ioc_type,ioc_value,source_feed,severity
                      <br />
                      domain,malicious.com,Feed Name,high
                      <br />
                      ip,192.168.1.1,Feed Name,medium
                    </div>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      JSON Format
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      Structured JSON with IOC objects. Flexible field mapping.
                    </p>
                    <div className="bg-gray-50 p-3 rounded text-sm font-mono">
                      {`{
  "iocs": [
    {
      "type": "domain",
      "value": "malicious.com",
      "confidence": 85
    }
  ]
}`}
                    </div>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      Text Format
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      One IOC per line. Type auto-detected from pattern.
                    </p>
                    <div className="bg-gray-50 p-3 rounded text-sm font-mono">
                      malicious.com
                      <br />
                      192.168.1.1
                      <br />
                      https://evil.com/payload
                      <br /># Comments are ignored
                    </div>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      STIX Format
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      Basic STIX 2.0 indicator objects. Limited support.
                    </p>
                    <div className="bg-gray-50 p-3 rounded text-sm font-mono">
                      {`{
  "objects": [
    {
      "type": "indicator",
      "pattern": "[domain-name:value = 'evil.com']"
    }
  ]
}`}
                    </div>
                  </div>
                </div>
              </div>

              {/* Field Mapping */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Field Mapping</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">
                          Standard Field
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">
                          Alternative Names
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      <tr>
                        <td className="px-4 py-2 text-sm font-mono">
                          ioc_value
                        </td>
                        <td className="px-4 py-2 text-sm">
                          value, indicator, ioc
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          The IOC value (required)
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 text-sm font-mono">
                          ioc_type
                        </td>
                        <td className="px-4 py-2 text-sm">
                          type, indicator_type
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          IOC type (auto-detected if missing)
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 text-sm font-mono">
                          source_feed
                        </td>
                        <td className="px-4 py-2 text-sm">source, feed</td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          Source of the IOC
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 text-sm font-mono">
                          severity
                        </td>
                        <td className="px-4 py-2 text-sm">priority, level</td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          Severity level (low, medium, high, critical)
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 text-sm font-mono">
                          confidence
                        </td>
                        <td className="px-4 py-2 text-sm">
                          score, reliability
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          Confidence score (0-100)
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 text-sm font-mono">tags</td>
                        <td className="px-4 py-2 text-sm">
                          labels, categories
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          Comma-separated tags
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Best Practices */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Best Practices</h3>
                <div className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <p className="text-sm text-gray-700">
                      <strong>File Size:</strong> Keep files under 10MB for
                      optimal performance. Large feeds should be split into
                      smaller chunks.
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <p className="text-sm text-gray-700">
                      <strong>Encoding:</strong> Ensure files are UTF-8 encoded
                      to avoid character issues.
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <p className="text-sm text-gray-700">
                      <strong>Duplicates:</strong> The system automatically
                      detects and skips duplicate IOCs based on type and value
                      combination.
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <p className="text-sm text-gray-700">
                      <strong>Validation:</strong> Invalid IOCs are logged but
                      don't stop the import process. Check import logs for
                      details.
                    </p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <p className="text-sm text-gray-700">
                      <strong>Justification:</strong> Always provide a
                      justification for imports to maintain audit compliance.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Upload Modal */}
      <UploadFeedModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onSuccess={handleUploadSuccess}
      />
    </div>
  );
};
