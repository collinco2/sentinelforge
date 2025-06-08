import React, { useState, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Upload, FileText, AlertCircle, CheckCircle, X } from "lucide-react";
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

export const UploadFeedModal: React.FC<UploadFeedModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceFeed, setSourceFeed] = useState("");
  const [justification, setJustification] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const supportedFormats = [".csv", ".json", ".txt", ".stix"];
  const maxFileSize = 10 * 1024 * 1024; // 10MB

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

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("source_feed", sourceFeed.trim());
      formData.append("justification", justification.trim());

      const response = await fetch("/api/feeds/upload", {
        method: "POST",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: formData,
      });

      const result = await response.json();

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
      onClose();
    }
  };

  const getFileIcon = () => {
    return <FileText className="h-8 w-8 text-blue-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Threat Feed</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* File Upload Area */}
          <div>
            <Label>Select File</Label>
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragOver
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {selectedFile ? (
                <div className="flex items-center justify-center space-x-3">
                  {getFileIcon()}
                  <div className="text-left">
                    <p className="font-medium text-gray-900">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div>
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">
                    Drag and drop your file here, or{" "}
                    <button
                      type="button"
                      className="text-blue-600 hover:text-blue-700 underline"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      browse
                    </button>
                  </p>
                  <p className="text-sm text-gray-500">
                    Supported formats: {supportedFormats.join(", ")} (max 10MB)
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
          </div>

          {/* Form Fields */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="source_feed">Source Feed Name *</Label>
              <Input
                id="source_feed"
                value={sourceFeed}
                onChange={(e) => setSourceFeed(e.target.value)}
                placeholder="e.g., Manual Upload, Custom Feed"
                disabled={uploading}
              />
            </div>

            <div>
              <Label htmlFor="justification">Justification (Optional)</Label>
              <Textarea
                id="justification"
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                placeholder="Reason for importing this feed..."
                rows={3}
                disabled={uploading}
              />
            </div>
          </div>

          {/* Upload Result */}
          {uploadResult && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start space-x-3">
                  {uploadResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 mb-2">
                      {uploadResult.success
                        ? "Upload Successful"
                        : "Upload Failed"}
                    </h4>

                    <div className="grid grid-cols-2 gap-4 mb-4">
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
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={uploading}
            >
              {uploadResult?.success ? "Close" : "Cancel"}
            </Button>
            {!uploadResult?.success && (
              <Button
                onClick={handleUpload}
                disabled={!selectedFile || !sourceFeed.trim() || uploading}
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
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
