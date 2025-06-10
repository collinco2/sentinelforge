import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { Bell, Mail, MessageSquare, Calendar } from "lucide-react";
import { toast } from "../../lib/toast";

interface NotificationPreferences {
  emailAlerts: boolean;
  slackNotifications: boolean;
  weeklySummary: boolean;
}

const defaultPreferences: NotificationPreferences = {
  emailAlerts: true,
  slackNotifications: false,
  weeklySummary: true,
};

export const NotificationSettings: React.FC = () => {
  const [preferences, setPreferences] =
    useState<NotificationPreferences>(defaultPreferences);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await fetch("/api/user/preferences", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences({
          emailAlerts: data.email_alerts ?? defaultPreferences.emailAlerts,
          slackNotifications:
            data.slack_notifications ?? defaultPreferences.slackNotifications,
          weeklySummary:
            data.weekly_summary ?? defaultPreferences.weeklySummary,
        });
      } else {
        // Fallback to localStorage if API fails
        const saved = localStorage.getItem("notification_preferences");
        if (saved) {
          const parsed = JSON.parse(saved);
          setPreferences({ ...defaultPreferences, ...parsed });
        }
      }
    } catch (error) {
      console.error("Error loading notification preferences:", error);
      // Fallback to localStorage
      try {
        const saved = localStorage.getItem("notification_preferences");
        if (saved) {
          const parsed = JSON.parse(saved);
          setPreferences({ ...defaultPreferences, ...parsed });
        }
      } catch (localError) {
        console.error("Error loading from localStorage:", localError);
      }
    } finally {
      setLoading(false);
    }
  };

  const savePreference = async (
    key: keyof NotificationPreferences,
    value: boolean,
  ) => {
    setSaving(key);
    const newPreferences = { ...preferences, [key]: value };

    try {
      // Save to localStorage immediately for instant feedback
      localStorage.setItem(
        "notification_preferences",
        JSON.stringify(newPreferences),
      );
      setPreferences(newPreferences);

      // Attempt to save to backend
      const response = await fetch("/api/user/preferences", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify({
          [key.replace(/([A-Z])/g, "_$1").toLowerCase()]: value,
        }),
      });

      if (response.ok) {
        toast.success("Notification preference updated");
      } else {
        // If backend fails, still keep the local change but show warning
        console.warn("Failed to save to backend, keeping local change");
        toast.success("Preference updated locally");
      }
    } catch (error) {
      console.error("Error saving notification preference:", error);
      toast.success("Preference updated locally");
    } finally {
      setSaving(null);
    }
  };

  if (loading) {
    return (
      <Card data-testid="notification-settings">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notification Preferences
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
    <Card data-testid="notification-settings">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Notification Preferences
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Email Alerts */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Label className="text-sm font-medium flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Email Alerts
            </Label>
            <p className="text-xs text-slate-400">
              Receive email notifications for critical alerts and security
              events
            </p>
          </div>
          <Switch
            checked={preferences.emailAlerts}
            onCheckedChange={(checked) =>
              savePreference("emailAlerts", checked)
            }
            disabled={saving === "emailAlerts"}
            data-testid="email-alerts-toggle"
            aria-label="Toggle email alerts"
          />
        </div>

        {/* Slack Notifications */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Label className="text-sm font-medium flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Slack Notifications
            </Label>
            <p className="text-xs text-gray-500">
              Send notifications to your configured Slack channels
            </p>
          </div>
          <Switch
            checked={preferences.slackNotifications}
            onCheckedChange={(checked) =>
              savePreference("slackNotifications", checked)
            }
            disabled={saving === "slackNotifications"}
            data-testid="slack-notifications-toggle"
            aria-label="Toggle Slack notifications"
          />
        </div>

        {/* Weekly Summary */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Label className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Weekly Summary Digest
            </Label>
            <p className="text-xs text-gray-500">
              Receive a weekly summary of threats, alerts, and system activity
            </p>
          </div>
          <Switch
            checked={preferences.weeklySummary}
            onCheckedChange={(checked) =>
              savePreference("weeklySummary", checked)
            }
            disabled={saving === "weeklySummary"}
            data-testid="weekly-summary-toggle"
            aria-label="Toggle weekly summary digest"
          />
        </div>

        {/* Status Information */}
        <div className="pt-4 border-t">
          <div className="space-y-2">
            <Label className="text-sm font-medium">Notification Status</Label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="flex items-center gap-2 p-2 rounded-lg bg-muted/50">
                <div
                  className={`w-2 h-2 rounded-full ${preferences.emailAlerts ? "bg-green-500" : "bg-gray-400"}`}
                />
                <span className="text-xs">Email</span>
              </div>
              <div className="flex items-center gap-2 p-2 rounded-lg bg-muted/50">
                <div
                  className={`w-2 h-2 rounded-full ${preferences.slackNotifications ? "bg-green-500" : "bg-gray-400"}`}
                />
                <span className="text-xs">Slack</span>
              </div>
              <div className="flex items-center gap-2 p-2 rounded-lg bg-muted/50">
                <div
                  className={`w-2 h-2 rounded-full ${preferences.weeklySummary ? "bg-green-500" : "bg-gray-400"}`}
                />
                <span className="text-xs">Weekly</span>
              </div>
            </div>
          </div>
        </div>

        {/* Help Text */}
        <div className="pt-2">
          <p className="text-xs text-gray-500">
            Changes are saved automatically. Contact your administrator to
            configure email and Slack integration settings.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
