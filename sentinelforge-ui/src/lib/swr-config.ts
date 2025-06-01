import axios from 'axios';
import { logApiCall, logApiResponse, logApiError } from '../hooks/debug';

// Global API fetcher for SWR
export const fetcher = async (url: string) => {
  try {
    logApiCall("swrConfig", url);
    
    const response = await axios.get(url, {
      // Set timeout to prevent hanging requests
      timeout: 15000,
      // Don't follow redirects to prevent redirect loops
      maxRedirects: 0,
      // Custom validation to handle different status codes
      validateStatus: (status) => status < 500
    });
    
    logApiResponse("swrConfig", url, response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      logApiError("swrConfig", url, error);
      
      if (error.code === 'ECONNABORTED') {
        throw new Error(`Request to ${url} timed out`);
      }
      
      if (error.response?.status === 404) {
        throw new Error(`Resource not found: ${url}`);
      } else if (error.response?.status && error.response.status >= 500) {
        throw new Error(`Server error (${error.response?.status}): ${error.message}`);
      }
    }
    throw error;
  }
};

// Global SWR configuration
export const swrConfig = {
  // Use the API_URL environment variable with fallback
  fetcher,
  revalidateOnFocus: true,
  revalidateOnReconnect: true,
  refreshInterval: 0, // Don't auto-refresh by default
  shouldRetryOnError: true,
  dedupingInterval: 5000,
  errorRetryCount: 3,
  onError: (error: any, key: string) => {
    // Log all SWR errors to the console
    logApiError("SWR", key, error);
  }
}; 