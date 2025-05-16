import React, { useState } from "react";
import { Button } from "./ui/button";
import { Slider } from "./ui/slider";
import { IOCData } from "./IocTable";

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
  // Local state to track changes before applying
  const [localFilters, setLocalFilters] = useState<IocFilters>(filters);

  // Update local state when a type checkbox changes
  const handleTypeChange = (type: keyof IocFilters["types"]) => {
    setLocalFilters((prev) => ({
      ...prev,
      types: {
        ...prev.types,
        [type]: !prev.types[type],
      },
    }));
  };

  // Update local state when a severity checkbox changes
  const handleSeverityChange = (severity: keyof IocFilters["severities"]) => {
    setLocalFilters((prev) => ({
      ...prev,
      severities: {
        ...prev.severities,
        [severity]: !prev.severities[severity],
      },
    }));
  };

  // Update local state when confidence range changes
  const handleConfidenceChange = (value: number[]) => {
    setLocalFilters((prev) => ({
      ...prev,
      confidenceRange: [value[0], value[1]],
    }));
  };

  // Apply filters
  const handleApplyFilters = () => {
    onFilterChange(localFilters);
  };

  // Clear all filters
  const handleClearFilters = () => {
    const clearedFilters = { ...defaultFilters };
    setLocalFilters(clearedFilters);
    onFilterChange(clearedFilters);
  };

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
            {Object.entries(localFilters.types).map(([type, isChecked]) => (
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
            {Object.entries(localFilters.severities).map(
              ([severity, isChecked]) => (
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
              ),
            )}
          </div>
        </div>

        {/* Confidence Score Filter Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-2">
            Confidence Score: {localFilters.confidenceRange[0]} -{" "}
            {localFilters.confidenceRange[1]}
          </h3>
          <Slider
            className="mt-2"
            min={0}
            max={100}
            step={5}
            value={[
              localFilters.confidenceRange[0],
              localFilters.confidenceRange[1],
            ]}
            onValueChange={handleConfidenceChange}
          />
        </div>

        {/* Action Buttons */}
        <div className="pt-4 space-y-2">
          <Button
            type="button"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            onClick={handleApplyFilters}
          >
            Apply Filters
          </Button>
          <Button
            type="button"
            variant="outline"
            className="w-full border-zinc-700 text-gray-300 hover:bg-zinc-800"
            onClick={handleClearFilters}
          >
            Clear All
          </Button>
        </div>
      </form>
    </aside>
  );
}
