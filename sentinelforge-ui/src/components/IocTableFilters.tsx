import React from 'react';
import { Filter, ChevronDown, ChevronUp, X } from 'lucide-react';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { Slider } from './ui/slider';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { IOCData } from './IocTable';

// Define the filter state interface
export interface IocFilters {
  types: Record<IOCData['type'], boolean>;
  severities: Record<IOCData['severity'], boolean>;
  confidenceRange: [number, number];
  dateRange: {
    from: string | null;
    to: string | null;
  };
}

// Default filters
export const defaultFilters: IocFilters = {
  types: {
    ip: false,
    domain: false,
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

interface IocTableFiltersProps {
  filters: IocFilters;
  onFiltersChange: (filters: IocFilters) => void;
  onReset: () => void;
  activeFilterCount: number;
}

export function IocTableFilters({
  filters,
  onFiltersChange,
  onReset,
  activeFilterCount,
}: IocTableFiltersProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  // Update type filters
  const handleTypeChange = (type: IOCData['type'], checked: boolean) => {
    onFiltersChange({
      ...filters,
      types: {
        ...filters.types,
        [type]: checked,
      },
    });
  };

  // Update severity filters
  const handleSeverityChange = (severity: IOCData['severity'], checked: boolean) => {
    onFiltersChange({
      ...filters,
      severities: {
        ...filters.severities,
        [severity]: checked,
      },
    });
  };

  // Update confidence range
  const handleConfidenceChange = (values: number[]) => {
    onFiltersChange({
      ...filters,
      confidenceRange: [values[0], values[1]],
    });
  };

  const todayDate = new Date().toISOString().split('T')[0];
  const lastMonthDate = new Date(
    new Date().setMonth(new Date().getMonth() - 1)
  ).toISOString().split('T')[0];

  // Update date range
  const handleDateChange = (field: 'from' | 'to', value: string) => {
    onFiltersChange({
      ...filters,
      dateRange: {
        ...filters.dateRange,
        [field]: value || null,
      },
    });
  };

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700"
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
                {activeFilterCount > 0 && (
                  <span className="ml-2 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {activeFilterCount}
                  </span>
                )}
                {isOpen ? (
                  <ChevronUp className="h-4 w-4 ml-2" />
                ) : (
                  <ChevronDown className="h-4 w-4 ml-2" />
                )}
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-2">
              <div className="bg-zinc-800 border border-zinc-700 rounded-md p-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* IOC Type Filters */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-300 mb-2">IOC Type</h3>
                    <div className="space-y-2">
                      {Object.keys(filters.types).map((type) => (
                        <div key={type} className="flex items-center space-x-2">
                          <Checkbox
                            id={`type-${type}`}
                            checked={filters.types[type as IOCData['type']]}
                            onCheckedChange={(checked) =>
                              handleTypeChange(type as IOCData['type'], checked === true)
                            }
                          />
                          <label
                            htmlFor={`type-${type}`}
                            className="text-sm text-gray-300 capitalize"
                          >
                            {type}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Severity Filters */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-300 mb-2">Severity</h3>
                    <div className="space-y-2">
                      {Object.keys(filters.severities).map((severity) => (
                        <div key={severity} className="flex items-center space-x-2">
                          <Checkbox
                            id={`severity-${severity}`}
                            checked={filters.severities[severity as IOCData['severity']]}
                            onCheckedChange={(checked) =>
                              handleSeverityChange(severity as IOCData['severity'], checked === true)
                            }
                          />
                          <label
                            htmlFor={`severity-${severity}`}
                            className="text-sm text-gray-300 capitalize"
                          >
                            {severity}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Confidence Range */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-300 mb-2">
                      Confidence ({filters.confidenceRange[0]}% - {filters.confidenceRange[1]}%)
                    </h3>
                    <div className="px-2 py-4">
                      <Slider
                        defaultValue={[filters.confidenceRange[0], filters.confidenceRange[1]]}
                        min={0}
                        max={100}
                        step={5}
                        onValueChange={handleConfidenceChange}
                      />
                    </div>
                  </div>

                  {/* Date Range */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-300 mb-2">Date Range</h3>
                    <div className="space-y-2">
                      <div className="space-y-1">
                        <label className="text-xs text-gray-400">From</label>
                        <input
                          type="date"
                          value={filters.dateRange.from || lastMonthDate}
                          onChange={(e) => handleDateChange('from', e.target.value)}
                          className="w-full bg-zinc-700 border border-zinc-600 rounded-md px-3 py-1 text-sm text-gray-300"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs text-gray-400">To</label>
                        <input
                          type="date"
                          value={filters.dateRange.to || todayDate}
                          onChange={(e) => handleDateChange('to', e.target.value)}
                          className="w-full bg-zinc-700 border border-zinc-600 rounded-md px-3 py-1 text-sm text-gray-300"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>

          {activeFilterCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onReset}
              className="text-gray-400 hover:text-gray-300"
            >
              <X className="h-4 w-4 mr-1" />
              Clear filters
            </Button>
          )}
        </div>
      </div>
    </div>
  );
} 