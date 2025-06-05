import React, { useState, useEffect, useCallback } from "react";
import {
  Clock,
  User,
  Edit3,
  FileText,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Info,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { fetchAuditLogs, AuditLogEntry } from "../services/api";

interface AuditTrailViewProps {
  alertId: number;
  className?: string;
}

export function AuditTrailView({
  alertId,
  className = "",
}: AuditTrailViewProps) {
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const fetchAuditLogsData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAuditLogs({ alert_id: alertId, limit: 50 });
      if (data) {
        setAuditLogs(data.audit_logs || []);
      } else {
        throw new Error("Failed to fetch audit logs");
      }
    } catch (err) {
      console.error("Error fetching audit logs:", err);
      setError(
        err instanceof Error ? err.message : "Failed to fetch audit logs",
      );
      setAuditLogs([]);
    } finally {
      setIsLoading(false);
    }
  }, [alertId]);

  // Fetch audit logs for the specific alert
  useEffect(() => {
    if (alertId) {
      fetchAuditLogsData();
    }
  }, [alertId, fetchAuditLogsData]);

  const toggleRowExpansion = (logId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedRows(newExpanded);
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getRiskScoreBadgeColor = (score: number) => {
    if (score >= 80) return "bg-red-600 hover:bg-red-700";
    if (score >= 50) return "bg-orange-500 hover:bg-orange-600";
    return "bg-green-600 hover:bg-green-700";
  };

  const getScoreChangeIcon = (original: number, override: number) => {
    if (override > original) {
      return <ChevronUp className="h-4 w-4 text-red-400" />;
    } else if (override < original) {
      return <ChevronDown className="h-4 w-4 text-green-400" />;
    }
    return <Edit3 className="h-4 w-4 text-blue-400" />;
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <Loader2
          className="h-6 w-6 animate-spin text-blue-500"
          data-testid="loading-spinner"
        />
        <span className="ml-2 text-gray-400">Loading audit trail...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="flex items-center text-red-400 mb-4">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span>Error loading audit trail</span>
        </div>
        <p className="text-gray-400 text-sm mb-4">{error}</p>
        <Button
          onClick={fetchAuditLogsData}
          variant="outline"
          size="sm"
          className="text-blue-400 border-blue-400 hover:bg-blue-400 hover:text-white"
        >
          Retry
        </Button>
      </div>
    );
  }

  if (auditLogs.length === 0) {
    return (
      <div className={`p-6 text-center ${className}`}>
        <FileText className="h-12 w-12 text-gray-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-300 mb-2">
          No Audit Trail
        </h3>
        <p className="text-gray-400 text-sm">
          No risk score overrides have been recorded for this alert yet.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Info Banner */}
      <div className="bg-blue-900/20 border border-blue-700/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-200 mb-1">
              Audit Trail Information
            </h4>
            <p className="text-sm text-blue-300/80">
              All risk overrides are logged here for transparency. Only
              authorized roles can view this log. This immutable record supports
              security compliance and accountability.
            </p>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-200 flex items-center">
          <Clock className="h-5 w-5 mr-2" />
          Audit Trail ({auditLogs.length})
        </h3>
        <Button
          onClick={fetchAuditLogsData}
          variant="outline"
          size="sm"
          className="text-blue-400 border-blue-400 hover:bg-blue-400 hover:text-white"
        >
          Refresh
        </Button>
      </div>

      {/* Audit logs table */}
      <div className="bg-zinc-800 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-700">
              <TableHead className="text-gray-300">Timestamp</TableHead>
              <TableHead className="text-gray-300">User</TableHead>
              <TableHead className="text-gray-300">Score Change</TableHead>
              <TableHead className="text-gray-300">Justification</TableHead>
              <TableHead className="text-gray-300 w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {auditLogs.map((log) => (
              <React.Fragment key={log.id}>
                <TableRow className="border-zinc-700 hover:bg-zinc-750">
                  <TableCell className="text-gray-300">
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 mr-2 text-gray-400" />
                      <span className="text-sm">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-gray-300">
                    <div className="flex items-center">
                      <User className="h-4 w-4 mr-2 text-gray-400" />
                      <span>User {log.user_id}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Badge
                        className={getRiskScoreBadgeColor(log.original_score)}
                      >
                        {log.original_score}
                      </Badge>
                      {getScoreChangeIcon(
                        log.original_score,
                        log.override_score,
                      )}
                      <Badge
                        className={getRiskScoreBadgeColor(log.override_score)}
                      >
                        {log.override_score}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-gray-300">
                    {log.justification ? (
                      <div className="max-w-xs">
                        <span className="text-sm">
                          {log.justification.length > 50
                            ? `${log.justification.substring(0, 50)}...`
                            : log.justification}
                        </span>
                        {log.justification.length > 50 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleRowExpansion(log.id)}
                            className="ml-2 p-0 h-auto text-blue-400 hover:text-blue-300"
                          >
                            {expandedRows.has(log.id) ? "Less" : "More"}
                          </Button>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-500 italic text-sm">
                        No justification provided
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Edit3 className="h-4 w-4 text-gray-400" />
                  </TableCell>
                </TableRow>
                {/* Expanded row for full justification */}
                {expandedRows.has(log.id) && log.justification.length > 50 && (
                  <TableRow className="border-zinc-700 bg-zinc-850">
                    <TableCell colSpan={5} className="text-gray-300">
                      <div className="p-3 bg-zinc-900 rounded-md">
                        <h4 className="text-sm font-medium text-gray-200 mb-2">
                          Full Justification:
                        </h4>
                        <p className="text-sm text-gray-300">
                          {log.justification}
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
