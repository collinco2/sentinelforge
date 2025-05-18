import React, { useState, useEffect } from "react";
import {
  Clock,
  AlertTriangle,
  Shield,
  Info,
  ExternalLink,
  Globe,
  FileText,
  Link2,
  Mail,
  X,
  Target,
  Braces,
  Copy,
  Check,
  Download,
  FileText as FileIcon,
  Table,
  ChevronDown,
  Loader2,
  ClipboardCopy,
  CheckCircle,
} from "lucide-react";
import { IOCData } from "./IocTable";
import { Dialog } from "./ui/dialog";
import { Button } from "./ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./ui/tabs";
import {
  useIocDetail,
  useIocExplanation,
  IocDetailData,
} from "../hooks/useIocDetail";
import ExportReportButton from "./ExportReportButton";

interface IocDetailModalProps {
  ioc?: IOCData | null; // Optional now - can use either this or iocId
  iocId?: string | null; // New prop to fetch by ID
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  sourceContext?: string; // Optional param to track where modal was opened from
  onNavigate?: (url: string) => void; // Optional navigation handler
}

// Utility function to export IOC to CSV
const exportIocToCsv = (ioc: IOCData | IocDetailData) => {
  // Define alerts (use from IocDetailData if available)
  const detailIoc = ioc as IocDetailData;
  const alerts = detailIoc.alerts || [
    { id: "1", name: "Network scan detected", timestamp: "2 hours ago" },
    {
      id: "2",
      name: "Suspicious outbound connection",
      timestamp: "4 hours ago",
    },
  ];

  // Create CSV header and row
  const headers = [
    "Value",
    "Type",
    "Severity",
    "Confidence",
    "First Seen",
    "Alerts",
  ];
  const alertsStr = alerts.map((a) => `${a.name} (${a.timestamp})`).join("; ");

  const row = [
    ioc.value,
    ioc.type,
    ioc.severity,
    `${ioc.confidence}%`,
    new Date(ioc.timestamp).toLocaleString(),
    alertsStr,
  ];

  // Convert to CSV format
  const csvContent = [
    headers.join(","),
    row.map((field) => `"${field.replace(/"/g, '""')}"`).join(","), // Escape quotes
  ].join("\n");

  // Create a Blob with the CSV content
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  // Create a temporary link element and trigger the download
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `ioc-${ioc.id}-details.csv`);
  document.body.appendChild(link);
  link.click();

  // Clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export function IocDetailModal({
  ioc: propIoc,
  iocId,
  isOpen,
  onOpenChange,
  sourceContext = "dashboard",
  onNavigate,
}: IocDetailModalProps) {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [isCopied, setIsCopied] = useState(false);
  const [copiedText, setCopiedText] = useState<string>("");

  // If an ID is provided, fetch the details
  const effectiveIocId = iocId || (propIoc ? propIoc.id : null);

  // Use our new hook to fetch IOC details
  const {
    iocDetail,
    isLoading: isLoadingIoc,
    isError: isIocError,
    error: iocError,
  } = useIocDetail(effectiveIocId);

  // Use the new ML explanation hook
  const {
    explanation,
    isLoading: isLoadingExplanation,
    isError: isExplanationError,
  } = useIocExplanation(effectiveIocId);

  // Use the prop IOC as fallback if no detail data yet
  const ioc = iocDetail || propIoc;

  // If neither prop IOC nor fetched data is available, show nothing
  if (!isOpen) return null;

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch (e) {
      return timestamp;
    }
  };

  const getSeverityColor = (severity: IOCData["severity"]) => {
    switch (severity) {
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

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 90) return "bg-red-600";
    if (confidence >= 70) return "bg-yellow-500";
    return "bg-green-500";
  };

  const getTypeIcon = (type: IOCData["type"]) => {
    switch (type) {
      case "ip":
        return <Shield className="h-4 w-4 text-purple-400" />;
      case "domain":
        return <Globe className="h-4 w-4 text-green-400" />;
      case "file":
        return <FileText className="h-4 w-4 text-blue-400" />;
      case "url":
        return <Link2 className="h-4 w-4 text-teal-400" />;
      case "email":
        return <Mail className="h-4 w-4 text-pink-400" />;
      default:
        return <Info className="h-4 w-4 text-gray-400" />;
    }
  };

  const handleCopyToClipboard = () => {
    if (!ioc) return;
    navigator.clipboard.writeText(ioc.value).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000); // Reset after 2 seconds
    });
  };

  const navigateToIocDetail = () => {
    if (!ioc) return;

    // Build deep link URL with ID and context parameters
    const iocDetailUrl = `/threat-intel/${ioc.id}?from=${sourceContext}&severity=${ioc.severity}`;

    if (onNavigate) {
      // Use the custom navigation handler if provided
      onNavigate(iocDetailUrl);
    } else {
      // Default behavior: copy URL to clipboard
      navigator.clipboard
        .writeText(`${window.location.origin}${iocDetailUrl}`)
        .then(() => {
          // Show a temporary message that URL was copied
          setIsCopied(true);
          setTimeout(() => setIsCopied(false), 2000);
        })
        .catch((err) => {
          console.error("Failed to copy URL: ", err);
        });
    }
  };

  // Add openInNewTab function
  const openInNewTab = () => {
    if (!ioc) return;

    const iocDetailUrl = `/threat-intel/${ioc.id}?from=${sourceContext}&severity=${ioc.severity}`;
    window.open(iocDetailUrl, "_blank");
  };

  // Render loading state
  const renderLoading = () => (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="h-8 w-8 text-blue-500 animate-spin mb-4" />
      <p className="text-gray-400">Loading IOC details...</p>
    </div>
  );

  // Render error state
  const renderError = () => (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertTriangle className="h-8 w-8 text-red-500 mb-4" />
      <h3 className="text-lg font-medium text-red-400 mb-2">
        Error Loading IOC Details
      </h3>
      <p className="text-gray-400 max-w-md mx-auto">
        {iocError?.message ||
          "An error occurred while loading the IOC details. Please try again."}
      </p>
      <Button
        className="mt-4 bg-zinc-800 hover:bg-zinc-700 text-gray-300"
        onClick={() => window.location.reload()}
      >
        Reload Page
      </Button>
    </div>
  );

  // Handler for the "View in Threat Intelligence" button
  const viewInThreatIntelligence = () => {
    if (!ioc) return;

    const url = `/ioc/${ioc.id}`;
    if (onNavigate) {
      onNavigate(url);
    } else {
      window.location.href = url;
    }
  };

  // Function to copy shareable link
  const handleCopyShareLink = () => {
    if (!ioc) return;

    const shareUrl = `${window.location.origin}/share/ioc/${encodeURIComponent(
      ioc.value,
    )}`;

    navigator.clipboard.writeText(shareUrl).then(
      () => {
        setCopiedText("share-link");
        setTimeout(() => setCopiedText(""), 2000);
      },
      (err) => {
        console.error("Could not copy text: ", err);
      },
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <div
        className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ioc-detail-title"
      >
        <div className="bg-zinc-900 text-gray-100 rounded-xl shadow-xl p-6 w-[90vw] max-w-3xl relative max-h-[80vh] sm:max-h-[90vh] overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700">
          {/* Close Button */}
          <button
            onClick={() => onOpenChange(false)}
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-100 bg-zinc-800 hover:bg-zinc-700 rounded-full p-1 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-600"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </button>

          {/* Header */}
          <div className="mb-6 pr-8">
            <div className="flex items-center mb-1">
              <span
                className={
                  ioc ? getSeverityColor(ioc.severity) : "text-gray-400"
                }
              >
                {ioc &&
                (ioc.severity === "critical" || ioc.severity === "high") ? (
                  <AlertTriangle className="h-5 w-5 inline mr-2" />
                ) : (
                  <Info className="h-5 w-5 inline mr-2" />
                )}
              </span>
              <h2
                id="ioc-detail-title"
                className="text-xl font-semibold text-gray-100"
              >
                IOC Details{" "}
                {ioc
                  ? `- ${ioc.value.substring(0, 30)}${ioc.value.length > 30 ? "..." : ""}`
                  : ""}
              </h2>
            </div>
            <p className="text-sm text-gray-400">
              Detailed information about the indicator of compromise
            </p>
          </div>

          {/* Content - Conditionally render based on loading/error state */}
          {isLoadingIoc ? (
            renderLoading()
          ) : isIocError ? (
            renderError()
          ) : !ioc ? (
            <div className="text-center py-8 text-gray-400">
              No IOC details available
            </div>
          ) : (
            <>
              {/* Tabs */}
              <Tabs
                defaultValue="overview"
                value={activeTab}
                onValueChange={setActiveTab}
              >
                <TabsList className="w-full mb-6">
                  <TabsTrigger
                    value="overview"
                    className="flex-1 transition-all duration-200 data-[state=active]:bg-zinc-700 data-[state=active]:text-white focus:ring-2 focus:ring-blue-600 focus:outline-none"
                  >
                    Overview
                  </TabsTrigger>
                  <TabsTrigger
                    value="scoring"
                    className="flex-1 transition-all duration-200 data-[state=active]:bg-zinc-700 data-[state=active]:text-white focus:ring-2 focus:ring-blue-600 focus:outline-none"
                  >
                    Scoring Rationale
                  </TabsTrigger>
                  <TabsTrigger
                    value="mitre"
                    className="flex-1 transition-all duration-200 data-[state=active]:bg-zinc-700 data-[state=active]:text-white focus:ring-2 focus:ring-blue-600 focus:outline-none"
                  >
                    MITRE ATT&CK
                  </TabsTrigger>
                </TabsList>

                {/* Overview Tab Content */}
                <TabsContent
                  value="overview"
                  className="space-y-6 sm:space-y-8"
                  role="tabpanel"
                  aria-labelledby="overview-tab"
                >
                  {/* IOC Value */}
                  <div className="space-y-2">
                    <h3 className="text-base font-semibold text-gray-200 tracking-tight">
                      Value
                    </h3>
                    <div className="flex items-center group relative">
                      <div className="mr-2">{getTypeIcon(ioc.type)}</div>
                      <code className="font-mono bg-zinc-800 p-2 rounded-md text-white w-full overflow-x-auto">
                        {ioc.value}
                      </code>
                      <button
                        onClick={handleCopyToClipboard}
                        className="absolute right-2 p-1.5 bg-zinc-700 hover:bg-zinc-600 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-600"
                        aria-label="Copy IOC value to clipboard"
                      >
                        {isCopied ? (
                          <Check className="h-4 w-4 text-green-400" />
                        ) : (
                          <Copy className="h-4 w-4 text-gray-300" />
                        )}
                        <span className="sr-only">
                          {isCopied ? "Copied" : "Copy to clipboard"}
                        </span>
                      </button>
                      {/* Tooltip */}
                      <div
                        className={`absolute -top-9 right-0 px-2 py-1 bg-zinc-800 text-xs text-gray-200 rounded shadow transition-opacity duration-300 ${
                          isCopied ? "opacity-100" : "opacity-0"
                        }`}
                        aria-live="polite"
                      >
                        Copied to clipboard!
                      </div>
                    </div>
                  </div>

                  {/* Type & Severity */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                        Type
                      </h3>
                      <div className="px-3 py-1.5 rounded-md bg-zinc-800 inline-block text-sm capitalize">
                        {ioc.type}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                        Severity
                      </h3>
                      <div
                        className={`px-3 py-1.5 rounded-md inline-block text-sm capitalize ${getSeverityColor(
                          ioc.severity,
                        )} bg-zinc-800`}
                      >
                        {ioc.severity}
                      </div>
                    </div>
                  </div>

                  {/* Confidence */}
                  <div>
                    <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                      Confidence Score
                    </h3>
                    <div className="flex items-center">
                      <div className="w-full bg-zinc-800 rounded-full h-2 mr-3">
                        <div
                          className={`h-full rounded-full ${getConfidenceColor(ioc.confidence)}`}
                          style={{ width: `${ioc.confidence}%` }}
                        />
                      </div>
                      <span className="text-sm text-white font-medium">
                        {ioc.confidence}%
                      </span>
                    </div>
                  </div>

                  {/* First Observed */}
                  <div>
                    <h3 className="text-base font-semibold text-gray-200 tracking-tight mb-1">
                      First Observed
                    </h3>
                    <div className="flex items-center text-gray-300">
                      <Clock className="h-4 w-4 mr-2 text-gray-400" />
                      {formatTimestamp(ioc.first_observed || ioc.timestamp)}
                    </div>
                  </div>

                  {/* Associated Alerts */}
                  <div className="space-y-2 border-t border-zinc-700 pt-4 mt-4">
                    <h3 className="text-base font-semibold text-gray-200 tracking-tight">
                      Associated Alerts
                    </h3>
                    {iocDetail?.alerts && iocDetail.alerts.length > 0 ? (
                      <ul className="space-y-2 text-sm text-gray-300">
                        {iocDetail.alerts.map((alert) => (
                          <li
                            key={alert.id}
                            className="bg-zinc-800 p-2 rounded flex justify-between"
                          >
                            <span>{alert.name}</span>
                            <span className="text-gray-400 text-xs">
                              {alert.timestamp}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <ul className="space-y-2 text-sm text-gray-300">
                        <li className="bg-zinc-800 p-2 rounded flex justify-between">
                          <span>Network scan detected</span>
                          <span className="text-gray-400 text-xs">
                            2 hours ago
                          </span>
                        </li>
                        <li className="bg-zinc-800 p-2 rounded flex justify-between">
                          <span>Suspicious outbound connection</span>
                          <span className="text-gray-400 text-xs">
                            4 hours ago
                          </span>
                        </li>
                      </ul>
                    )}
                  </div>
                </TabsContent>

                {/* Scoring Rationale Tab Content */}
                <TabsContent
                  value="scoring"
                  className="space-y-6 sm:space-y-8"
                  role="tabpanel"
                  aria-labelledby="scoring-tab"
                >
                  <div className="flex items-center mb-4">
                    <Braces className="h-5 w-5 mr-2 text-purple-400" />
                    <h3 className="text-md font-medium text-gray-100">
                      Scoring Rationale
                    </h3>
                  </div>

                  <div className="space-y-4 sm:space-y-6">
                    {isLoadingExplanation ? (
                      <div className="bg-zinc-800 p-4 sm:p-5 rounded-md flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 text-blue-400 animate-spin mr-2" />
                        <span className="text-gray-300">
                          Analyzing with ML model...
                        </span>
                      </div>
                    ) : isExplanationError ? (
                      <div className="bg-zinc-800 p-4 sm:p-5 rounded-md">
                        <div className="flex items-center text-red-400 mb-2">
                          <AlertTriangle className="h-5 w-5 mr-2" />
                          <h4 className="text-sm font-medium">
                            Error Loading ML Explanation
                          </h4>
                        </div>
                        <p className="text-sm text-gray-400">
                          The ML model was unable to provide an explanation.
                          Using baseline scoring instead.
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="bg-zinc-800 p-4 sm:p-5 rounded-md">
                          <h4 className="text-sm font-medium text-gray-300 mb-2">
                            ML Threat Score:{" "}
                            {explanation?.score
                              ? Math.round(explanation.score * 100)
                              : ioc.confidence}
                            /100
                          </h4>
                          <div className="flex items-center mb-4">
                            <div className="w-full bg-zinc-700/50 rounded-full h-2 mr-3 overflow-hidden border border-zinc-600">
                              <div
                                className={`h-full rounded-full ${getConfidenceColor(explanation?.score ? Math.round(explanation.score * 100) : ioc.confidence)}`}
                                style={{
                                  width: `${explanation?.score ? Math.round(explanation.score * 100) : ioc.confidence}%`,
                                }}
                              />
                            </div>
                            <span className="text-sm text-white font-medium">
                              {explanation?.score
                                ? Math.round(explanation.score * 100)
                                : ioc.confidence}
                              %
                            </span>
                          </div>
                          <p className="text-sm text-gray-400">
                            {explanation?.explanation?.summary ||
                              "This IOC was analyzed using our ML model based on its features and observed behavior."}
                          </p>
                        </div>

                        <div className="bg-zinc-800 p-4 sm:p-5 rounded-md">
                          <h4 className="text-sm font-medium text-gray-300 mb-2">
                            Key Factors
                          </h4>
                          <ul className="space-y-2 text-sm">
                            {explanation?.explanation?.feature_breakdown &&
                            explanation.explanation.feature_breakdown.length >
                              0 ? (
                              explanation.explanation.feature_breakdown.map(
                                (factor, index) => (
                                  <li key={index} className="flex items-start">
                                    <span className="text-red-600 mr-2">•</span>
                                    <div className="w-full">
                                      <span className="text-gray-300">
                                        {factor.feature}{" "}
                                        {factor.value
                                          ? `(${factor.value})`
                                          : ""}
                                      </span>
                                      <div className="w-full bg-zinc-700/50 rounded h-2 mt-1 overflow-hidden border border-zinc-600">
                                        <div
                                          className={`h-2 rounded ${
                                            factor.weight > 0.5
                                              ? "bg-red-500"
                                              : factor.weight > 0.2
                                                ? "bg-yellow-500"
                                                : factor.weight > 0
                                                  ? "bg-blue-500"
                                                  : "bg-gray-500"
                                          }`}
                                          style={{
                                            width: `${Math.abs(factor.weight) * 100}%`,
                                          }}
                                        />
                                      </div>
                                    </div>
                                  </li>
                                ),
                              )
                            ) : iocDetail?.scoring_rationale?.factors &&
                              iocDetail.scoring_rationale.factors.length > 0 ? (
                              iocDetail.scoring_rationale.factors.map(
                                (factor, index) => (
                                  <li key={index} className="flex items-start">
                                    <span className="text-red-600 mr-2">•</span>
                                    <div className="w-full">
                                      <span className="text-gray-300">
                                        {factor.name} (
                                        {(factor.weight * 100).toFixed(0)}%)
                                        {factor.description &&
                                          `: ${factor.description}`}
                                      </span>
                                      <div className="w-full bg-zinc-700/50 rounded h-2 mt-1 overflow-hidden border border-zinc-600">
                                        <div
                                          className={`h-2 rounded ${
                                            factor.weight > 0.7
                                              ? "bg-red-500"
                                              : factor.weight > 0.4
                                                ? "bg-yellow-500"
                                                : "bg-blue-500"
                                          }`}
                                          style={{
                                            width: `${factor.weight * 100}%`,
                                          }}
                                        />
                                      </div>
                                    </div>
                                  </li>
                                ),
                              )
                            ) : (
                              <>
                                <li className="flex items-start">
                                  <span className="text-red-600 mr-2">•</span>
                                  <div className="w-full">
                                    <span className="text-gray-300">
                                      Pattern matches known malicious {ioc.type}{" "}
                                      signatures (83% similarity)
                                    </span>
                                    <div className="w-full bg-zinc-700/50 rounded h-2 mt-1 overflow-hidden border border-zinc-600">
                                      <div
                                        className="bg-red-500 h-2 rounded"
                                        style={{ width: "83%" }}
                                      />
                                    </div>
                                  </div>
                                </li>
                                <li className="flex items-start">
                                  <span className="text-red-600 mr-2">•</span>
                                  <div className="w-full">
                                    <span className="text-gray-300">
                                      Association with known threat actor
                                      infrastructure
                                    </span>
                                    <div className="w-full bg-zinc-700/50 rounded h-2 mt-1 overflow-hidden border border-zinc-600">
                                      <div
                                        className="bg-yellow-500 h-2 rounded"
                                        style={{ width: "65%" }}
                                      />
                                    </div>
                                  </div>
                                </li>
                                <li className="flex items-start">
                                  <span className="text-red-600 mr-2">•</span>
                                  <div className="w-full">
                                    <span className="text-gray-300">
                                      Recently observed in multiple attack
                                      campaigns
                                    </span>
                                    <div className="w-full bg-zinc-700/50 rounded h-2 mt-1 overflow-hidden border border-zinc-600">
                                      <div
                                        className="bg-blue-500 h-2 rounded"
                                        style={{ width: "45%" }}
                                      />
                                    </div>
                                  </div>
                                </li>
                              </>
                            )}
                          </ul>
                        </div>

                        <div className="bg-zinc-800 p-4 sm:p-5 rounded-md">
                          <h4 className="text-sm font-medium text-gray-300 mb-2">
                            Model Information
                          </h4>
                          <p className="text-xs text-gray-400">
                            This analysis was performed using SentinelForge's ML
                            Threat Scoring Model{" "}
                            {iocDetail?.scoring_rationale?.model_version ||
                              "v2.3"}
                            , last updated{" "}
                            {iocDetail?.scoring_rationale?.model_last_updated ||
                              "7 days ago"}
                            .
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </TabsContent>

                {/* MITRE ATT&CK Tab Content */}
                <TabsContent
                  value="mitre"
                  className="space-y-6 sm:space-y-8"
                  role="tabpanel"
                  aria-labelledby="mitre-tab"
                >
                  <div className="flex items-center mb-4">
                    <Target className="h-5 w-5 mr-2 text-blue-400" />
                    <h3 className="text-base font-semibold text-gray-200 tracking-tight">
                      MITRE ATT&CK Framework Analysis
                    </h3>
                  </div>

                  <div className="space-y-4 sm:space-y-6">
                    <div className="bg-zinc-800 p-4 sm:p-5 rounded-md">
                      <h4 className="text-sm font-medium text-gray-300 mb-2">
                        Tactics
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {iocDetail?.mitre_tactics &&
                        iocDetail.mitre_tactics.length > 0 ? (
                          iocDetail.mitre_tactics.map((tactic, index) => (
                            <span
                              key={index}
                              className="bg-blue-600/30 text-blue-300 px-2 py-1 rounded text-xs"
                            >
                              {tactic.name}
                            </span>
                          ))
                        ) : (
                          <>
                            <span className="bg-blue-600/30 text-blue-300 px-2 py-1 rounded text-xs">
                              Initial Access
                            </span>
                            <span className="bg-blue-600/30 text-blue-300 px-2 py-1 rounded text-xs">
                              Command & Control
                            </span>
                            <span className="bg-blue-600/30 text-blue-300 px-2 py-1 rounded text-xs">
                              Exfiltration
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="bg-zinc-800 p-4 sm:p-5 rounded-md">
                      <h4 className="text-sm font-medium text-gray-300 mb-2">
                        Techniques
                      </h4>
                      <ul className="space-y-2">
                        {iocDetail?.mitre_techniques &&
                        iocDetail.mitre_techniques.length > 0 ? (
                          iocDetail.mitre_techniques.map((technique, index) => (
                            <li key={index} className="flex justify-between">
                              <span className="text-sm text-gray-300">
                                <a
                                  href={`https://attack.mitre.org/techniques/${technique.id.toLowerCase()}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:underline"
                                >
                                  {technique.id} - {technique.name}
                                </a>
                              </span>
                              <span
                                className={`text-xs ${
                                  technique.confidence === "high"
                                    ? "bg-red-700/40 text-red-300"
                                    : technique.confidence === "medium"
                                      ? "bg-yellow-500/30 text-yellow-200"
                                      : "bg-blue-600/40 text-blue-300"
                                } px-2 py-0.5 rounded-full`}
                              >
                                {technique.confidence.charAt(0).toUpperCase() +
                                  technique.confidence.slice(1)}{" "}
                                Confidence
                              </span>
                            </li>
                          ))
                        ) : (
                          <>
                            <li className="flex justify-between">
                              <span className="text-sm text-gray-300">
                                <a
                                  href="https://attack.mitre.org/techniques/T1566"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:underline"
                                >
                                  T1566 - Phishing
                                </a>
                              </span>
                              <span className="text-xs bg-red-700/40 text-red-300 px-2 py-0.5 rounded-full">
                                High Confidence
                              </span>
                            </li>
                            <li className="flex justify-between">
                              <span className="text-sm text-gray-300">
                                <a
                                  href="https://attack.mitre.org/techniques/T1071"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:underline"
                                >
                                  T1071 - Application Layer Protocol
                                </a>
                              </span>
                              <span className="text-xs bg-yellow-500/30 text-yellow-200 px-2 py-0.5 rounded-full">
                                Medium Confidence
                              </span>
                            </li>
                          </>
                        )}
                      </ul>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              {/* Footer */}
              <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between border-t border-zinc-700 pt-4 mt-6">
                {/* Export Options */}
                <div className="flex space-x-2">
                  <ExportReportButton
                    data={ioc}
                    variant="outline"
                    size="default"
                    className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700 focus:ring-2 focus:ring-blue-600 focus:outline-none mt-2 sm:mt-0"
                  />

                  {/* Share Link Button */}
                  <Button
                    variant="outline"
                    className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700 focus:ring-2 focus:ring-blue-600 focus:outline-none mt-2 sm:mt-0"
                    onClick={handleCopyShareLink}
                  >
                    {copiedText === "share-link" ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                        <span>Link Copied</span>
                      </>
                    ) : (
                      <>
                        <ClipboardCopy className="h-4 w-4 mr-2" />
                        <span>Copy Share Link</span>
                      </>
                    )}
                  </Button>
                </div>

                <div className="flex flex-col-reverse sm:flex-row sm:space-x-2">
                  <Button
                    variant="outline"
                    className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700 focus:ring-2 focus:ring-blue-600 focus:outline-none mt-2 sm:mt-0 min-w-[100px]"
                    onClick={() => onOpenChange(false)}
                  >
                    Close
                  </Button>
                  <Button
                    className="bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-600 focus:outline-none min-w-[100px] relative"
                    onClick={navigateToIocDetail}
                    aria-label="Copy link to clipboard"
                  >
                    <Link2 className="h-4 w-4 mr-2" />
                    {isCopied ? "Copied!" : "Copy Link"}
                    {/* Add link copied tooltip */}
                    <span
                      className={`absolute -top-9 right-1/2 translate-x-1/2 px-2 py-1 bg-zinc-800 text-xs text-gray-200 rounded shadow transition-opacity duration-300 ${
                        isCopied ? "opacity-100" : "opacity-0"
                      }`}
                      aria-live="polite"
                    >
                      Link copied to clipboard!
                    </span>
                  </Button>
                  <Button
                    variant="outline"
                    className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700 focus:ring-2 focus:ring-blue-600 focus:outline-none mt-2 sm:mt-0 min-w-[100px]"
                    onClick={openInNewTab}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open
                  </Button>
                  <Button
                    variant="outline"
                    className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700 focus:ring-2 focus:ring-blue-600 focus:outline-none mt-2 sm:mt-0 min-w-[100px]"
                    onClick={viewInThreatIntelligence}
                  >
                    <Target className="h-4 w-4 mr-2" />
                    View
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </Dialog>
  );
}
