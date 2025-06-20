import axios from "axios";
import { getAuthHeaders } from "./auth";

// API base URL
export const API_BASE_URL = "http://localhost:5059";

// Define interfaces for our data models
export interface IOC {
  id: number;
  ioc_value: string;
  ioc_type: string;
  score: number;
  timestamp: number;
  source: string;
  value?: string; // Alias for ioc_value
}

export interface ExtendedIOC extends IOC {
  threat_class?: string;
  malicious_probability?: number;
  feature_importance?: Array<{
    feature: string;
    weight: number;
  }>;
  whois?: {
    registrar?: string;
    creation_date?: string;
    expiration_date?: string;
    updated_date?: string;
    name_servers?: string[];
  };
  geolocation?: {
    country?: string;
    city?: string;
    latitude?: number;
    longitude?: number;
    asn?: string;
    org?: string;
  };
  attack_techniques?: Array<{
    id: string;
    name: string;
    description: string;
  }>;
}

export interface Stats {
  total_iocs: number;
  high_risk_iocs: number;
  new_iocs: number;
  avg_score: number;
  ioc_types: {
    [key: string]: number;
  };
  risk_categories: {
    [key: string]: number;
  };
}

export interface MLExplanation {
  summary: string;
  feature_breakdown: Array<{
    feature: string;
    value: string;
    weight: number;
  }>;
  timeline_prediction: Array<{
    event: string;
    probability: number;
    timeframe: string;
  }>;
}

// API Functions
export async function fetchStats(): Promise<Stats> {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/stats`);
    return response.data;
  } catch (error) {
    console.error("Error fetching stats:", error);
    return {
      total_iocs: 0,
      high_risk_iocs: 0,
      new_iocs: 0,
      avg_score: 0,
      ioc_types: {},
      risk_categories: {},
    };
  }
}

export async function fetchIOCs(
  limit = 10,
  offset = 0,
  minScore = 0,
  maxScore = 10,
  iocType?: string,
  search?: string,
): Promise<IOC[]> {
  try {
    let url = `${API_BASE_URL}/api/iocs?limit=${limit}&offset=${offset}&min_score=${minScore}&max_score=${maxScore}`;

    if (iocType) {
      url += `&ioc_type=${iocType}`;
    }

    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }

    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error("Error fetching IOCs:", error);
    return [];
  }
}

export async function fetchIOC(iocValue: string): Promise<ExtendedIOC | null> {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/ioc/${encodeURIComponent(iocValue)}`,
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching IOC ${iocValue}:`, error);
    return null;
  }
}

export async function fetchMLExplanation(
  iocValue: string,
): Promise<MLExplanation | null> {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/explain/${encodeURIComponent(iocValue)}`,
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching ML explanation for ${iocValue}:`, error);
    return null;
  }
}

// Audit logging interfaces and functions
export interface AuditLogEntry {
  id: number;
  alert_id: number;
  alert_name: string;
  user_id: number;
  original_score: number;
  override_score: number;
  justification: string;
  timestamp: string;
}

export interface AuditLogsResponse {
  audit_logs: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditFilters {
  alert_id?: number;
  user_id?: number;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

// User management interfaces
export interface User {
  user_id: number;
  username: string;
  email: string;
  role: "viewer" | "analyst" | "auditor" | "admin";
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UsersResponse {
  users: User[];
  total: number;
}

export interface RoleUpdateRequest {
  role: "viewer" | "analyst" | "auditor" | "admin";
}

export interface RoleUpdateResponse {
  message: string;
  user: User;
  old_role: string;
  new_role: string;
}

export interface RoleChangeAuditLog {
  id: number;
  alert_id: number; // Negative for role changes
  user_id: number; // Admin who made the change
  admin_username: string;
  original_score: number; // Not applicable for role changes
  override_score: number; // Not applicable for role changes
  justification: string; // Contains role change details
  timestamp: string;
  action: string; // "role_change"
  target_user_id: number; // User whose role was changed
}

export interface RoleChangeAuditResponse {
  audit_logs: RoleChangeAuditLog[];
  total: number;
  limit: number;
  offset: number;
}

export async function fetchAuditLogs(
  filters: AuditFilters = {},
): Promise<AuditLogsResponse | null> {
  try {
    const params = new URLSearchParams();

    if (filters.alert_id)
      params.append("alert_id", filters.alert_id.toString());
    if (filters.user_id) params.append("user_id", filters.user_id.toString());
    if (filters.start_date) params.append("start_date", filters.start_date);
    if (filters.end_date) params.append("end_date", filters.end_date);
    if (filters.limit) params.append("limit", filters.limit.toString());
    if (filters.offset) params.append("offset", filters.offset.toString());

    const response = await axios.get(
      `${API_BASE_URL}/api/audit?${params.toString()}`,
      {
        headers: getAuthHeaders(),
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error fetching audit logs:", error);
    return null;
  }
}

export interface RiskScoreOverride {
  risk_score: number;
  justification?: string;
  user_id?: number;
}

export async function overrideAlertRiskScore(
  alertId: number | string,
  override: RiskScoreOverride,
): Promise<any> {
  try {
    const response = await axios.patch(
      `${API_BASE_URL}/api/alert/${alertId}/override`,
      override,
      {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
      },
    );
    return response.data;
  } catch (error) {
    console.error(`Error overriding risk score for alert ${alertId}:`, error);
    throw error;
  }
}

export async function exportToCSV(): Promise<void> {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/export/csv`, {
      responseType: "blob",
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `sentinelforge-iocs-${new Date().toISOString().slice(0, 10)}.csv`,
    );
    document.body.appendChild(link);
    link.click();

    // Clean up
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
  } catch (error) {
    console.error("Error exporting to CSV:", error);
    alert("Failed to export data. Please try again later.");
  }
}

// User management API functions
export async function getUsers(): Promise<UsersResponse> {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/users`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching users:", error);
    throw error;
  }
}

export async function updateUserRole(
  userId: number,
  newRole: "viewer" | "analyst" | "auditor" | "admin",
): Promise<RoleUpdateResponse> {
  try {
    const response = await axios.patch(
      `${API_BASE_URL}/api/user/${userId}/role`,
      { role: newRole },
      {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error updating user role:", error);
    throw error;
  }
}

export async function getRoleChangeAuditLogs(
  filters: { user_id?: number; limit?: number; offset?: number } = {},
): Promise<RoleChangeAuditResponse> {
  try {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const response = await axios.get(
      `${API_BASE_URL}/api/audit/roles?${params.toString()}`,
      {
        headers: getAuthHeaders(),
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error fetching role change audit logs:", error);
    throw error;
  }
}

// ============================================================================
// THREAT FEED MANAGEMENT API
// ============================================================================

export interface ThreatFeed {
  id: number;
  name: string;
  description: string;
  url: string;
  feed_type: string;
  format_config: Record<string, any>;
  is_active: boolean;
  auto_import: boolean;
  import_frequency: number;
  last_import: string | null;
  last_import_status: string | null;
  last_import_count: number;
  created_by: number;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface FeedImportLog {
  id: number;
  feed_id: number | null;
  feed_name: string;
  import_type: string;
  file_name: string | null;
  file_size: number | null;
  total_records: number;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: string[];
  import_status: string;
  duration_seconds: number | null;
  user_id: number;
  user_name: string;
  justification: string | null;
  timestamp: string;
}

export interface FeedCreateRequest {
  name: string;
  description?: string;
  url?: string;
  feed_type: string;
  format_config?: Record<string, any>;
  is_active?: boolean;
  auto_import?: boolean;
  import_frequency?: number;
}

export interface FeedUpdateRequest {
  name?: string;
  description?: string;
  url?: string;
  feed_type?: string;
  format_config?: Record<string, any>;
  is_active?: boolean;
  auto_import?: boolean;
  import_frequency?: number;
}

export interface ImportResult {
  success: boolean;
  message?: string;
  error?: string;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: string[];
  total_records: number;
  duration_seconds: number;
  log_id?: number;
}

// Get all threat feeds
export async function getFeeds(): Promise<{ feeds: ThreatFeed[] }> {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/feeds`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching feeds:", error);
    throw error;
  }
}

// Create a new threat feed
export async function createFeed(
  feed: FeedCreateRequest,
): Promise<{ message: string; feed_id: number }> {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/feeds`, feed, {
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error creating feed:", error);
    throw error;
  }
}

// Update a threat feed
export async function updateFeed(
  feedId: number,
  updates: FeedUpdateRequest,
): Promise<{ message: string }> {
  try {
    const response = await axios.patch(
      `${API_BASE_URL}/api/feeds/${feedId}`,
      updates,
      {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error updating feed:", error);
    throw error;
  }
}

// Delete a threat feed
export async function deleteFeed(feedId: number): Promise<{ message: string }> {
  try {
    const response = await axios.delete(`${API_BASE_URL}/api/feeds/${feedId}`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    console.error("Error deleting feed:", error);
    throw error;
  }
}

// Import from a feed URL
export async function importFromFeed(
  feedId: number,
  justification?: string,
): Promise<ImportResult> {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/feeds/${feedId}/import`,
      { justification },
      {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error importing from feed:", error);
    throw error;
  }
}

// Upload and import a file
export async function uploadFeed(
  file: File,
  sourceFeed: string,
  justification?: string,
): Promise<ImportResult> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("source_feed", sourceFeed);
    if (justification) {
      formData.append("justification", justification);
    }

    const response = await axios.post(
      `${API_BASE_URL}/api/feeds/upload`,
      formData,
      {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error uploading feed:", error);
    throw error;
  }
}

// Get import logs
export async function getImportLogs(
  filters: {
    feed_id?: number;
    import_status?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<{ logs: FeedImportLog[]; total: number }> {
  try {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const response = await axios.get(
      `${API_BASE_URL}/api/feeds/import-logs?${params.toString()}`,
      {
        headers: getAuthHeaders(),
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error fetching import logs:", error);
    throw error;
  }
}
