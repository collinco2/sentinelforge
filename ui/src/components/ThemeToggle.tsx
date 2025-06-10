/**
 * 🎨 ThemeToggle Component - Professional Theme Switcher for SentinelForge
 *
 * Provides a comprehensive theme switching interface with:
 * - Light, Dark, and System theme modes
 * - Persistent theme preferences via localStorage
 * - Smooth transitions and visual feedback
 * - Accessibility compliant with ARIA labels
 * - Professional dropdown interface
 */

import React from "react";
import { Monitor, Moon, Sun, Check } from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { useTheme, Theme } from "../hooks/useTheme";
import { cn } from "../lib/utils";

interface ThemeToggleProps {
  className?: string;
  variant?: "icon" | "button" | "compact";
  showLabel?: boolean;
}

export function ThemeToggle({ 
  className, 
  variant = "icon",
  showLabel = false 
}: ThemeToggleProps) {
  const { theme, setTheme, actualTheme } = useTheme();

  const themeOptions: Array<{
    value: Theme;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    description: string;
  }> = [
    {
      value: "light",
      label: "Light",
      icon: Sun,
      description: "Light theme with bright backgrounds",
    },
    {
      value: "dark",
      label: "Dark",
      icon: Moon,
      description: "Dark theme with dark backgrounds",
    },
    {
      value: "system",
      label: "System",
      icon: Monitor,
      description: "Follow system preference",
    },
  ];

  const getCurrentIcon = () => {
    if (theme === "system") {
      return actualTheme === "dark" ? Moon : Sun;
    }
    return theme === "dark" ? Moon : Sun;
  };

  const getCurrentLabel = () => {
    if (theme === "system") {
      return `System (${actualTheme})`;
    }
    return theme.charAt(0).toUpperCase() + theme.slice(1);
  };

  const CurrentIcon = getCurrentIcon();

  if (variant === "compact") {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setTheme(actualTheme === "dark" ? "light" : "dark")}
        className={cn(
          "h-8 w-8 p-0 text-muted-foreground hover:text-foreground",
          className
        )}
        aria-label={`Switch to ${actualTheme === "dark" ? "light" : "dark"} theme`}
      >
        <CurrentIcon className="h-4 w-4" />
      </Button>
    );
  }

  if (variant === "button") {
    return (
      <Button
        variant="outline"
        onClick={() => setTheme(actualTheme === "dark" ? "light" : "dark")}
        className={cn("flex items-center gap-2", className)}
        aria-label={`Switch to ${actualTheme === "dark" ? "light" : "dark"} theme`}
      >
        <CurrentIcon className="h-4 w-4" />
        {showLabel && <span>{getCurrentLabel()}</span>}
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            "h-9 w-9 text-muted-foreground hover:text-foreground",
            className
          )}
          aria-label="Toggle theme"
        >
          <CurrentIcon className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        {themeOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = theme === option.value;
          
          return (
            <DropdownMenuItem
              key={option.value}
              onClick={() => setTheme(option.value)}
              className={cn(
                "flex items-center gap-3 cursor-pointer",
                isSelected && "bg-accent/10"
              )}
            >
              <Icon className="h-4 w-4" />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{option.label}</span>
                  {isSelected && <Check className="h-4 w-4 text-primary" />}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {option.description}
                </p>
              </div>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/**
 * ThemeProvider Component - Wrapper for theme context
 */
interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
}

export function ThemeProvider({ 
  children, 
  defaultTheme = "system" 
}: ThemeProviderProps) {
  // The useTheme hook handles all the theme logic internally
  return <>{children}</>;
}

/**
 * useThemeToggle Hook - Simplified theme toggle functionality
 */
export function useThemeToggle() {
  const { theme, setTheme, actualTheme, toggleTheme } = useTheme();
  
  return {
    currentTheme: theme,
    actualTheme,
    setTheme,
    toggleTheme,
    isLight: actualTheme === "light",
    isDark: actualTheme === "dark",
    isSystem: theme === "system",
  };
}

export default ThemeToggle;
