import React, { useState, useEffect } from "react";
import { DashboardLayout } from "../layout/DashboardLayout";
import { PageTransition } from "../components/PageTransition";
import {
  DashboardContainer,
  DashboardSection,
  DashboardMetrics,
  StatWidget,
  FeedCard,
} from "../components/dashboard";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Shield,
  Activity,
  AlertTriangle,
  Clock,
  Database,
  TrendingUp,
  Eye,
  AlertCircle,
  RefreshCw,
  Filter,
  Download,
  BarChart3,
  Globe,
  Zap,
} from "lucide-react";

interface ThreatEvent {
  id: string;
  timestamp: string;
  type:
    | "malware"
    | "phishing"
    | "suspicious_ip"
    | "c2_domain"
    | "data_exfiltration";
  severity: "critical" | "high" | "medium" | "low";
  source: string;
  description: string;
  ioc_value: string;
  status: "active" | "investigating" | "resolved" | "false_positive";
}

interface ThreatMetrics {
  total_threats: number;
  active_threats: number;
  critical_threats: number;
  resolved_today: number;
  avg_response_time: string;
  threat_trend: { value: string; isPositive: boolean };
}

export function ThreatMonitorPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [threatMetrics, setThreatMetrics] = useState<ThreatMetrics | null>(
    null,
  );
  const [recentThreats, setRecentThreats] = useState<ThreatEvent[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch threat monitoring data
  useEffect(() => {
    fetchThreatData();
  }, []);

  const fetchThreatData = async () => {
    try {
      setError(null);

      // Simulate API calls for threat monitoring data
      // In a real implementation, these would be actual API endpoints
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Mock threat metrics
      setThreatMetrics({
        total_threats: 1247,
        active_threats: 23,
        critical_threats: 5,
        resolved_today: 18,
        avg_response_time: "12.5 min",
        threat_trend: { value: "-8.2%", isPositive: true },
      });

      // Mock recent threat events
      setRecentThreats([
        {
          id: "1",
          timestamp: new Date(Date.now() - 300000).toISOString(),
          type: "malware",
          severity: "critical",
          source: "EDR Alert",
          description: "Suspicious executable detected on endpoint",
          ioc_value: "malicious.exe",
          status: "investigating",
        },
        {
          id: "2",
          timestamp: new Date(Date.now() - 600000).toISOString(),
          type: "phishing",
          severity: "high",
          source: "Email Security",
          description: "Phishing email with malicious attachment",
          ioc_value: "phishing@evil.com",
          status: "active",
        },
        {
          id: "3",
          timestamp: new Date(Date.now() - 900000).toISOString(),
          type: "suspicious_ip",
          severity: "medium",
          source: "Network Monitor",
          description: "Unusual traffic pattern detected",
          ioc_value: "192.168.1.100",
          status: "resolved",
        },
      ]);
    } catch (err) {
      setError("Failed to load threat monitoring data");
      console.error("Error fetching threat data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchThreatData();
    setRefreshing(false);
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "text-red-600 dark:text-red-400";
      case "high":
        return "text-orange-600 dark:text-orange-400";
      case "medium":
        return "text-yellow-600 dark:text-yellow-400";
      case "low":
        return "text-blue-600 dark:text-blue-400";
      default:
        return "text-muted-foreground";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400";
      case "investigating":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400";
      case "resolved":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400";
      case "false_positive":
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout title="Threat Monitor">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Threat Monitor">
      <PageTransition>
        <DashboardContainer>
          {/* Header Section */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground dark:text-foreground">
                Threat Monitor
              </h1>
              <p className="text-lg text-muted-foreground dark:text-muted-foreground">
                Real-time threat detection and monitoring dashboard
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center gap-2"
              >
                <RefreshCw
                  className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <Filter className="h-4 w-4" />
                Filter
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Export
              </Button>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20 transition-colors duration-200 mb-6">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              <AlertDescription className="text-red-800 dark:text-red-200">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Metrics Grid */}
          {threatMetrics && (
            <DashboardMetrics columns={4} className="mb-6">
              <StatWidget
                title="Total Threats"
                value={threatMetrics.total_threats}
                description="All time"
                icon={Shield}
                iconColor="text-blue-600 dark:text-blue-400"
              />

              <StatWidget
                title="Active Threats"
                value={threatMetrics.active_threats}
                description="Requiring attention"
                icon={AlertTriangle}
                iconColor="text-red-600 dark:text-red-400"
              />

              <StatWidget
                title="Critical Threats"
                value={threatMetrics.critical_threats}
                description="High priority"
                icon={Zap}
                iconColor="text-orange-600 dark:text-orange-400"
              />

              <StatWidget
                title="Avg Response Time"
                value={threatMetrics.avg_response_time}
                description="Last 30 days"
                icon={Clock}
                iconColor="text-green-600 dark:text-green-400"
                trend={threatMetrics.threat_trend}
              />
            </DashboardMetrics>
          )}

          {/* Main Content Grid */}
          <DashboardSection columns={2}>
            {/* Recent Threat Events */}
            <FeedCard
              title="Recent Threat Events"
              icon={Activity}
              iconColor="text-red-600 dark:text-red-400"
              emptyState={{
                icon: Activity,
                message: "No recent threat events",
              }}
            >
              <div className="space-y-3">
                {recentThreats.map((threat) => (
                  <div
                    key={threat.id}
                    className="flex items-start justify-between p-3 bg-muted/30 dark:bg-muted/30 rounded-xl border border-border/50 dark:border-border/50 transition-colors duration-200 hover:bg-muted/50 dark:hover:bg-muted/50 cursor-pointer"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className={`font-medium text-sm ${getSeverityColor(threat.severity)}`}
                        >
                          {threat.severity.toUpperCase()}
                        </span>
                        <Badge
                          className={`text-xs ${getStatusColor(threat.status)}`}
                        >
                          {threat.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium text-foreground mb-1">
                        {threat.description}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-medium">{threat.source}</span>
                        <span>•</span>
                        <code className="bg-muted px-1 py-0.5 rounded text-xs text-foreground">
                          {threat.ioc_value}
                        </code>
                        <span>•</span>
                        <span>{formatTimeAgo(threat.timestamp)}</span>
                      </div>
                    </div>
                    <Eye className="h-4 w-4 text-muted-foreground ml-2 flex-shrink-0" />
                  </div>
                ))}
              </div>
            </FeedCard>

            {/* Threat Analytics */}
            <FeedCard
              title="Threat Analytics"
              icon={TrendingUp}
              iconColor="text-purple-600 dark:text-purple-400"
            >
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <BarChart3 className="h-16 w-16 mx-auto mb-4 opacity-50 text-muted-foreground" />
                  <p className="text-sm font-medium text-foreground">
                    Threat analytics visualization
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Real-time threat pattern analysis
                  </p>
                </div>
              </div>
            </FeedCard>
          </DashboardSection>

          {/* Additional Monitoring Sections */}
          <DashboardSection columns={2} className="mt-6">
            {/* Global Threat Intelligence */}
            <FeedCard
              title="Global Threat Intelligence"
              icon={Globe}
              iconColor="text-indigo-600 dark:text-indigo-400"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-muted rounded-xl">
                  <span className="text-sm font-medium text-foreground">Active Campaigns</span>
                  <Badge variant="outline">12</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-muted rounded-xl">
                  <span className="text-sm font-medium text-foreground">New IOCs Today</span>
                  <Badge variant="outline">47</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-muted rounded-xl">
                  <span className="text-sm font-medium text-foreground">Feed Updates</span>
                  <Badge variant="outline">8</Badge>
                </div>
              </div>
            </FeedCard>

            {/* System Health */}
            <FeedCard
              title="Monitoring System Health"
              icon={Database}
              iconColor="text-green-600 dark:text-green-400"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-muted rounded-xl">
                  <span className="text-sm font-medium text-foreground">Detection Engines</span>
                  <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                    Online
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-muted rounded-xl">
                  <span className="text-sm font-medium text-foreground">Data Ingestion</span>
                  <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                    Active
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-muted rounded-xl">
                  <span className="text-sm font-medium text-foreground">Alert Processing</span>
                  <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
                    Delayed
                  </Badge>
                </div>
              </div>
            </FeedCard>
          </DashboardSection>
        </DashboardContainer>
      </PageTransition>
    </DashboardLayout>
  );
}
