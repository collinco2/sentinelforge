/**
 * Button Accessibility Test Component
 * Demonstrates WCAG 2.1 compliant button styles with enhanced contrast ratios
 */

import React, { useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import {
  Upload,
  Download,
  RefreshCw,
  Trash2,
  Settings,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Info,
  Plus,
  Minus,
  Edit,
  Save,
  X,
} from "lucide-react";

export const ButtonAccessibilityTest: React.FC = () => {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [isLoading, setIsLoading] = useState(false);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);

    // Apply theme to document
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const handleLoadingTest = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 2000);
  };

  return (
    <div className="p-8 space-y-8 bg-background text-foreground min-h-screen">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Button Accessibility Test</h1>
        <Button onClick={toggleTheme} variant="outline">
          {theme === "light" ? (
            <EyeOff className="h-4 w-4 mr-2" />
          ) : (
            <Eye className="h-4 w-4 mr-2" />
          )}
          {theme === "light" ? "Dark Mode" : "Light Mode"}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Primary Buttons */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Primary Buttons (Default)
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              High contrast background with white text. Meets WCAG AA standards.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button>Default Primary</Button>
              <Button size="sm">Small Primary</Button>
              <Button size="lg">Large Primary</Button>
              <Button size="icon" aria-label="Add new item">
                <Plus className="h-4 w-4" />
                <span className="sr-only">Add new item</span>
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button disabled>Disabled Primary</Button>
              <Button className="bg-green-600 hover:bg-green-700">
                <CheckCircle className="h-4 w-4 mr-2" />
                Success Action
              </Button>
              <Button onClick={handleLoadingTest} disabled={isLoading}>
                {isLoading ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4 mr-2" />
                )}
                {isLoading ? "Uploading..." : "Upload File"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Secondary Buttons */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5 text-blue-600" />
              Secondary Buttons
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Enhanced contrast with darker background and improved text
              visibility.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary">Secondary</Button>
              <Button variant="secondary" size="sm">
                Small Secondary
              </Button>
              <Button variant="secondary" size="lg">
                Large Secondary
              </Button>
              <Button variant="secondary" size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" disabled>
                Disabled Secondary
              </Button>
              <Button variant="secondary">
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </Button>
              <Button variant="secondary">
                <Edit className="h-4 w-4 mr-2" />
                Edit Settings
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Outline Buttons */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              Outline Buttons
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Enhanced with thicker borders and better contrast ratios for
              visibility.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="outline">Outline</Button>
              <Button variant="outline" size="sm">
                Small Outline
              </Button>
              <Button variant="outline" size="lg">
                Large Outline
              </Button>
              <Button variant="outline" size="icon" aria-label="Remove item">
                <Minus className="h-4 w-4" />
                <span className="sr-only">Remove item</span>
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" disabled>
                Disabled Outline
              </Button>
              <Button variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Data
              </Button>
              <Button
                variant="outline"
                className="text-red-600 border-red-600 hover:bg-red-50 hover:text-red-700"
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Ghost Buttons */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5 text-purple-600" />
              Ghost Buttons
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Enhanced with default text color for better visibility in resting
              state.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="ghost">Ghost</Button>
              <Button variant="ghost" size="sm">
                Small Ghost
              </Button>
              <Button variant="ghost" size="lg">
                Large Ghost
              </Button>
              <Button variant="ghost" size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="ghost" disabled>
                Disabled Ghost
              </Button>
              <Button variant="ghost">
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </Button>
              <Button variant="ghost">
                <Save className="h-4 w-4 mr-2" />
                Save Draft
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Destructive Buttons */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              Destructive Buttons
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              High contrast red background for critical actions with clear
              visibility.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="destructive">Delete</Button>
              <Button variant="destructive" size="sm">
                Small Delete
              </Button>
              <Button variant="destructive" size="lg">
                Large Delete
              </Button>
              <Button
                variant="destructive"
                size="icon"
                aria-label="Delete item"
              >
                <Trash2 className="h-4 w-4" />
                <span className="sr-only">Delete item</span>
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="destructive" disabled>
                Disabled Delete
              </Button>
              <Button variant="destructive">
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Account
              </Button>
              <Button variant="destructive">
                <X className="h-4 w-4 mr-2" />
                Remove Access
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Link Buttons */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5 text-blue-600" />
              Link Buttons
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Maintains primary color for good contrast and clear link
              indication.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="link">Link Button</Button>
              <Button variant="link" size="sm">
                Small Link
              </Button>
              <Button variant="link" size="lg">
                Large Link
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="link" disabled>
                Disabled Link
              </Button>
              <Button variant="link">Learn More</Button>
              <Button variant="link">View Documentation</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Accessibility Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            WCAG 2.1 Compliance Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Badge variant="default" className="mb-2">
                Contrast Ratios
              </Badge>
              <ul className="text-sm space-y-1">
                <li>✅ Primary buttons: 4.5:1+ contrast</li>
                <li>✅ Secondary buttons: Enhanced background</li>
                <li>✅ Outline buttons: Thicker borders (2px)</li>
                <li>✅ Ghost buttons: Default text color</li>
              </ul>
            </div>
            <div className="space-y-2">
              <Badge variant="secondary" className="mb-2">
                Focus States
              </Badge>
              <ul className="text-sm space-y-1">
                <li>✅ Visible focus rings</li>
                <li>✅ 2px ring width</li>
                <li>✅ High contrast ring colors</li>
                <li>✅ Ring offset for clarity</li>
              </ul>
            </div>
            <div className="space-y-2">
              <Badge variant="outline" className="mb-2">
                Interactive States
              </Badge>
              <ul className="text-sm space-y-1">
                <li>✅ Clear hover feedback</li>
                <li>✅ Active state indication</li>
                <li>✅ Disabled state clarity</li>
                <li>✅ Loading state feedback</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ButtonAccessibilityTest;
