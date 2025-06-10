/**
 * 🎨 ThemedButton Component - SentinelForge themed button variants
 *
 * Provides button components with SentinelForge dark theme styling:
 * - Primary button with glow effect
 * - Secondary and ghost variants
 * - Consistent with theme design system
 * - Accessibility compliant
 */

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";
import { useThemeClass } from "@/hooks/useThemeClass";

export interface ThemedButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline";
  size?: "default" | "sm" | "lg" | "icon";
  asChild?: boolean;
}

const ThemedButton = React.forwardRef<HTMLButtonElement, ThemedButtonProps>(
  ({ className, variant = "primary", size = "default", asChild = false, ...props }, ref) => {
    const theme = useThemeClass();
    const Comp = asChild ? Slot : "button";

    // Get variant-specific classes
    const getVariantClasses = () => {
      switch (variant) {
        case "primary":
          return theme.buttonPrimary;
        case "secondary":
          return theme.buttonSecondary;
        case "ghost":
          return theme.buttonGhost;
        case "outline":
          return cn(
            "border border-border bg-transparent text-foreground",
            "hover:bg-muted hover:text-foreground",
            "focus:ring-2 focus:ring-ring focus:ring-offset-2"
          );
        default:
          return theme.buttonPrimary;
      }
    };

    // Get size-specific classes
    const getSizeClasses = () => {
      switch (size) {
        case "sm":
          return "h-9 px-3";
        case "lg":
          return "h-11 px-8";
        case "icon":
          return "h-10 w-10";
        default:
          return "h-10 px-4 py-2";
      }
    };

    return (
      <Comp
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
          getSizeClasses(),
          getVariantClasses(),
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
ThemedButton.displayName = "ThemedButton";

export { ThemedButton };
