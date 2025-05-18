import React, { useState } from "react";
import {
  Download,
  FileText,
  ChevronDown,
  CheckCircle,
  Loader2,
} from "lucide-react";
import { Button } from "./ui/button";
import { IOCData } from "./IocTable";
import { IocDetailData } from "../hooks/useIocDetail";
import { exportIocData, ExportFormat, ExportScope } from "../utils/exportUtils";

interface ExportReportButtonProps {
  data: IOCData | IocDetailData | IOCData[];
  variant?: "default" | "outline" | "ghost";
  className?: string;
  size?: "default" | "sm" | "lg";
  scope?: ExportScope;
}

const ExportReportButton: React.FC<ExportReportButtonProps> = ({
  data,
  variant = "outline",
  className = "",
  size = "default",
  scope = "single",
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);
    setIsDropdownOpen(false);
    setExportSuccess(false);
    setExportError(null);

    try {
      const title = Array.isArray(data)
        ? `IOCs Report (${data.length} IOCs)`
        : `IOC Report: ${data.value}`;

      await exportIocData(data, format, title);

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error("Error exporting report:", error);
      setExportError("Failed to export report");
      setTimeout(() => setExportError(null), 3000);
    } finally {
      setIsExporting(false);
    }
  };

  const getButtonText = () => {
    if (isExporting) return "Exporting...";
    if (exportSuccess) return "Export Successful!";
    if (exportError) return exportError;
    return "Export Report";
  };

  return (
    <div className="relative">
      <div className="flex">
        <Button
          variant={variant}
          size={size}
          className={`${className} ${isExporting ? "opacity-70" : ""} ${
            exportSuccess ? "bg-green-700 text-white border-green-600" : ""
          } ${exportError ? "bg-red-700 text-white border-red-600" : ""}`}
          onClick={() => !isExporting && setIsDropdownOpen(!isDropdownOpen)}
          disabled={isExporting}
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : exportSuccess ? (
            <CheckCircle className="h-4 w-4 mr-2" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          {getButtonText()}
          <ChevronDown className="h-4 w-4 ml-2" />
        </Button>
      </div>

      {isDropdownOpen && (
        <div className="absolute z-50 top-full mt-1 right-0 min-w-[200px] bg-zinc-800 border border-zinc-700 rounded-md shadow-lg p-1">
          <button
            className="w-full text-left px-3 py-2 flex items-center text-sm text-gray-300 hover:bg-zinc-700 rounded"
            onClick={() => handleExport("pdf")}
          >
            <FileText className="h-4 w-4 mr-2 text-red-400" />
            Export as PDF
          </button>
          <button
            className="w-full text-left px-3 py-2 flex items-center text-sm text-gray-300 hover:bg-zinc-700 rounded"
            onClick={() => handleExport("markdown")}
          >
            <FileText className="h-4 w-4 mr-2 text-blue-400" />
            Export as Markdown
          </button>
        </div>
      )}
    </div>
  );
};

export default ExportReportButton;
