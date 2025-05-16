import React from 'react';
import { render } from '@testing-library/react';
import { screen } from '@testing-library/dom';
import { describe, it, expect } from 'vitest';
import { StatCard } from './StatCard';
import { ShieldAlert } from 'lucide-react';

describe('StatCard', () => {
  it('renders correctly with required props', () => {
    render(
      <StatCard
        title="Test Title"
        value="100"
        icon={ShieldAlert}
      />
    );
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });
  
  it('shows loading state when isLoading is true', () => {
    render(
      <StatCard
        title="Test Title"
        value="100"
        icon={ShieldAlert}
        isLoading={true}
      />
    );
    
    // Should show placeholder instead of value
    expect(screen.queryByText('100')).not.toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
  });
  
  it('renders with different variants', () => {
    const { rerender } = render(
      <StatCard
        title="Critical"
        value="5"
        icon={ShieldAlert}
        variant="critical"
      />
    );
    
    expect(screen.getByText('Critical')).toBeInTheDocument();
    
    rerender(
      <StatCard
        title="Warning"
        value="10"
        icon={ShieldAlert}
        variant="warning"
      />
    );
    
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });
  
  it('shows change indicators when provided', () => {
    render(
      <StatCard
        title="With Change"
        value="200"
        icon={ShieldAlert}
        change={15}
        changePeriod="vs last week"
      />
    );
    
    expect(screen.getByText('15%')).toBeInTheDocument();
    expect(screen.getByText('vs last week')).toBeInTheDocument();
  });
}); 