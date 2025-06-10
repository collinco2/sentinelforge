/**
 * 🎨 ThemeDemo Component - Showcase Light/Dark Mode Implementation
 *
 * Demonstrates the comprehensive theme system with visual examples
 * of all major UI components in both light and dark modes.
 */

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { ThemeToggle } from "./ThemeToggle";
import { StatWidget, StatWidgetGrid } from "./dashboard/StatWidget";
import { FeedCard } from "./dashboard/FeedCard";
import { useTheme } from "../hooks/useTheme";
import { 
  Sun, 
  Moon, 
  Monitor, 
  Database, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  Activity,
  Users,
  Settings
} from "lucide-react";

export function ThemeDemo() {
  const { theme, actualTheme } = useTheme();

  const mockThreats = [
    {
      id: 1,
      description: "Suspicious network activity detected",
      source: "Network Monitor",
      ioc_value: "192.168.1.100",
      timestamp: new Date().toISOString(),
      status: "active" as const,
    },
    {
      id: 2,
      description: "Malware signature found",
      source: "Antivirus",
      ioc_value: "malware.exe",
      timestamp: new Date().toISOString(),
      status: "resolved" as const,
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground p-8 space-y-8 transition-colors duration-200">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            🌞 SentinelForge Light Mode Demo
          </h1>
          <p className="text-muted-foreground text-lg">
            Comprehensive theme system with seamless light/dark mode switching
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Current Theme</p>
            <p className="font-semibold text-foreground">
              {theme} ({actualTheme})
            </p>
          </div>
          <ThemeToggle variant="button" showLabel />
        </div>
      </div>

      {/* Theme Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-primary/20">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-primary">
              <Sun className="h-5 w-5" />
              Light Mode
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Clean, bright interface with dark text on light backgrounds.
              Perfect for well-lit environments.
            </p>
            <div className="mt-3 flex items-center gap-2">
              <div className="w-4 h-4 bg-white border-2 border-gray-300 rounded"></div>
              <span className="text-xs text-muted-foreground">White backgrounds</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-primary/20">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-primary">
              <Moon className="h-5 w-5" />
              Dark Mode
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Professional dark interface with light text on dark backgrounds.
              Ideal for low-light environments.
            </p>
            <div className="mt-3 flex items-center gap-2">
              <div className="w-4 h-4 bg-slate-800 border-2 border-slate-600 rounded"></div>
              <span className="text-xs text-muted-foreground">Dark backgrounds</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-primary/20">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-primary">
              <Monitor className="h-5 w-5" />
              System Mode
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Automatically follows your operating system's theme preference.
              Switches between light and dark automatically.
            </p>
            <div className="mt-3 flex items-center gap-2">
              <div className="w-4 h-4 bg-gradient-to-r from-white to-slate-800 border-2 border-gray-400 rounded"></div>
              <span className="text-xs text-muted-foreground">Auto-switching</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Component Showcase */}
      <div className="space-y-8">
        <h2 className="text-2xl font-semibold text-foreground">Component Showcase</h2>

        {/* Buttons */}
        <Card>
          <CardHeader>
            <CardTitle>Buttons & Interactive Elements</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <Button variant="default">Primary Button</Button>
              <Button variant="secondary">Secondary Button</Button>
              <Button variant="outline">Outline Button</Button>
              <Button variant="ghost">Ghost Button</Button>
              <Button variant="destructive">Destructive Button</Button>
            </div>
            <div className="flex flex-wrap gap-3">
              <Badge variant="default">Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Error</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Stats Widgets */}
        <Card>
          <CardHeader>
            <CardTitle>Dashboard Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <StatWidgetGrid columns={4}>
              <StatWidget
                title="Total Threats"
                value={1247}
                description="Last 24 hours"
                icon={Shield}
                iconColor="text-red-500"
                trend={{ value: "+12%", isPositive: false }}
              />
              <StatWidget
                title="Active Feeds"
                value={8}
                description="All operational"
                icon={Database}
                iconColor="text-green-500"
                trend={{ value: "100%", isPositive: true }}
              />
              <StatWidget
                title="Alerts"
                value={23}
                description="Requires attention"
                icon={AlertTriangle}
                iconColor="text-yellow-500"
                trend={{ value: "-5%", isPositive: true }}
              />
              <StatWidget
                title="Users Online"
                value={156}
                description="Active sessions"
                icon={Users}
                iconColor="text-blue-500"
                trend={{ value: "+8%", isPositive: true }}
              />
            </StatWidgetGrid>
          </CardContent>
        </Card>

        {/* Feed Card Example */}
        <Card>
          <CardHeader>
            <CardTitle>Feed Components</CardTitle>
          </CardHeader>
          <CardContent>
            <FeedCard
              title="Recent Threats"
              icon={Activity}
              iconColor="text-orange-500"
              onViewAll={() => console.log("View all threats")}
            >
              <div className="space-y-3">
                {mockThreats.map((threat) => (
                  <div
                    key={threat.id}
                    className="flex items-center justify-between p-3 bg-muted rounded-xl"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-foreground mb-1">
                        {threat.description}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-medium">{threat.source}</span>
                        <span>•</span>
                        <code className="bg-background px-1 py-0.5 rounded text-xs">
                          {threat.ioc_value}
                        </code>
                      </div>
                    </div>
                    <Badge 
                      variant={threat.status === "active" ? "destructive" : "default"}
                      className="ml-3"
                    >
                      {threat.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </FeedCard>
          </CardContent>
        </Card>

        {/* Form Elements */}
        <Card>
          <CardHeader>
            <CardTitle>Form Elements</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">
                  Search Query
                </label>
                <Input 
                  placeholder="Enter search terms..." 
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">
                  Filter Options
                </label>
                <select className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground">
                  <option>All Categories</option>
                  <option>High Priority</option>
                  <option>Medium Priority</option>
                  <option>Low Priority</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Theme Toggle Variants */}
        <Card>
          <CardHeader>
            <CardTitle>Theme Toggle Variants</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Icon Only</p>
                <ThemeToggle variant="icon" />
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Button with Label</p>
                <ThemeToggle variant="button" showLabel />
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Compact</p>
                <ThemeToggle variant="compact" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <div className="text-center py-8 border-t border-border">
        <p className="text-muted-foreground">
          🎨 SentinelForge Light Mode Implementation - Complete Theme System
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          WCAG 2.1 AA Compliant • Responsive Design • Persistent Preferences
        </p>
      </div>
    </div>
  );
}

export default ThemeDemo;
