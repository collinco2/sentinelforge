import React, { useState, useEffect } from "react";
import {
  Clock,
  AlertTriangle,
  Shield,
  Info,
  Globe,
  FileText,
  Link2,
  Mail,
  X,
  Loader2,
  AlertCircle,
  Hash,
  Edit3,
  Save,
  RotateCcw,
} from "lucide-react";
import { Dialog } from "./ui/dialog";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Slider } from "./ui/slider";
import { useToast } from "./ui/use-toast";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

// Alert interface matching the one from AlertTable
interface Alert {
  id: string | number;
  name: string;
  severity?: string;
  timestamp?: number;
  formatted_time?: string;
  threat_type?: string;
  confidence?: number;
  description?: string;
  source?: string;
  risk_score?: number; // 0-100 risk assessment
  overridden_risk_score?: number; // 0-100 analyst override
}

// IOC interface for associated IOCs
interface IOC {
  ioc_value: string;
  value: string;
  ioc_type: string;
  score: number;
  severity: string;
  inferred?: boolean;
}

interface AlertIocsResponse {
  alert_id: string;
  alert_name: string;
  timestamp: number;
  formatted_time: string;
  total_iocs: number;
  iocs: IOC[];
}

interface AlertDetailModalProps {
  alert: Alert | null;
  isOpen: boolean;
  onClose: () => void;
  onAlertUpdate?: () => void;
}

export function AlertDetailModal({
  alert,
  isOpen,
  onClose,
  onAlertUpdate,
}: AlertDetailModalProps) {
  const [relatedIocs, setRelatedIocs] = useState<IOC[]>([]);
  const [isLoadingIocs, setIsLoadingIocs] = useState(false);
  const [iocsError, setIocsError] = useState<string | null>(null);

  // Risk score override state
  const [isEditingRiskScore, setIsEditingRiskScore] = useState(false);
  const [newRiskScore, setNewRiskScore] = useState<number>(50);
  const [isUpdatingRiskScore, setIsUpdatingRiskScore] = useState(false);
  const { toast } = useToast();

  // Fetch associated IOCs when alert changes
  useEffect(() => {
    if (alert && isOpen) {
      fetchAlertIocs(String(alert.id));
    }
  }, [alert, isOpen]);

  // Initialize risk score when alert changes
  useEffect(() => {
    if (alert) {
      const effectiveScore =
        alert.overridden_risk_score ?? alert.risk_score ?? 50;
      setNewRiskScore(effectiveScore);
      setIsEditingRiskScore(false);
    }
  }, [alert]);

  const fetchAlertIocs = async (alertId: string) => {
    setIsLoadingIocs(true);
    setIocsError(null);
    try {
      const response = await fetch(`/api/alert/${alertId}/iocs`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data: AlertIocsResponse = await response.json();
      setRelatedIocs(data.iocs || []);
    } catch (error) {
      console.error("Error fetching related IOCs:", error);
      setIocsError(
        error instanceof Error ? error.message : "Failed to fetch IOCs",
      );
      setRelatedIocs([]);
    } finally {
      setIsLoadingIocs(false);
    }
  };

  const handleRiskScoreOverride = async () => {
    if (!alert) return;

    setIsUpdatingRiskScore(true);
    try {
      const response = await fetch(`/api/alert/${alert.id}/override`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ risk_score: newRiskScore }),
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: "Unknown error" }));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      await response.json(); // Response contains updated alert data

      toast({
        title: "Risk Score Updated",
        description: `Risk score overridden to ${newRiskScore}`,
        variant: "default",
      });

      setIsEditingRiskScore(false);

      // Update the alert in the parent component
      if (onAlertUpdate) {
        onAlertUpdate();
      }
    } catch (error) {
      console.error("Error updating risk score:", error);
      toast({
        title: "Error",
        description:
          error instanceof Error
            ? error.message
            : "Failed to update risk score",
        variant: "destructive",
      });
    } finally {
      setIsUpdatingRiskScore(false);
    }
  };

  const handleCancelEdit = () => {
    if (alert) {
      const effectiveScore =
        alert.overridden_risk_score ?? alert.risk_score ?? 50;
      setNewRiskScore(effectiveScore);
    }
    setIsEditingRiskScore(false);
  };

  const formatTimestamp = (timestamp: number | string) => {
    try {
      const date =
        typeof timestamp === "number"
          ? new Date(timestamp * 1000) // Convert Unix timestamp to milliseconds
          : new Date(timestamp);
      return date.toLocaleString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch (e) {
      return timestamp.toString();
    }
  };

  const getSeverityColor = (severity?: string) => {
    if (!severity) return "text-gray-400";
    switch (severity.toLowerCase()) {
      case "critical":
        return "text-red-500";
      case "high":
        return "text-orange-500";
      case "medium":
        return "text-yellow-500";
      case "low":
        return "text-blue-400";
      default:
        return "text-gray-400";
    }
  };

  const getSeverityBadgeColor = (severity?: string) => {
    if (!severity) return "bg-gray-500 hover:bg-gray-600";
    switch (severity.toLowerCase()) {
      case "critical":
        return "bg-red-500 hover:bg-red-600";
      case "high":
        return "bg-orange-500 hover:bg-orange-600";
      case "medium":
        return "bg-yellow-500 hover:bg-yellow-600";
      case "low":
        return "bg-blue-500 hover:bg-blue-600";
      default:
        return "bg-gray-500 hover:bg-gray-600";
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "bg-green-600";
    if (confidence >= 50) return "bg-yellow-500";
    return "bg-red-600";
  };

  const getIocTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "ip":
        return <Shield className="h-4 w-4 text-purple-400" />;
      case "domain":
        return <Globe className="h-4 w-4 text-green-400" />;
      case "file":
      case "hash":
        return <FileText className="h-4 w-4 text-blue-400" />;
      case "url":
        return <Link2 className="h-4 w-4 text-teal-400" />;
      case "email":
        return <Mail className="h-4 w-4 text-pink-400" />;
      default:
        return <Hash className="h-4 w-4 text-gray-400" />;
    }
  };

  const getIocTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "domain":
        return "bg-purple-500 hover:bg-purple-600";
      case "ip":
        return "bg-blue-500 hover:bg-blue-600";
      case "url":
        return "bg-green-500 hover:bg-green-600";
      case "hash":
      case "file":
        return "bg-orange-500 hover:bg-orange-600";
      case "email":
        return "bg-teal-500 hover:bg-teal-600";
      default:
        return "bg-gray-500 hover:bg-gray-600";
    }
  };

  const getRiskScoreBadge = (score: number, isOverridden: boolean = false) => {
    let badgeClass = "";

    if (score >= 80) {
      badgeClass = "bg-red-500 hover:bg-red-600";
    } else if (score >= 50) {
      badgeClass = "bg-orange-500 hover:bg-orange-600";
    } else {
      badgeClass = "bg-green-500 hover:bg-green-600";
    }

    return (
      <div
        className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-sm text-white ${badgeClass} ${isOverridden ? "font-bold" : "font-medium"}`}
      >
        {score > 90 && <span>🔥</span>}
        {score}
        {isOverridden && <span className="ml-1">✏️</span>}
      </div>
    );
  };

  if (!isOpen || !alert) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <div
        className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50"
        role="dialog"
        aria-modal="true"
        aria-labelledby="alert-detail-title"
      >
        <div className="bg-zinc-900 text-gray-100 rounded-xl shadow-xl p-6 w-[90vw] max-w-4xl relative max-h-[80vh] sm:max-h-[90vh] overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700">
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-100 bg-zinc-800 hover:bg-zinc-700 rounded-full p-1 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-600"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </button>

          {/* Header */}
          <div className="mb-6 pr-8">
            <div className="flex items-center mb-1">
              <span className={getSeverityColor(alert.severity)}>
                {alert.severity === "critical" || alert.severity === "high" ? (
                  <AlertTriangle className="h-5 w-5 inline mr-2" />
                ) : (
                  <Info className="h-5 w-5 inline mr-2" />
                )}
              </span>
              <h2
                id="alert-detail-title"
                className="text-xl font-semibold text-gray-100"
              >
                Alert Details - {alert.name}
              </h2>
            </div>
            <p className="text-sm text-gray-400">
              Detailed information about the security alert
            </p>
          </div>

          {/* Alert Metadata */}
          <div className="space-y-6 mb-8">
            {/* Alert ID */}
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-gray-200 tracking-tight">
                Alert ID
              </h3>
              <code className="font-mono bg-zinc-800 p-2 rounded-md text-white block">
                {alert.id}
              </code>
            </div>

            {/* Alert Name */}
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-gray-200 tracking-tight">
                Name
              </h3>
              <div className="bg-zinc-800 p-3 rounded-md text-gray-100">
                {alert.name}
              </div>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-gray-200 tracking-tight">
                Description
              </h3>
              <div className="bg-zinc-800 p-3 rounded-md text-gray-300">
                {alert.description || "No description available"}
              </div>
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Severity */}
              {alert.severity && (
                <div>
                  <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                    Severity
                  </h3>
                  <Badge
                    variant="outline"
                    className={`${getSeverityBadgeColor(alert.severity)} text-white capitalize`}
                  >
                    {alert.severity}
                  </Badge>
                </div>
              )}

              {/* Confidence */}
              {alert.confidence !== undefined && (
                <div>
                  <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                    Confidence Score
                  </h3>
                  <div className="flex items-center">
                    <div className="w-full bg-zinc-800 rounded-full h-2 mr-3">
                      <div
                        className={`h-full rounded-full ${getConfidenceColor(alert.confidence)}`}
                        style={{ width: `${alert.confidence}%` }}
                      />
                    </div>
                    <span className="text-sm text-white font-medium">
                      {alert.confidence}%
                    </span>
                  </div>
                </div>
              )}

              {/* Risk Score */}
              {(alert.risk_score !== undefined ||
                alert.overridden_risk_score !== undefined) && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-base font-semibold text-gray-200 tracking-tight">
                      Risk Score
                    </h3>
                    {!isEditingRiskScore && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsEditingRiskScore(true)}
                        className="h-6 w-6 p-0 text-gray-400 hover:text-gray-200"
                        title="Override risk score"
                        aria-label="Override risk score"
                      >
                        <Edit3 className="h-3 w-3" />
                      </Button>
                    )}
                  </div>

                  {isEditingRiskScore ? (
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">
                            Risk Score: {newRiskScore}
                          </span>
                          <span className="text-xs text-gray-400">0-100</span>
                        </div>
                        <Slider
                          value={[newRiskScore]}
                          onValueChange={(value) => setNewRiskScore(value[0])}
                          max={100}
                          min={0}
                          step={1}
                          className="w-full"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          value={newRiskScore}
                          onChange={(e) =>
                            setNewRiskScore(
                              Math.max(
                                0,
                                Math.min(100, parseInt(e.target.value) || 0),
                              ),
                            )
                          }
                          className="w-20 h-8 text-sm bg-zinc-800 border-zinc-700"
                        />
                        <Button
                          size="sm"
                          onClick={handleRiskScoreOverride}
                          disabled={isUpdatingRiskScore}
                          className="h-8 px-3 text-xs"
                        >
                          {isUpdatingRiskScore ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Save className="h-3 w-3" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleCancelEdit}
                          disabled={isUpdatingRiskScore}
                          className="h-8 px-3 text-xs bg-zinc-800 border-zinc-700"
                        >
                          <RotateCcw className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {getRiskScoreBadge(
                        alert.overridden_risk_score ?? alert.risk_score ?? 50,
                        alert.overridden_risk_score !== null &&
                          alert.overridden_risk_score !== undefined,
                      )}
                      {alert.overridden_risk_score !== null &&
                        alert.overridden_risk_score !== undefined && (
                          <div className="text-xs text-gray-400">
                            Overridden from {alert.risk_score}
                          </div>
                        )}
                    </div>
                  )}
                </div>
              )}

              {/* Threat Type */}
              {alert.threat_type && (
                <div>
                  <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                    Threat Type
                  </h3>
                  <div className="px-3 py-1.5 rounded-md bg-zinc-800 inline-block text-sm">
                    {alert.threat_type}
                  </div>
                </div>
              )}

              {/* Source */}
              {alert.source && (
                <div>
                  <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                    Source
                  </h3>
                  <div className="px-3 py-1.5 rounded-md bg-zinc-800 inline-block text-sm">
                    {alert.source}
                  </div>
                </div>
              )}

              {/* Timestamp */}
              {(alert.formatted_time || alert.timestamp) && (
                <div className="md:col-span-2">
                  <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                    Timestamp
                  </h3>
                  <div className="flex items-center text-gray-300">
                    <Clock className="h-4 w-4 mr-2 text-gray-400" />
                    {alert.formatted_time ||
                      (alert.timestamp
                        ? formatTimestamp(alert.timestamp)
                        : "Unknown")}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Associated IOCs Section */}
          <div className="space-y-4 border-t border-zinc-700 pt-6">
            <h3 className="text-lg font-semibold text-gray-200 tracking-tight">
              Associated IOCs
            </h3>

            {isLoadingIocs ? (
              <div className="flex flex-col items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                <p className="mt-2 text-sm text-gray-400">Loading IOCs...</p>
              </div>
            ) : iocsError ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <AlertCircle className="h-6 w-6 text-red-500 mb-2" />
                <p className="text-sm text-red-400">Error loading IOCs</p>
                <p className="text-xs text-gray-400">{iocsError}</p>
              </div>
            ) : relatedIocs.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <AlertCircle className="h-6 w-6 mx-auto mb-2" />
                <p>No IOCs found for this alert</p>
              </div>
            ) : (
              <div className="bg-zinc-800 rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="border-zinc-700">
                      <TableHead className="text-gray-300">Type</TableHead>
                      <TableHead className="text-gray-300">Value</TableHead>
                      <TableHead className="text-gray-300">Severity</TableHead>
                      <TableHead className="text-gray-300">Score</TableHead>
                      <TableHead className="text-gray-300">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {relatedIocs.map((ioc, index) => (
                      <TableRow
                        key={index}
                        className="border-zinc-700 hover:bg-zinc-700/50"
                      >
                        <TableCell>
                          <div className="flex items-center">
                            {getIocTypeIcon(ioc.ioc_type)}
                            <Badge
                              variant="outline"
                              className={`${getIocTypeColor(ioc.ioc_type)} text-white ml-2 capitalize`}
                            >
                              {ioc.ioc_type}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>
                          <code className="font-mono text-sm bg-zinc-700 px-2 py-1 rounded break-all">
                            {ioc.value || ioc.ioc_value}
                          </code>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`${getSeverityBadgeColor(ioc.severity)} text-white capitalize`}
                          >
                            {ioc.severity}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="font-semibold">
                            {ioc.score.toFixed(1)}
                          </span>
                        </TableCell>
                        <TableCell>
                          {ioc.inferred && (
                            <Badge
                              variant="outline"
                              className="bg-gray-500 text-white"
                            >
                              Inferred
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end border-t border-zinc-700 pt-4 mt-6">
            <Button
              variant="outline"
              className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700 focus:ring-2 focus:ring-blue-600 focus:outline-none"
              onClick={onClose}
            >
              Close
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
