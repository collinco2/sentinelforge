import useSWR from 'swr';
import axios from 'axios';
import { IocFilters } from '../components/FilterSidebar';
import { IOCData } from '../components/IocTable';

// Base API URL
const API_URL = '/api/iocs';

// Fetcher function for SWR
const fetcher = async (url: string) => {
  const response = await axios.get(url);
  return response.data;
};

// Create query string from filters
const createQueryString = (filters: IocFilters): string => {
  const params = new URLSearchParams();
  
  // Add type filters if any are selected
  const selectedTypes = Object.entries(filters.types)
    .filter(([_, isSelected]) => isSelected)
    .map(([type]) => type);
  
  if (selectedTypes.length > 0) {
    params.append('types', selectedTypes.join(','));
  }
  
  // Add severity filters if any are selected
  const selectedSeverities = Object.entries(filters.severities)
    .filter(([_, isSelected]) => isSelected)
    .map(([severity]) => severity);
  
  if (selectedSeverities.length > 0) {
    params.append('severities', selectedSeverities.join(','));
  }
  
  // Add confidence range if not default
  const [minConfidence, maxConfidence] = filters.confidenceRange;
  if (minConfidence > 0) {
    params.append('minConfidence', minConfidence.toString());
  }
  if (maxConfidence < 100) {
    params.append('maxConfidence', maxConfidence.toString());
  }
  
  const queryString = params.toString();
  return queryString ? `?${queryString}` : '';
};

// Interface for the hook return value
interface UseIocsReturn {
  iocs: IOCData[];
  isLoading: boolean;
  isError: any;
  mutate: () => void;
}

// Main hook function
export function useIocs(filters: IocFilters): UseIocsReturn {
  const queryString = createQueryString(filters);
  const url = `${API_URL}${queryString}`;

  // Mock data for development (remove in production)
  const mockData: IOCData[] = [
    {
      id: "ioc-1",
      value: "malicious-domain.com",
      type: "domain",
      severity: "high",
      confidence: 85,
      timestamp: "2025-05-13T08:30:00Z",
    },
    {
      id: "ioc-2",
      value: "192.168.1.254",
      type: "ip",
      severity: "medium",
      confidence: 72,
      timestamp: "2025-05-13T07:45:00Z",
    },
    {
      id: "ioc-3",
      value: "ransomware.exe",
      type: "file",
      severity: "critical",
      confidence: 98,
      timestamp: "2025-05-13T09:15:00Z",
    },
    // Add more mock data as needed
  ];

  // Enable this for real API calls
  // const { data, error, mutate } = useSWR(url, fetcher);
  
  // Using mock data for development
  const { data, error, mutate } = useSWR(url, () => {
    // Simulate API latency
    return new Promise<IOCData[]>((resolve) => {
      setTimeout(() => {
        // Apply mock filtering based on the filters
        let filteredData = [...mockData];
        
        // Filter by type
        const activeTypes = Object.entries(filters.types)
          .filter(([_, active]) => active)
          .map(([type]) => type);
        
        if (activeTypes.length > 0) {
          filteredData = filteredData.filter(ioc => 
            activeTypes.includes(ioc.type)
          );
        }
        
        // Filter by severity
        const activeSeverities = Object.entries(filters.severities)
          .filter(([_, active]) => active)
          .map(([severity]) => severity);
        
        if (activeSeverities.length > 0) {
          filteredData = filteredData.filter(ioc => 
            activeSeverities.includes(ioc.severity)
          );
        }
        
        // Filter by confidence
        const [minConfidence, maxConfidence] = filters.confidenceRange;
        filteredData = filteredData.filter(ioc => 
          ioc.confidence >= minConfidence && ioc.confidence <= maxConfidence
        );
        
        resolve(filteredData);
      }, 500); // Simulate 500ms delay
    });
  });

  return {
    iocs: data || [],
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}

// Helper for analyzing IOCs
export function analyzeIocs(iocs: IOCData[]) {
  if (!iocs || iocs.length === 0) {
    return {
      total: 0,
      bySeverity: { critical: 0, high: 0, medium: 0, low: 0 },
      byType: { domain: 0, ip: 0, file: 0, url: 0, email: 0 },
      highestConfidence: 0,
      avgConfidence: 0,
      recentCount: 0 // IOCs in last 24h
    };
  }
  
  // Count by severity
  const bySeverity = iocs.reduce((acc, ioc) => {
    acc[ioc.severity] = (acc[ioc.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  // Count by type
  const byType = iocs.reduce((acc, ioc) => {
    acc[ioc.type] = (acc[ioc.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  // Calculate highest confidence
  const highestConfidence = Math.max(...iocs.map(ioc => ioc.confidence));
  
  // Calculate average confidence
  const avgConfidence = Math.round(
    iocs.reduce((sum, ioc) => sum + ioc.confidence, 0) / iocs.length
  );
  
  // Count recent IOCs (last 24 hours)
  const now = new Date();
  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const recentCount = iocs.filter(ioc => 
    new Date(ioc.timestamp) >= oneDayAgo
  ).length;
  
  return {
    total: iocs.length,
    bySeverity,
    byType,
    highestConfidence,
    avgConfidence,
    recentCount
  };
} 