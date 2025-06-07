import React, { useState } from "react";
import { AlertTimelineChart } from "../components/AlertTimelineChart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

interface TimePeriod {
  label: string;
  startDate?: number;
  endDate?: number;
}

export function AlertTimelinePage() {
  const [groupBy, setGroupBy] = useState<"day" | "hour">("day");
  const [period, setPeriod] = useState<TimePeriod>({ label: "Last 30 Days" });

  // Pre-defined time periods
  const timePeriods: TimePeriod[] = [
    { label: "Last 30 Days" },
    { label: "Last 7 Days", startDate: Date.now() / 1000 - 7 * 24 * 60 * 60 },
    { label: "Last 24 Hours", startDate: Date.now() / 1000 - 24 * 60 * 60 },
    { label: "Today", startDate: new Date().setHours(0, 0, 0, 0) / 1000 },
  ];

  const handlePeriodChange = (value: string) => {
    const newPeriod =
      timePeriods.find((p) => p.label === value) || timePeriods[0];
    setPeriod(newPeriod);
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Alert Timeline</h1>

        <div className="flex flex-col sm:flex-row gap-3">
          <div>
            <Select value={period.label} onValueChange={handlePeriodChange}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select period" />
              </SelectTrigger>
              <SelectContent>
                {timePeriods.map((period) => (
                  <SelectItem key={period.label} value={period.label}>
                    {period.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Select
              value={groupBy}
              onValueChange={(value) => setGroupBy(value as "day" | "hour")}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Group by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="day">Group by Day</SelectItem>
                <SelectItem value="hour">Group by Hour</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-lg shadow p-4 md:p-6">
        <AlertTimelineChart
          groupBy={groupBy}
          startDate={period.startDate}
          endDate={period.endDate}
          height={500}
        />
      </div>
    </div>
  );
}
