import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { screen } from '@testing-library/dom';
import { describe, it, expect, vi } from 'vitest';
import { IocTable, IOCData } from './IocTable';

describe('IocTable', () => {
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
    }
  ];
  
  it('renders loading state when isLoading is true', () => {
    render(<IocTable isLoading={true} />);
    
    expect(screen.getByText('Loading IOC data...')).toBeInTheDocument();
  });
  
  it('renders table with provided data', () => {
    render(<IocTable data={mockData} />);
    
    // Check if IOC values are displayed
    expect(screen.getByText('malicious-domain.com')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.254')).toBeInTheDocument();
    
    // Check if types are displayed
    expect(screen.getByText('domain')).toBeInTheDocument();
    expect(screen.getByText('ip')).toBeInTheDocument();
    
    // Check if severities are displayed
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
  });
  
  it('calls onRowClick when a row is clicked', () => {
    const handleRowClick = vi.fn();
    
    render(
      <IocTable 
        data={mockData} 
        onRowClick={handleRowClick} 
      />
    );
    
    // Find the first row by IOC value and click it
    const firstRow = screen.getByText('malicious-domain.com').closest('tr');
    if (firstRow) {
      fireEvent.click(firstRow);
    }
    
    // Check if handler was called with the correct IOC data
    expect(handleRowClick).toHaveBeenCalledTimes(1);
    expect(handleRowClick).toHaveBeenCalledWith(mockData[0]);
  });
  
  it('renders empty state when no data is available', () => {
    render(<IocTable data={[]} />);
    
    expect(screen.getByText('No IOCs match the current filters')).toBeInTheDocument();
  });
  
  it('renders pagination when there are more items than rows per page', () => {
    // Create more mock data to trigger pagination
    const manyItems: IOCData[] = Array(15).fill(null).map((_, i) => ({
      id: `ioc-${i}`,
      value: `test-ioc-${i}.com`,
      type: "domain",
      severity: "medium",
      confidence: 70,
      timestamp: "2025-05-13T08:30:00Z",
    }));
    
    render(<IocTable data={manyItems} />);
    
    // Check if pagination text is displayed
    expect(screen.getByText(/Showing 1 to 10 of 15 entries/)).toBeInTheDocument();
  });
}); 