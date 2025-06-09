import React, { useState, useRef, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "./ui/card";
import { Badge } from "./ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { Progress } from "./ui/progress";
import { Alert, AlertDescription } from "./ui/alert";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";
import { Switch } from "./ui/switch";
import { Slider } from "./ui/slider";
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  X,
  FileJson,
  ShieldCheck,
  FileType,
  Settings,
  Zap,
  Clock,
} from "lucide-react";
import { toast } from "../lib/toast";

interface UploadFeedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

interface UploadResult {
  success: boolean;
  message?: string;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: string[];
  total_records: number;
  duration_seconds: number;
}

type UploadStatus = "idle" | "uploading" | "parsing" | "success" | "error";

interface UploadProgress {
  status: UploadStatus;
  progress: number;
  message: string;
}

export const UploadFeedModal: React.FC<UploadFeedModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceFeed, setSourceFeed] = useState("");
  const [justification, setJustification] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    status: "idle",
    progress: 0,
    message: "",
  });

  // Advanced Settings State
  const [enableScheduling, setEnableScheduling] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState([75]);
  const [enableDeduplication, setEnableDeduplication] = useState(true);
  const [enableValidation, setEnableValidation] = useState(true);
  const [batchSize, setBatchSize] = useState([1000]);
  const [retryAttempts, setRetryAttempts] = useState([3]);

  const supportedFormats = [".csv", ".json", ".txt", ".stix"];
  const maxFileSize = 10 * 1024 * 1024; // 10MB

  // Focus management - focus first input when modal opens
  useEffect(() => {
    if (isOpen && firstInputRef.current) {
      const timer = setTimeout(() => {
        firstInputRef.current?.focus();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Enhanced keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return;

      // ESC key handling (already handled by Radix Dialog, but we can add custom logic)
      if (event.key === "Escape" && !uploading) {
        onClose();
      }

      // Enter key to submit when focused on inputs (but not textarea)
      if (event.key === "Enter" && !event.shiftKey) {
        const target = event.target as HTMLElement;
        if (target.tagName === "INPUT" && selectedFile && sourceFeed.trim()) {
          event.preventDefault();
          // handleUpload will be called when available
        }
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, uploading, selectedFile, sourceFeed, onClose]);

  const handleFileSelect = (file: File) => {
    // Validate file type
    const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
    if (!supportedFormats.includes(fileExtension)) {
      toast.error(
        `Unsupported file type. Supported formats: ${supportedFormats.join(", ")}`,
      );
      return;
    }

    // Validate file size
    if (file.size > maxFileSize) {
      toast.error("File size must be less than 10MB");
      return;
    }

    setSelectedFile(file);
    setUploadResult(null);
    setUploadProgress({
      status: "idle",
      progress: 0,
      message: "",
    });
  };

  const handleFileInputChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);

    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error("Please select a file to upload");
      return;
    }

    if (!sourceFeed.trim()) {
      toast.error("Please enter a source feed name");
      return;
    }

    setUploading(true);
    setUploadResult(null);

    // Initialize upload progress
    setUploadProgress({
      status: "uploading",
      progress: 10,
      message: "Preparing file upload...",
    });

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("source_feed", sourceFeed.trim());
      formData.append("justification", justification.trim());

      // Add advanced settings
      formData.append("enable_scheduling", enableScheduling.toString());
      formData.append(
        "confidence_threshold",
        confidenceThreshold[0].toString(),
      );
      formData.append("enable_deduplication", enableDeduplication.toString());
      formData.append("enable_validation", enableValidation.toString());
      formData.append("batch_size", batchSize[0].toString());
      formData.append("retry_attempts", retryAttempts[0].toString());

      // Update progress for upload start
      setUploadProgress({
        status: "uploading",
        progress: 30,
        message: "Uploading file to server...",
      });

      const response = await fetch("/api/feeds/upload", {
        method: "POST",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: formData,
      });

      // Update progress for parsing
      setUploadProgress({
        status: "parsing",
        progress: 70,
        message: "Processing and parsing threat data...",
      });

      const result = await response.json();

      // Update progress for completion
      setUploadProgress({
        status: response.ok ? "success" : "error",
        progress: 100,
        message: response.ok
          ? "Upload completed successfully!"
          : "Upload failed",
      });

      if (response.ok) {
        setUploadResult({
          success: true,
          message: result.message,
          imported_count: result.imported_count,
          skipped_count: result.skipped_count,
          error_count: result.error_count,
          errors: result.errors || [],
          total_records: result.total_records,
          duration_seconds: result.duration_seconds,
        });

        toast.success(
          `Upload completed: ${result.imported_count} imported, ${result.skipped_count} skipped`,
        );

        if (onSuccess) {
          onSuccess();
        }
      } else {
        setUploadResult({
          success: false,
          message: result.error,
          imported_count: result.imported_count || 0,
          skipped_count: result.skipped_count || 0,
          error_count: result.error_count || 0,
          errors: result.errors || [],
          total_records: 0,
          duration_seconds: 0,
        });

        toast.error(result.error || "Upload failed");
      }
    } catch (error) {
      toast.error("Upload failed: Network error");
      setUploadProgress({
        status: "error",
        progress: 100,
        message: "Network error occurred",
      });
      setUploadResult({
        success: false,
        message: "Network error occurred",
        imported_count: 0,
        skipped_count: 0,
        error_count: 0,
        errors: [],
        total_records: 0,
        duration_seconds: 0,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setSelectedFile(null);
      setSourceFeed("");
      setJustification("");
      setUploadResult(null);
      setUploadProgress({
        status: "idle",
        progress: 0,
        message: "",
      });
      // Reset advanced settings
      setEnableScheduling(false);
      setConfidenceThreshold([75]);
      setEnableDeduplication(true);
      setEnableValidation(true);
      setBatchSize([1000]);
      setRetryAttempts([3]);
      onClose();
    }
  };

  const getFileIcon = () => {
    return <FileText className="h-8 w-8 text-primary" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFormatIcon = (format: string) => {
    switch (format.toLowerCase()) {
      case ".csv":
        return (
          <FileText className="h-6 w-6 text-green-600 dark:text-green-400" />
        );
      case ".json":
        return (
          <FileJson className="h-6 w-6 text-blue-600 dark:text-blue-400" />
        );
      case ".stix":
        return (
          <ShieldCheck className="h-6 w-6 text-purple-600 dark:text-purple-400" />
        );
      case ".txt":
        return <FileType className="h-6 w-6 text-muted-foreground" />;
      default:
        return <FileText className="h-6 w-6 text-muted-foreground" />;
    }
  };

  const getFormatDescription = (format: string) => {
    switch (format.toLowerCase()) {
      case ".csv":
        return "Comma-Separated Values - Structured tabular data format";
      case ".json":
        return "JavaScript Object Notation - Structured data interchange format";
      case ".stix":
        return "Structured Threat Information eXpression - Cyber threat intelligence format";
      case ".txt":
        return "Plain Text - Simple text-based format";
      default:
        return "Supported file format";
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="w-full max-w-screen-sm sm:max-w-2xl max-h-[95vh] overflow-y-auto">
        <DialogHeader className="pb-4">
          <DialogTitle className="text-lg sm:text-xl">
            Upload Threat Feed
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 sm:space-y-6">
          {/* File Upload Area */}
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                File Selection
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 sm:space-y-6">
              {/* Supported Formats Display */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-foreground">
                  Supported Formats
                </h4>
                <TooltipProvider>
                  <div className="flex items-center justify-center gap-2 sm:gap-4 p-3 bg-muted/50 rounded-lg border border-border">
                    {supportedFormats.map((format) => (
                      <Tooltip key={format}>
                        <TooltipTrigger asChild>
                          <div className="flex flex-col items-center gap-1 p-2 rounded-md hover:bg-white hover:shadow-sm transition-all duration-200 cursor-help">
                            {getFormatIcon(format)}
                            <span className="text-xs font-medium text-muted-foreground uppercase">
                              {format.replace(".", "")}
                            </span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" className="max-w-xs">
                          <p className="font-medium">
                            {format.toUpperCase()} Format
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {getFormatDescription(format)}
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    ))}
                  </div>
                </TooltipProvider>
                <p className="text-xs text-muted-foreground text-center">
                  Maximum file size: 10MB
                </p>
              </div>
              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  dragOver
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-border/80"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {selectedFile ? (
                  <div className="flex items-center justify-center space-x-3">
                    {getFileIcon()}
                    <div className="text-left">
                      <p className="font-medium text-foreground">
                        {selectedFile.name}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedFile(null)}
                      className="min-h-[44px] min-w-[44px] sm:min-h-[36px] sm:min-w-[36px] flex items-center justify-center"
                      aria-label="Remove selected file"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <div>
                    <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-2">
                      Drag and drop your file here, or{" "}
                      <button
                        type="button"
                        className="text-primary hover:text-primary/80 underline"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        browse
                      </button>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Choose from the supported formats above
                    </p>
                  </div>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept={supportedFormats.join(",")}
                onChange={handleFileInputChange}
                className="hidden"
              />
            </CardContent>
          </Card>

          {/* Form Fields */}
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Feed Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 sm:space-y-6">
              <div className="space-y-3">
                <Label htmlFor="source_feed" className="text-sm font-medium">
                  Source Feed Name *
                </Label>
                <Input
                  ref={firstInputRef}
                  id="source_feed"
                  value={sourceFeed}
                  onChange={(e) => setSourceFeed(e.target.value)}
                  placeholder="e.g., Manual Upload, Custom Feed"
                  disabled={uploading}
                  data-testid="upload-source-feed-input"
                  className="min-h-[44px] sm:min-h-[40px]"
                />
                <p className="text-xs text-gray-500">
                  Specify the threat intelligence source for this data
                </p>
              </div>

              <div className="space-y-3">
                <Label htmlFor="justification" className="text-sm font-medium">
                  Justification (Optional)
                </Label>
                <Textarea
                  id="justification"
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  placeholder="Reason for importing this feed..."
                  rows={3}
                  disabled={uploading}
                  className="min-h-[88px] resize-none"
                />
                <p className="text-xs text-gray-500">
                  Optional context for audit trail and compliance
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Advanced Settings */}
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Advanced Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="advanced-settings">
                  <AccordionTrigger className="text-sm font-medium">
                    Configure advanced upload options
                  </AccordionTrigger>
                  <AccordionContent className="space-y-6">
                    {/* Processing Options */}
                    <div className="space-y-4">
                      <h4 className="text-sm font-medium text-gray-900 flex items-center gap-2">
                        <ShieldCheck className="h-4 w-4" />
                        Processing Options
                      </h4>

                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <Label className="text-sm font-medium">
                            Enable Deduplication
                          </Label>
                          <p className="text-xs text-gray-500">
                            Remove duplicate IOCs during import
                          </p>
                        </div>
                        <Switch
                          checked={enableDeduplication}
                          onCheckedChange={setEnableDeduplication}
                          disabled={uploading}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <Label className="text-sm font-medium">
                            Enable Validation
                          </Label>
                          <p className="text-xs text-gray-500">
                            Validate IOC formats and syntax
                          </p>
                        </div>
                        <Switch
                          checked={enableValidation}
                          onCheckedChange={setEnableValidation}
                          disabled={uploading}
                        />
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label className="text-sm font-medium">
                            Confidence Threshold: {confidenceThreshold[0]}%
                          </Label>
                        </div>
                        <Slider
                          value={confidenceThreshold}
                          onValueChange={setConfidenceThreshold}
                          max={100}
                          min={0}
                          step={5}
                          className="w-full"
                          disabled={uploading}
                        />
                        <p className="text-xs text-gray-500">
                          Minimum confidence level for imported IOCs
                        </p>
                      </div>
                    </div>

                    {/* Performance Options */}
                    <div className="space-y-4 pt-4 border-t">
                      <h4 className="text-sm font-medium text-gray-900 flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Performance Options
                      </h4>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label className="text-sm font-medium">
                            Batch Size: {batchSize[0]} records
                          </Label>
                        </div>
                        <Slider
                          value={batchSize}
                          onValueChange={setBatchSize}
                          max={5000}
                          min={100}
                          step={100}
                          className="w-full"
                          disabled={uploading}
                        />
                        <p className="text-xs text-gray-500">
                          Number of records to process in each batch
                        </p>
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label className="text-sm font-medium">
                            Retry Attempts: {retryAttempts[0]}
                          </Label>
                        </div>
                        <Slider
                          value={retryAttempts}
                          onValueChange={setRetryAttempts}
                          max={10}
                          min={0}
                          step={1}
                          className="w-full"
                          disabled={uploading}
                        />
                        <p className="text-xs text-gray-500">
                          Number of retry attempts for failed records
                        </p>
                      </div>
                    </div>

                    {/* Scheduling Options */}
                    <div className="space-y-4 pt-4 border-t">
                      <h4 className="text-sm font-medium text-gray-900 flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        Scheduling Options
                      </h4>

                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <Label className="text-sm font-medium">
                            Enable Scheduled Processing
                          </Label>
                          <p className="text-xs text-gray-500">
                            Process upload during off-peak hours
                          </p>
                        </div>
                        <Switch
                          checked={enableScheduling}
                          onCheckedChange={setEnableScheduling}
                          disabled={uploading}
                        />
                      </div>

                      {enableScheduling && (
                        <div className="ml-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                          <p className="text-xs text-blue-700">
                            <strong>Note:</strong> Scheduled uploads will be
                            queued and processed during the next maintenance
                            window (typically 2-4 AM UTC).
                          </p>
                        </div>
                      )}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>

          {/* Upload Progress Indicator */}
          {uploadProgress.status !== "idle" && (
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {uploadProgress.status === "uploading" && (
                    <Upload className="h-5 w-5 text-blue-500 animate-pulse" />
                  )}
                  {uploadProgress.status === "parsing" && (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500" />
                  )}
                  {uploadProgress.status === "success" && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  {uploadProgress.status === "error" && (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  Upload Progress
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">
                      {uploadProgress.message}
                    </span>
                    <span className="text-sm text-gray-500">
                      {uploadProgress.progress}%
                    </span>
                  </div>
                  <Progress
                    value={uploadProgress.progress}
                    className="w-full h-2"
                  />
                </div>

                {uploadProgress.status === "success" && (
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      File uploaded and processed successfully! Check the
                      results below.
                    </AlertDescription>
                  </Alert>
                )}

                {uploadProgress.status === "error" && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Upload failed. Please check your file format and try
                      again.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

          {/* Upload Result */}
          {uploadResult && (
            <Card
              className={`shadow-md ${uploadResult.success ? "border-green-200 bg-green-50/50" : "border-red-200 bg-red-50/50"}`}
            >
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {uploadResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  {uploadResult.success ? "Upload Successful" : "Upload Failed"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex-1">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-sm">
                        <span className="text-gray-600">Imported:</span>
                        <Badge variant="default" className="ml-2">
                          {uploadResult.imported_count}
                        </Badge>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-600">Skipped:</span>
                        <Badge variant="secondary" className="ml-2">
                          {uploadResult.skipped_count}
                        </Badge>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-600">Errors:</span>
                        <Badge variant="destructive" className="ml-2">
                          {uploadResult.error_count}
                        </Badge>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-600">Duration:</span>
                        <span className="ml-2">
                          {uploadResult.duration_seconds}s
                        </span>
                      </div>
                    </div>

                    {uploadResult.errors.length > 0 && (
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">
                          Errors:
                        </h5>
                        <div className="bg-red-50 border border-red-200 rounded p-3 max-h-32 overflow-y-auto">
                          {uploadResult.errors
                            .slice(0, 10)
                            .map((error, index) => (
                              <p
                                key={index}
                                className="text-sm text-red-700 mb-1"
                              >
                                {error}
                              </p>
                            ))}
                          {uploadResult.errors.length > 10 && (
                            <p className="text-sm text-red-600 italic">
                              ... and {uploadResult.errors.length - 10} more
                              errors
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <Card className="shadow-md">
            <CardFooter className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 sm:gap-3 pt-4 sm:pt-6">
              <Button
                variant="outline"
                onClick={handleClose}
                disabled={uploading}
                aria-label={
                  uploadResult?.success
                    ? "Close upload dialog"
                    : "Cancel upload"
                }
                data-testid="upload-modal-cancel"
                className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
              >
                {uploadResult?.success ? "Close" : "Cancel"}
              </Button>
              {!uploadResult?.success && (
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || !sourceFeed.trim() || uploading}
                  aria-label="Upload and import threat intelligence feed"
                  data-testid="upload-modal-submit"
                  className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload & Import
                    </>
                  )}
                </Button>
              )}
            </CardFooter>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
};
