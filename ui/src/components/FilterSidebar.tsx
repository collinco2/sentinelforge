import React from "react";
import { Button } from "./ui/button";
import { Slider } from "./ui/slider";

// Define the filter structure
export interface IocFilters {
  types: {
    domain: boolean;
    ip: boolean;
    file: boolean;
    url: boolean;
    email: boolean;
  };
  severities: {
    critical: boolean;
    high: boolean;
    medium: boolean;
    low: boolean;
  };
  confidenceRange: [number, number]; // [min, max]
  dateRange?: {
    from: string | null;
    to: string | null;
  };
}

// Default filters
export const defaultFilters: IocFilters = {
  types: {
    domain: false,
    ip: false,
    file: false,
    url: false,
    email: false,
  },
  severities: {
    critical: false,
    high: false,
    medium: false,
    low: false,
  },
  confidenceRange: [0, 100],
  dateRange: {
    from: null,
    to: null,
  },
};

interface FilterSidebarProps {
  filters: IocFilters;
  onFilterChange: (filters: IocFilters) => void;
  className?: string;
}

export function FilterSidebar({
  filters,
  onFilterChange,
  className = "",
}: FilterSidebarProps) {
  // Update local state when a type checkbox changes
  const handleTypeChange = (type: keyof IocFilters["types"]) => {
    const updatedFilters = {
      ...filters,
      types: {
        ...filters.types,
        [type]: !filters.types[type],
      },
    };
    onFilterChange(updatedFilters);
  };

  // Update local state when a severity checkbox changes
  const handleSeverityChange = (severity: keyof IocFilters["severities"]) => {
    const updatedFilters = {
      ...filters,
      severities: {
        ...filters.severities,
        [severity]: !filters.severities[severity],
      },
    };
    onFilterChange(updatedFilters);
  };

  // Update state when confidence range changes
  const handleConfidenceChange = (value: number[]) => {
    const updatedFilters = {
      ...filters,
      confidenceRange: [value[0], value[1]] as [number, number],
    };
    onFilterChange(updatedFilters);
  };

  // Update state when date range changes
  const handleDateRangeChange = (field: "from" | "to", value: string) => {
    const updatedFilters = {
      ...filters,
      dateRange: {
        from:
          field === "from" ? value || null : filters.dateRange?.from || null,
        to: field === "to" ? value || null : filters.dateRange?.to || null,
      },
    };
    onFilterChange(updatedFilters);
  };

  // Clear all filters
  const handleClearFilters = () => {
    onFilterChange(defaultFilters);
  };

  // Get today's date and the date from 30 days ago in YYYY-MM-DD format
  // Commented out for now as they're not being used
  // const today = new Date().toISOString().split("T")[0];
  // const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  //   .toISOString()
  //   .split("T")[0];

  return (
    <aside
      className={`w-full md:w-64 bg-zinc-900 border-r border-zinc-800 p-4 ${className}`}
    >
      <h2 className="text-lg font-semibold text-gray-200 mb-4">Filters</h2>

      <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
        {/* IOC Type Filter Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-2">IOC Type</h3>
          <div className="space-y-2">
            {Object.entries(filters.types).map(([type, isChecked]) => (
              <label
                key={type}
                className="flex items-center space-x-2 text-gray-300 text-sm cursor-pointer hover:text-gray-100"
              >
                <input
                  type="checkbox"
                  className="rounded bg-zinc-800 border-zinc-700 text-blue-600 focus:ring-blue-600 focus:ring-offset-zinc-900"
                  checked={isChecked}
                  onChange={() =>
                    handleTypeChange(type as keyof IocFilters["types"])
                  }
                />
                <span className="capitalize">{type}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Severity Filter Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-2">Severity</h3>
          <div className="space-y-2">
            {Object.entries(filters.severities).map(([severity, isChecked]) => (
              <label
                key={severity}
                className="flex items-center space-x-2 text-gray-300 text-sm cursor-pointer hover:text-gray-100"
              >
                <input
                  type="checkbox"
                  className="rounded bg-zinc-800 border-zinc-700 text-blue-600 focus:ring-blue-600 focus:ring-offset-zinc-900"
                  checked={isChecked}
                  onChange={() =>
                    handleSeverityChange(
                      severity as keyof IocFilters["severities"],
                    )
                  }
                />
                <span className="capitalize">{severity}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Confidence Score Filter Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-2">
            Confidence Score: {filters.confidenceRange[0]} -{" "}
            {filters.confidenceRange[1]}
          </h3>
          <Slider
            className="mt-2"
            min={0}
            max={100}
            step={5}
            value={[filters.confidenceRange[0], filters.confidenceRange[1]]}
            onValueChange={handleConfidenceChange}
          />
        </div>

        {/* Date Range Filter Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-2">Date Range</h3>
          <div className="space-y-2">
            <div className="space-y-1">
              <label className="block text-xs text-gray-400">From</label>
              <input
                type="date"
                className="w-full rounded bg-zinc-800 border-zinc-700 text-gray-300 focus:ring-blue-600 focus:ring-offset-zinc-900"
                value={filters.dateRange?.from || ""}
                onChange={(e) => handleDateRangeChange("from", e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs text-gray-400">To</label>
              <input
                type="date"
                className="w-full rounded bg-zinc-800 border-zinc-700 text-gray-300 focus:ring-blue-600 focus:ring-offset-zinc-900"
                value={filters.dateRange?.to || ""}
                onChange={(e) => handleDateRangeChange("to", e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Clear Filters Button */}
        <div className="pt-4">
          <Button
            type="button"
            variant="outline"
            className="w-full border-zinc-700 text-gray-300 hover:bg-zinc-800"
            onClick={handleClearFilters}
          >
            Clear All Filters
          </Button>
        </div>
      </form>
    </aside>
  );
}
