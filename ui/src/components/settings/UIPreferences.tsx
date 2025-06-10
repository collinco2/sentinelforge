import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { Palette, Monitor, Layout } from "lucide-react";
import { toast } from "../../lib/toast";
import { useTheme } from "../../hooks/useTheme";

interface UIPreferencesType {
  tableDensity: "compact" | "comfortable";
  defaultLandingPage: string;
}

const defaultPreferences: UIPreferencesType = {
  tableDensity: "comfortable",
  defaultLandingPage: "/dashboard",
};

export const UIPreferences: React.FC = () => {
  const { theme, setTheme, actualTheme } = useTheme();
  const [preferences, setPreferences] =
    useState<UIPreferencesType>(defaultPreferences);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = () => {
    try {
      const saved = localStorage.getItem("ui_preferences");
      if (saved) {
        const parsed = JSON.parse(saved);
        setPreferences({ ...defaultPreferences, ...parsed });
      }
    } catch (error) {
      console.error("Error loading UI preferences:", error);
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = (newPreferences: UIPreferencesType) => {
    try {
      localStorage.setItem("ui_preferences", JSON.stringify(newPreferences));
      setPreferences(newPreferences);

      toast.success("UI preferences saved");
    } catch (error) {
      console.error("Error saving UI preferences:", error);
      toast.error("Failed to save preferences");
    }
  };

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme as "light" | "dark" | "system");
  };

  const handleTableDensityChange = (density: string) => {
    const newPreferences = {
      ...preferences,
      tableDensity: density as UIPreferencesType["tableDensity"],
    };
    savePreferences(newPreferences);
  };

  const handleLandingPageChange = (page: string) => {
    const newPreferences = { ...preferences, defaultLandingPage: page };
    savePreferences(newPreferences);
  };

  if (loading) {
    return (
      <Card data-testid="ui-preferences">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            UI Preferences
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="ui-preferences">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Palette className="h-5 w-5" />
          UI Preferences
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Theme Selection */}
        <div className="space-y-4">
          <Label className="text-sm font-medium flex items-center gap-2">
            <Monitor className="h-4 w-4" />
            Theme
          </Label>
          <RadioGroup
            value={theme}
            onValueChange={handleThemeChange}
            className="grid grid-cols-3 gap-4"
            data-testid="theme-selector"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="light" id="light" />
              <Label htmlFor="light" className="text-sm">
                Light
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="dark" id="dark" />
              <Label htmlFor="dark" className="text-sm">
                Dark
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="system" id="system" />
              <Label htmlFor="system" className="text-sm">
                System
              </Label>
            </div>
          </RadioGroup>
          <p className="text-xs text-gray-500">
            Choose your preferred color scheme. System will match your device
            settings.
          </p>
        </div>

        {/* Table Density */}
        <div className="space-y-4">
          <Label className="text-sm font-medium flex items-center gap-2">
            <Layout className="h-4 w-4" />
            Table Density
          </Label>
          <RadioGroup
            value={preferences.tableDensity}
            onValueChange={handleTableDensityChange}
            className="grid grid-cols-2 gap-4"
            data-testid="table-density-selector"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="compact" id="compact" />
              <Label htmlFor="compact" className="text-sm">
                Compact
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="comfortable" id="comfortable" />
              <Label htmlFor="comfortable" className="text-sm">
                Comfortable
              </Label>
            </div>
          </RadioGroup>
          <p className="text-xs text-gray-500">
            Adjust the spacing and padding in data tables.
          </p>
        </div>

        {/* Default Landing Page */}
        <div className="space-y-4">
          <Label htmlFor="landing-page" className="text-sm font-medium">
            Default Landing Page
          </Label>
          <Select
            value={preferences.defaultLandingPage}
            onValueChange={handleLandingPageChange}
            data-testid="landing-page-selector"
          >
            <SelectTrigger>
              <SelectValue placeholder="Select default page" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="/dashboard">Dashboard</SelectItem>
              <SelectItem value="/ioc-management">IOC Management</SelectItem>
              <SelectItem value="/feed-management">Feed Management</SelectItem>
              <SelectItem value="/alerts">Alerts</SelectItem>
              <SelectItem value="/reports">Reports</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-500">
            Choose which page to display when you first log in.
          </p>
        </div>

        {/* Preview Section */}
        <div className="pt-6 border-t">
          <div className="space-y-3">
            <Label className="text-sm font-medium">Preview</Label>
            <div className="p-3 border rounded-lg bg-muted/50">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Current Theme:</span>
                  <span className="text-sm font-medium capitalize">
                    {theme} ({actualTheme})
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Table Density:</span>
                  <span className="text-sm font-medium capitalize">
                    {preferences.tableDensity}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Landing Page:</span>
                  <span className="text-sm font-medium">
                    {preferences.defaultLandingPage
                      .replace("/", "")
                      .replace("-", " ") || "Dashboard"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
