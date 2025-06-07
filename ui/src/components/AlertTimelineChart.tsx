import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import "chart.js/auto";
import { Spinner } from "./ui/spinner";
import { useAlertTimeline, AlertTimelineDataPoint } from "../hooks/useAlertTimeline";

// Register required chart components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
);

interface AlertTimelineChartProps {
  title?: string;
  className?: string;
  height?: number;
  groupBy?: "day" | "hour";
  startDate?: number;
  endDate?: number;
}

export function AlertTimelineChart({
  title = "Alert Activity Timeline",
  className = "",
  height = 400,
  groupBy = "day",
  startDate,
  endDate,
}: AlertTimelineChartProps) {
  // Use the new hook for data fetching
  const { data, loading, error, hasAttemptedFetch } = useAlertTimeline({
    groupBy,
    startDate,
    endDate,
  });

  // Helper function to check if a date is valid
  const isValidDate = (dateString: string | undefined | null): boolean => {
    if (!dateString) return false;

    let date: Date;

    // Handle Unix timestamp
    if (/^\d+$/.test(dateString)) {
      // Ensure we have a reasonable timestamp (after 2020)
      const timestamp = parseInt(dateString);
      // Too small to be milliseconds timestamp, assume seconds
      if (timestamp < 2000000000) {
        date = new Date(timestamp * 1000);
      } else {
        date = new Date(timestamp);
      }
    } else {
      date = new Date(dateString);
    }

    // Basic validation: check if the date is within a reasonable range
    // Reject dates before 2000 or after 2050
    const validTime = date.getTime();
    if (isNaN(validTime)) return false;

    const year2000 = new Date("2000-01-01").getTime();
    const year2050 = new Date("2050-01-01").getTime();

    return validTime >= year2000 && validTime <= year2050;
  };

  // Filter out entries with invalid dates and log them
  const validData = data.filter((item) => {
    const isValid = isValidDate(item.date);
    if (!isValid) {
      console.error("Skipping invalid date entry:", item);
    }
    return isValid;
  });

  // Sort chronologically
  const sortedData = [...validData].sort((a, b) => {
    // Parse dates using the same logic as formatDate
    let dateA: Date, dateB: Date;

    if (/^\d+$/.test(a.date)) {
      const timestampA = parseInt(a.date);
      dateA =
        timestampA < 2000000000
          ? new Date(timestampA * 1000)
          : new Date(timestampA);
    } else {
      dateA = new Date(a.date);
    }

    if (/^\d+$/.test(b.date)) {
      const timestampB = parseInt(b.date);
      dateB =
        timestampB < 2000000000
          ? new Date(timestampB * 1000)
          : new Date(timestampB);
    } else {
      dateB = new Date(b.date);
    }

    return dateA.getTime() - dateB.getTime();
  });

  // Generate fallback data when API fails or returns empty results
  const generateFallbackData = (): AlertTimelineDataPoint[] => {
    const fallbackData: AlertTimelineDataPoint[] = [];
    const today = new Date();

    // Generate 14 days of fake data
    for (let i = 13; i >= 0; i--) {
      const date = new Date();
      date.setDate(today.getDate() - i);

      // Generate some pattern with randomness
      // Weekdays have more alerts than weekends
      const dayOfWeek = date.getDay();
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

      const baseValue = isWeekend ? 5 : 15;
      const randomFactor = 0.5 + Math.random();
      const count = Math.floor(baseValue * randomFactor);

      fallbackData.push({
        date: Math.floor(date.getTime() / 1000).toString(), // Unix timestamp in seconds
        count,
      });
    }

    return fallbackData;
  };

  // Prepare chart data from sorted data
  const chartData = {
    labels: sortedData.map((point) => formatDate(point.date, groupBy)),
    datasets: [
      {
        label: "Alerts",
        data: sortedData.map((point) => point.count || 0), // Ensure count is never undefined or null
        borderColor: "rgba(59, 130, 246, 1)", // blue-500
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.2,
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: "top" as const,
        labels: {
          color: "rgba(156, 163, 175, 1)", // gray-400
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        backgroundColor: "rgba(24, 24, 27, 0.9)", // zinc-900 with opacity
        titleColor: "rgba(255, 255, 255, 0.9)",
        bodyColor: "rgba(255, 255, 255, 0.9)",
        borderColor: "rgba(63, 63, 70, 1)", // zinc-700
        borderWidth: 1,
        padding: 10,
        callbacks: {
          title: (tooltipItems) => {
            const index = tooltipItems[0].dataIndex;
            const dateString = sortedData[index]?.date;
            // Use the same date parsing/formatting logic as in formatDate function
            if (dateString) {
              let date;
              if (/^\d+$/.test(dateString)) {
                const timestamp = parseInt(dateString);
                date =
                  timestamp < 2000000000
                    ? new Date(timestamp * 1000)
                    : new Date(timestamp);
              } else {
                date = new Date(dateString);
              }

              // Handle invalid dates in tooltips
              if (isNaN(date.getTime())) {
                return "Date: Unknown";
              }

              return `Date: ${date.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}`;
            }
            return "Date: Unknown";
          },
          label: (tooltipItem) => {
            const datasetLabel = tooltipItem.dataset.label || "";
            const value =
              tooltipItem.raw !== undefined ? tooltipItem.raw : "N/A";
            return `${datasetLabel}: ${value}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: "rgba(63, 63, 70, 0.3)", // zinc-700 with opacity
        },
        ticks: {
          color: "rgba(156, 163, 175, 1)", // gray-400
          font: {
            size: 10,
          },
          maxRotation: 45,
          minRotation: 45,
        },
        title: {
          display: true,
          text: "Date",
          color: "rgba(156, 163, 175, 1)",
          font: {
            size: 12,
            weight: "normal",
          },
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: "rgba(63, 63, 70, 0.3)", // zinc-700 with opacity
        },
        ticks: {
          color: "rgba(156, 163, 175, 1)", // gray-400
          precision: 0, // Only show integers
          font: {
            size: 11,
          },
        },
        title: {
          display: true,
          text: "Alert Count",
          color: "rgba(156, 163, 175, 1)",
          font: {
            size: 12,
            weight: "normal",
          },
        },
      },
    },
    interaction: {
      mode: "index" as const,
      intersect: false,
    },
    animations: {
      tension: {
        duration: 1000,
        easing: "linear",
        from: 0.2,
        to: 0.2,
      },
    },
  };

  if (loading && !hasAttemptedFetch) {
    return (
      <div className={`${className} flex items-center justify-center py-20`}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} p-6 text-center`}>
        <div className="text-destructive mb-2">Error</div>
        <p className="text-muted-foreground">{error}</p>
      </div>
    );
  }

  // Handle empty data states
  if (sortedData.length === 0) {
    // Case 1: We had data but all entries were filtered out due to invalid dates
    if (data.length > 0) {
      console.warn(
        `All ${data.length} entries were filtered out due to invalid dates`,
      );
      return (
        <div className={className}>
          {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
          <div className="p-6 text-center border border-amber-500/20 rounded-md bg-amber-500/5">
            <div className="text-amber-500 mb-2 font-medium">Warning</div>
            <p className="text-muted-foreground">
              No valid dates found in the data. Check console for details.
            </p>
          </div>
        </div>
      );
    }

    // Case 2: API returned empty results
    if (hasAttemptedFetch) {
      // Show fallback data or empty state message based on configuration
      const useFallbackData = true; // Could be made configurable via props

      if (useFallbackData) {
        const fallbackData = generateFallbackData();
        const fallbackChartData = {
          labels: fallbackData.map((point) => formatDate(point.date, groupBy)),
          datasets: [
            {
              label: "Alerts (Sample Data)",
              data: fallbackData.map((point) => point.count),
              borderColor: "rgba(156, 163, 175, 1)", // gray-400 to indicate fallback
              backgroundColor: "rgba(156, 163, 175, 0.1)",
              borderWidth: 2,
              pointRadius: 3,
              pointHoverRadius: 5,
              borderDash: [5, 5], // Dashed line to indicate fallback data
              tension: 0.2,
            },
          ],
        };

        return (
          <div className={className}>
            {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
            <div className="mb-4 bg-amber-900/20 text-amber-400 p-3 rounded text-sm">
              No actual data available. Showing sample data pattern.
            </div>
            <div style={{ height: `${height}px` }}>
              <Line data={fallbackChartData} options={options} />
            </div>
          </div>
        );
      } else {
        // Clean empty state with a message
        return (
          <div className={className}>
            {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
            <div className="flex flex-col items-center justify-center h-64 border border-gray-200 rounded-md bg-gray-50/50 dark:border-gray-800 dark:bg-gray-900/50">
              <p className="text-muted-foreground mb-2">No data available</p>
              <p className="text-sm text-muted-foreground/70">
                There are no alerts in the selected time period.
              </p>
            </div>
          </div>
        );
      }
    }
  }

  return (
    <div className={className}>
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      <div style={{ height: `${height}px` }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}

// Helper to format dates for display
function formatDate(
  dateString: string | undefined | null,
  groupBy: "day" | "hour",
): string {
  if (!dateString) return "No Date";

  let date: Date;

  try {
    // Check if the date is a UNIX timestamp (numeric string)
    if (/^\d+$/.test(dateString)) {
      // Convert seconds to milliseconds for JavaScript Date if needed
      const timestamp = parseInt(dateString);
      // If timestamp is in seconds (less than year 2033 in seconds), convert to milliseconds
      date =
        timestamp < 2000000000
          ? new Date(timestamp * 1000)
          : new Date(timestamp);
    } else {
      // Handle ISO 8601 date string
      date = new Date(dateString);
    }

    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.error("Invalid date:", dateString);
      return "Invalid Date";
    }

    if (groupBy === "hour") {
      return date.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch (error) {
    console.error("Error formatting date:", error, "for input:", dateString);
    return "Format Error";
  }
}
