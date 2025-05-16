import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { screen } from '@testing-library/dom';
import { describe, it, expect, vi } from 'vitest';
import { FilterSidebar, defaultFilters } from './FilterSidebar';

describe('FilterSidebar', () => {
  it('renders with default filters', () => {
    render(
      <FilterSidebar 
        filters={defaultFilters} 
        onFilterChange={() => {}} 
      />
    );
    
    expect(screen.getByText('Filters')).toBeInTheDocument();
    expect(screen.getByText('IOC Type')).toBeInTheDocument();
    expect(screen.getByText('Severity')).toBeInTheDocument();
    expect(screen.getByText(/Confidence Score/)).toBeInTheDocument();
  });
  
  it('shows filter values based on prop', () => {
    const customFilters = {
      ...defaultFilters,
      types: {
        ...defaultFilters.types,
        domain: true
      }
    };
    
    render(
      <FilterSidebar 
        filters={customFilters} 
        onFilterChange={() => {}} 
      />
    );
    
    // Domain checkbox should be checked
    const domainCheckbox = screen.getByLabelText('domain', { exact: false });
    expect(domainCheckbox).toBeChecked();
    
    // Other checkboxes should not be checked
    const ipCheckbox = screen.getByLabelText('ip', { exact: false });
    expect(ipCheckbox).not.toBeChecked();
  });
  
  it('calls onFilterChange when "Apply Filters" is clicked', () => {
    const handleFilterChange = vi.fn();
    
    render(
      <FilterSidebar 
        filters={defaultFilters} 
        onFilterChange={handleFilterChange} 
      />
    );
    
    // Click on a checkbox to change a filter
    const domainCheckbox = screen.getByLabelText('domain', { exact: false });
    fireEvent.click(domainCheckbox);
    
    // Apply the filters
    const applyButton = screen.getByText('Apply Filters');
    fireEvent.click(applyButton);
    
    // onFilterChange should be called once
    expect(handleFilterChange).toHaveBeenCalledTimes(1);
    
    // The first argument should contain the updated filters
    const updatedFilters = handleFilterChange.mock.calls[0][0];
    expect(updatedFilters.types.domain).toBe(true);
  });
  
  it('resets filters when "Clear All" is clicked', () => {
    const handleFilterChange = vi.fn();
    const customFilters = {
      ...defaultFilters,
      types: {
        ...defaultFilters.types,
        domain: true
      },
      severities: {
        ...defaultFilters.severities,
        high: true
      }
    };
    
    render(
      <FilterSidebar 
        filters={customFilters} 
        onFilterChange={handleFilterChange} 
      />
    );
    
    // Click the "Clear All" button
    const clearButton = screen.getByText('Clear All');
    fireEvent.click(clearButton);
    
    // handleFilterChange should be called with default filters
    expect(handleFilterChange).toHaveBeenCalledTimes(1);
    
    // The first argument should be the default filters
    const resetFilters = handleFilterChange.mock.calls[0][0];
    expect(resetFilters).toEqual(defaultFilters);
  });
}); 