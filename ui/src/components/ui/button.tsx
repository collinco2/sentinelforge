import * as React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(
          // Base styles with enhanced focus visibility for WCAG 2.1 and SentinelForge theme
          "inline-flex items-center justify-center font-medium transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2",
          "disabled:opacity-50 disabled:pointer-events-none ring-offset-background",
          // Enhanced focus for better accessibility
          "focus:ring-2 focus:ring-accent focus:ring-offset-2",
          {
            // Primary - SentinelForge theme with glow effect
            "bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/95 rounded-2xl shadow-glow hover:shadow-glow-lg":
              variant === "default",

            // Destructive - maintains good contrast with rounded corners
            "bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-destructive/95 rounded-2xl":
              variant === "destructive",

            // Outline - SentinelForge theme with border styling
            "border border-border text-foreground bg-transparent hover:bg-muted hover:text-foreground active:bg-muted/80 rounded-2xl":
              variant === "outline",

            // Secondary - SentinelForge panel styling
            "bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:text-foreground active:bg-secondary/60 rounded-2xl":
              variant === "secondary",

            // Ghost - enhanced with SentinelForge hover styling
            "text-muted-foreground hover:bg-muted hover:text-foreground active:bg-muted/80 rounded-lg":
              variant === "ghost",

            // Link - maintains primary color for good contrast
            "underline-offset-4 hover:underline text-primary hover:text-primary/80":
              variant === "link",

            // Size variants
            "h-10 py-2 px-4": size === "default",
            "h-9 px-3 rounded-md": size === "sm",
            "h-11 px-8 rounded-md": size === "lg",
            "h-10 w-10": size === "icon",
          },
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button };
