import React, { useState, useEffect } from "react";
import {
  X,
  Clock,
  Network,
  File,
  Settings,
  Shield,
  User,
  Loader2,
  AlertCircle,
  Calendar,
  BarChart3,
  List,
} from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
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
} from "chart.js";
import { Line } from "react-chartjs-2";
import "chartjs-adapter-date-fns";

// Register Chart.js components
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

// Timeline event interface
interface TimelineEvent {
  timestamp: string;
  type: string;
  description: string;
}

interface AlertTimelineViewProps {
  alertId: number;
  onClose: () => void;
}

export function AlertTimelineView({
  alertId,
  onClose,
}: AlertTimelineViewProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("timeline");

  // Fetch timeline data
  useEffect(() => {
    const fetchTimeline = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/alert/${alertId}/timeline`);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Alert not found");
          }
          throw new Error(
            `API error: ${response.status} ${response.statusText}`,
          );
        }

        const timelineData = await response.json();
        setEvents(timelineData);
      } catch (err) {
        console.error("Error fetching timeline:", err);
        setError(
          err instanceof Error ? err.message : "Failed to fetch timeline",
        );
        setEvents([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTimeline();
  }, [alertId]);

  // Get icon for event type
  const getEventIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "network":
        return <Network className="h-4 w-4 text-blue-500" />;
      case "file":
        return <File className="h-4 w-4 text-green-500" />;
      case "process":
        return <Settings className="h-4 w-4 text-purple-500" />;
      case "registry":
        return <Shield className="h-4 w-4 text-orange-500" />;
      case "authentication":
        return <User className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  // Get color for event type
  const getEventColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "network":
        return "bg-blue-500";
      case "file":
        return "bg-green-500";
      case "process":
        return "bg-purple-500";
      case "registry":
        return "bg-orange-500";
      case "authentication":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return {
        time: date.toLocaleTimeString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
        date: date.toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
      };
    } catch (e) {
      return { time: timestamp, date: "" };
    }
  };

  // Prepare chart data
  const getChartData = () => {
    const eventTypeColors = {
      network: "#3b82f6",
      file: "#10b981",
      process: "#8b5cf6",
      registry: "#f59e0b",
      authentication: "#ef4444",
    };

    const datasets = Object.keys(eventTypeColors)
      .map((eventType) => {
        const typeEvents = events.filter(
          (event) => event.type.toLowerCase() === eventType,
        );

        return {
          label: eventType.charAt(0).toUpperCase() + eventType.slice(1),
          data: typeEvents.map((event, index) => ({
            x: new Date(event.timestamp),
            y: index + 1,
            description: event.description,
          })),
          borderColor:
            eventTypeColors[eventType as keyof typeof eventTypeColors],
          backgroundColor:
            eventTypeColors[eventType as keyof typeof eventTypeColors] + "20",
          pointBackgroundColor:
            eventTypeColors[eventType as keyof typeof eventTypeColors],
          pointBorderColor: "#ffffff",
          pointBorderWidth: 2,
          pointRadius: 6,
          tension: 0.1,
        };
      })
      .filter((dataset) => dataset.data.length > 0);

    return { datasets };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
      },
      title: {
        display: true,
        text: "Event Timeline",
      },
      tooltip: {
        callbacks: {
          title: (context: any) => {
            return new Date(context[0].parsed.x).toLocaleString();
          },
          label: (context: any) => {
            const dataPoint = context.raw;
            return dataPoint.description;
          },
        },
      },
    },
    scales: {
      x: {
        type: "time" as const,
        time: {
          displayFormats: {
            minute: "HH:mm",
            hour: "HH:mm",
          },
        },
        title: {
          display: true,
          text: "Time",
        },
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "Event Sequence",
        },
        ticks: {
          stepSize: 1,
        },
      },
    },
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
      <div className="bg-background rounded-xl shadow-xl w-[90vw] max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">Alert Timeline</h2>
            <Badge variant="outline" className="ml-2">
              Alert #{alertId}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="mt-4 text-muted-foreground">Loading timeline...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <AlertCircle className="h-8 w-8 text-red-500" />
              <p className="mt-4 text-red-500 font-medium">
                Error loading timeline
              </p>
              <p className="text-sm text-muted-foreground">{error}</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          ) : events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <Clock className="h-8 w-8 text-muted-foreground" />
              <p className="mt-4 text-muted-foreground">
                No timeline events found
              </p>
            </div>
          ) : (
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="flex flex-col h-full"
            >
              <div className="px-6 pt-4">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger
                    value="timeline"
                    className="flex items-center gap-2"
                  >
                    <List className="h-4 w-4" />
                    Timeline View
                  </TabsTrigger>
                  <TabsTrigger
                    value="chart"
                    className="flex items-center gap-2"
                  >
                    <BarChart3 className="h-4 w-4" />
                    Chart View
                  </TabsTrigger>
                </TabsList>
              </div>

              <TabsContent
                value="timeline"
                className="flex-1 overflow-hidden mt-0"
              >
                <div className="p-6 h-full overflow-y-auto">
                  {/* Timeline */}
                  <div className="relative">
                    {/* Vertical line */}
                    <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border"></div>

                    {/* Events */}
                    <div className="space-y-6">
                      {events.map((event, index) => {
                        const { time, date } = formatTimestamp(event.timestamp);

                        return (
                          <div
                            key={index}
                            className="relative flex items-start gap-4"
                          >
                            {/* Timeline dot */}
                            <div
                              className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full ${getEventColor(event.type)} shadow-lg`}
                            >
                              {getEventIcon(event.type)}
                            </div>

                            {/* Event content */}
                            <div className="flex-1 min-w-0">
                              <Card className="shadow-sm">
                                <CardHeader className="pb-2">
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-sm font-medium capitalize">
                                      {event.type} Event
                                    </CardTitle>
                                    <div className="text-right">
                                      <div className="text-sm font-medium">
                                        {time}
                                      </div>
                                      <div className="text-xs text-muted-foreground">
                                        {date}
                                      </div>
                                    </div>
                                  </div>
                                </CardHeader>
                                <CardContent className="pt-0">
                                  <p className="text-sm text-foreground">
                                    {event.description}
                                  </p>
                                </CardContent>
                              </Card>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent
                value="chart"
                className="flex-1 overflow-hidden mt-0"
              >
                <div className="p-6 h-full">
                  <div className="h-full">
                    <Line data={getChartData()} options={chartOptions} />
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t border-border">
          <div className="text-sm text-muted-foreground">
            {events.length > 0 && `${events.length} events in timeline`}
          </div>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
