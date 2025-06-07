// Debug utilities for SentinelForge API 
export const API_DEBUG = true; // Set to false in production

export function logApiCall(source: string, url: string): void {
  if (API_DEBUG) {
    console.log(`[${source}] Fetching API: ${url}`);
  }
}

export function logApiResponse(source: string, url: string, data: any): void {
  if (API_DEBUG) {
    console.log(`[${source}] Response from ${url}:`, data);
    
    if (Array.isArray(data?.iocs)) {
      console.log(`[${source}] Received ${data.iocs.length} IOCs`);
    }
    
    if (data?.total) {
      console.log(`[${source}] Total records: ${data.total}`);
    }
  }
}

export function logApiError(source: string, url: string, error: any): void {
  console.error(`[${source}] API error from ${url}:`, error);
  
  if (error?.response) {
    console.error(`[${source}] Status: ${error.response.status}`);
    console.error(`[${source}] Data:`, error.response.data);
  }
} 