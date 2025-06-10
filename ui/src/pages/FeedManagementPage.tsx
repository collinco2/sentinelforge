import React, { useState } from "react";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageTransition } from "../components/PageTransition";
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
  const { hasRole } = useAuth();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const canModify = hasRole([UserRole.ANALYST, UserRole.ADMIN]);

  const handleUploadSuccess = () => {
    // Refresh the feed manager
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <DashboardLayout title="Feed Management">
      <PageTransition>
        <div className="space-y-6">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-white">
                Feed Management
              </h1>
              <p className="text-lg text-slate-300">
                Manage threat intelligence feeds and import IOCs from external
                sources
              </p>
            </div>

            {canModify && (
              <Button
                onClick={() => setShowUploadModal(true)}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Feed
              </Button>
            )}
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-card dark:bg-card border-border dark:border-border">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Database className="h-8 w-8 text-blue-500 dark:text-blue-400" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground dark:text-muted-foreground">
                      Active Feeds
                    </p>
                    <p className="text-2xl font-bold text-foreground dark:text-foreground">
                      3
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card dark:bg-card border-border dark:border-border">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Activity className="h-8 w-8 text-green-500 dark:text-green-400" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground dark:text-muted-foreground">
                      Recent Imports
                    </p>
                    <p className="text-2xl font-bold text-foreground dark:text-foreground">
                      12
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card dark:bg-card border-border dark:border-border">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Upload className="h-8 w-8 text-purple-500 dark:text-purple-400" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground dark:text-muted-foreground">
                      IOCs Imported
                    </p>
                    <p className="text-2xl font-bold text-foreground dark:text-foreground">
                      1,247
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <Tabs defaultValue="feeds" className="space-y-6">
            <TabsList className="bg-slate-700/50 border-slate-600">
              <TabsTrigger
                value="feeds"
                className="data-[state=active]:bg-slate-800/50 data-[state=active]:text-white text-slate-300"
              >
                Feed Configuration
              </TabsTrigger>
              <TabsTrigger
                value="guide"
                className="data-[state=active]:bg-slate-800/50 data-[state=active]:text-white text-slate-300"
              >
                Import Guide
              </TabsTrigger>
            </TabsList>

            <TabsContent value="feeds" className="space-y-6">
              <FeedManager key={refreshKey} />
            </TabsContent>

            <TabsContent value="guide" className="space-y-6">
              <Card className="bg-card dark:bg-card border-border dark:border-border">
                <CardHeader>
                  <CardTitle className="flex items-center text-foreground dark:text-foreground">
                    <Info className="h-5 w-5 mr-2 text-blue-500 dark:text-blue-400" />
                    Feed Import Guide
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Supported Formats */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3 text-foreground dark:text-foreground">
                      Supported Formats
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="border border-border dark:border-border rounded-lg p-4 bg-card dark:bg-card">
                        <h4 className="font-medium text-foreground dark:text-foreground mb-2">
                          CSV Format
                        </h4>
                        <p className="text-sm text-muted-foreground dark:text-muted-foreground mb-3">
                          Comma-separated values with headers. Supports field
                          mapping.
                        </p>
                        <div className="bg-muted dark:bg-muted p-3 rounded text-sm font-mono text-foreground dark:text-foreground">
                          ioc_type,ioc_value,source_feed,severity
                          <br />
                          domain,malicious.com,Feed Name,high
                          <br />
                          ip,192.168.1.1,Feed Name,medium
                        </div>
                      </div>

                      <div className="border border-border dark:border-border rounded-lg p-4 bg-card dark:bg-card">
                        <h4 className="font-medium text-foreground dark:text-foreground mb-2">
                          JSON Format
                        </h4>
                        <p className="text-sm text-muted-foreground dark:text-muted-foreground mb-3">
                          Structured JSON with IOC objects. Flexible field
                          mapping.
                        </p>
                        <div className="bg-muted dark:bg-muted p-3 rounded text-sm font-mono text-foreground dark:text-foreground">
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

                      <div className="border border-border dark:border-border rounded-lg p-4 bg-card dark:bg-card">
                        <h4 className="font-medium text-foreground dark:text-foreground mb-2">
                          Text Format
                        </h4>
                        <p className="text-sm text-muted-foreground dark:text-muted-foreground mb-3">
                          One IOC per line. Type auto-detected from pattern.
                        </p>
                        <div className="bg-muted dark:bg-muted p-3 rounded text-sm font-mono text-foreground dark:text-foreground">
                          malicious.com
                          <br />
                          192.168.1.1
                          <br />
                          https://evil.com/payload
                          <br /># Comments are ignored
                        </div>
                      </div>

                      <div className="border border-slate-600 rounded-lg p-4 bg-slate-800/50">
                        <h4 className="font-medium text-white mb-2">
                          STIX Format
                        </h4>
                        <p className="text-sm text-slate-300 mb-3">
                          Basic STIX 2.0 indicator objects. Limited support.
                        </p>
                        <div className="bg-slate-700/50 p-3 rounded text-sm font-mono text-white">
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
                    <h3 className="text-lg font-semibold mb-3 text-foreground dark:text-foreground">
                      Field Mapping
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full border border-border dark:border-border rounded-lg bg-card dark:bg-card">
                        <thead className="bg-muted dark:bg-muted">
                          <tr>
                            <th className="px-4 py-2 text-left text-sm font-medium text-foreground dark:text-foreground">
                              Standard Field
                            </th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-foreground dark:text-foreground">
                              Alternative Names
                            </th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-foreground dark:text-foreground">
                              Description
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border dark:divide-border">
                          <tr>
                            <td className="px-4 py-2 text-sm font-mono text-foreground dark:text-foreground">
                              ioc_value
                            </td>
                            <td className="px-4 py-2 text-sm text-foreground dark:text-foreground">
                              value, indicator, ioc
                            </td>
                            <td className="px-4 py-2 text-sm text-muted-foreground dark:text-muted-foreground">
                              The IOC value (required)
                            </td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm font-mono text-foreground dark:text-foreground">
                              ioc_type
                            </td>
                            <td className="px-4 py-2 text-sm text-foreground dark:text-foreground">
                              type, indicator_type
                            </td>
                            <td className="px-4 py-2 text-sm text-muted-foreground dark:text-muted-foreground">
                              IOC type (auto-detected if missing)
                            </td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm font-mono text-foreground dark:text-foreground">
                              source_feed
                            </td>
                            <td className="px-4 py-2 text-sm text-foreground dark:text-foreground">
                              source, feed
                            </td>
                            <td className="px-4 py-2 text-sm text-muted-foreground dark:text-muted-foreground">
                              Source of the IOC
                            </td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm font-mono text-foreground dark:text-foreground">
                              severity
                            </td>
                            <td className="px-4 py-2 text-sm text-foreground dark:text-foreground">
                              priority, level
                            </td>
                            <td className="px-4 py-2 text-sm text-muted-foreground dark:text-muted-foreground">
                              Severity level (low, medium, high, critical)
                            </td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm font-mono text-foreground dark:text-foreground">
                              confidence
                            </td>
                            <td className="px-4 py-2 text-sm text-foreground dark:text-foreground">
                              score, reliability
                            </td>
                            <td className="px-4 py-2 text-sm text-muted-foreground dark:text-muted-foreground">
                              Confidence score (0-100)
                            </td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm font-mono text-foreground dark:text-foreground">
                              tags
                            </td>
                            <td className="px-4 py-2 text-sm text-foreground dark:text-foreground">
                              labels, categories
                            </td>
                            <td className="px-4 py-2 text-sm text-muted-foreground dark:text-muted-foreground">
                              Comma-separated tags
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Best Practices */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3 text-foreground dark:text-foreground">
                      Best Practices
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full mt-2"></div>
                        <p className="text-sm text-foreground dark:text-foreground">
                          <strong>File Size:</strong> Keep files under 10MB for
                          optimal performance. Large feeds should be split into
                          smaller chunks.
                        </p>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full mt-2"></div>
                        <p className="text-sm text-foreground dark:text-foreground">
                          <strong>Encoding:</strong> Ensure files are UTF-8
                          encoded to avoid character issues.
                        </p>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full mt-2"></div>
                        <p className="text-sm text-foreground dark:text-foreground">
                          <strong>Duplicates:</strong> The system automatically
                          detects and skips duplicate IOCs based on type and
                          value combination.
                        </p>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full mt-2"></div>
                        <p className="text-sm text-foreground dark:text-foreground">
                          <strong>Validation:</strong> Invalid IOCs are logged
                          but don't stop the import process. Check import logs
                          for details.
                        </p>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full mt-2"></div>
                        <p className="text-sm text-foreground dark:text-foreground">
                          <strong>Justification:</strong> Always provide a
                          justification for imports to maintain audit
                          compliance.
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
      </PageTransition>
    </DashboardLayout>
  );
};
