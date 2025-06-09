import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { Switch } from "./ui/switch";
import {
  Moon,
  Sun,
  Monitor,
  CheckCircle,
  AlertCircle,
  XCircle,
  Upload,
  Download,
  Settings,
  Shield,
} from "lucide-react";

export const DarkModeTest: React.FC = () => {
  const [currentTheme, setCurrentTheme] = useState<"light" | "dark" | "system">(
    "system",
  );

  useEffect(() => {
    // Get current theme from localStorage
    const savedTheme = localStorage.getItem("ui-preferences");
    if (savedTheme) {
      try {
        const preferences = JSON.parse(savedTheme);
        setCurrentTheme(preferences.theme || "system");
      } catch (error) {
        console.warn("Failed to parse saved theme preferences:", error);
      }
    }
  }, []);

  const applyTheme = (theme: "light" | "dark" | "system") => {
    const root = document.documentElement;
    root.classList.remove("dark");

    if (theme === "dark") {
      root.classList.add("dark");
    } else if (theme === "light") {
      // Light mode is default, no class needed
    } else {
      // System theme
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      if (prefersDark) {
        root.classList.add("dark");
      }
    }

    // Save to localStorage
    const preferences = { theme };
    localStorage.setItem("ui-preferences", JSON.stringify(preferences));
    setCurrentTheme(theme);
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-8 space-y-8 transition-colors duration-200">
      {/* Theme Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Dark Mode Test & Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Button
              variant={currentTheme === "light" ? "default" : "outline"}
              onClick={() => applyTheme("light")}
              className="flex items-center gap-2"
            >
              <Sun className="h-4 w-4" />
              Light
            </Button>
            <Button
              variant={currentTheme === "dark" ? "default" : "outline"}
              onClick={() => applyTheme("dark")}
              className="flex items-center gap-2"
            >
              <Moon className="h-4 w-4" />
              Dark
            </Button>
            <Button
              variant={currentTheme === "system" ? "default" : "outline"}
              onClick={() => applyTheme("system")}
              className="flex items-center gap-2"
            >
              <Monitor className="h-4 w-4" />
              System
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Current theme: <span className="font-medium">{currentTheme}</span>
          </p>
        </CardContent>
      </Card>

      {/* Color Palette Test */}
      <Card>
        <CardHeader>
          <CardTitle>Color Palette Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <div className="h-16 bg-background border border-border rounded-lg flex items-center justify-center">
                <span className="text-foreground text-sm">Background</span>
              </div>
              <p className="text-xs text-muted-foreground">bg-background</p>
            </div>
            <div className="space-y-2">
              <div className="h-16 bg-card border border-border rounded-lg flex items-center justify-center">
                <span className="text-card-foreground text-sm">Card</span>
              </div>
              <p className="text-xs text-muted-foreground">bg-card</p>
            </div>
            <div className="space-y-2">
              <div className="h-16 bg-muted border border-border rounded-lg flex items-center justify-center">
                <span className="text-muted-foreground text-sm">Muted</span>
              </div>
              <p className="text-xs text-muted-foreground">bg-muted</p>
            </div>
            <div className="space-y-2">
              <div className="h-16 bg-accent border border-border rounded-lg flex items-center justify-center">
                <span className="text-accent-foreground text-sm">Accent</span>
              </div>
              <p className="text-xs text-muted-foreground">bg-accent</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Button Variants Test */}
      <Card>
        <CardHeader>
          <CardTitle>Button Variants</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button variant="default">Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="link">Link</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button disabled>Disabled</Button>
            <Button variant="outline" disabled>
              Disabled Outline
            </Button>
            <Button variant="ghost" disabled>
              Disabled Ghost
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Status Indicators */}
      <Card>
        <CardHeader>
          <CardTitle>Status Indicators</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="default">Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge variant="destructive">Destructive</Badge>
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
              <span className="text-sm">Success</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
              <span className="text-sm">Warning</span>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-destructive" />
              <span className="text-sm">Error</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Form Elements */}
      <Card>
        <CardHeader>
          <CardTitle>Form Elements</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="test-input">Test Input</Label>
            <Input id="test-input" placeholder="Enter some text..." />
          </div>
          <div className="flex items-center space-x-2">
            <Switch id="test-switch" />
            <Label htmlFor="test-switch">Test Switch</Label>
          </div>
        </CardContent>
        <CardFooter>
          <Button>Save Changes</Button>
        </CardFooter>
      </Card>

      {/* Alerts */}
      <div className="space-y-4">
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            This is a default alert with proper dark mode support.
          </AlertDescription>
        </Alert>
        <Alert className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20">
          <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            This is a success alert with dark mode colors.
          </AlertDescription>
        </Alert>
        <Alert className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
          <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
          <AlertDescription className="text-red-800 dark:text-red-200">
            This is an error alert with dark mode colors.
          </AlertDescription>
        </Alert>
      </div>

      {/* Action Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Action Buttons</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Download
            </Button>
            <Button variant="destructive" className="flex items-center gap-2">
              <XCircle className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Text Hierarchy */}
      <Card>
        <CardHeader>
          <CardTitle>Text Hierarchy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <h1 className="text-4xl font-bold text-foreground">Heading 1</h1>
          <h2 className="text-3xl font-semibold text-foreground">Heading 2</h2>
          <h3 className="text-2xl font-medium text-foreground">Heading 3</h3>
          <p className="text-foreground">
            This is regular body text that should be clearly readable in both
            light and dark modes.
          </p>
          <p className="text-muted-foreground">
            This is muted text that provides secondary information with
            appropriate contrast.
          </p>
          <p className="text-sm text-muted-foreground">
            This is small muted text for captions and metadata.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default DarkModeTest;
