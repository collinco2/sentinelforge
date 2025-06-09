import * as React from "react";
import { cn } from "@/lib/utils";

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
          // Base styles with enhanced focus visibility for WCAG 2.1
          "inline-flex items-center justify-center rounded-md font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:opacity-50 disabled:pointer-events-none ring-offset-background",
          // Enhanced focus for better accessibility
          "focus:ring-2 focus:ring-ring focus:ring-offset-2",
          {
            // Primary - maintains good contrast
            "bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/95":
              variant === "default",

            // Destructive - maintains good contrast
            "bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-destructive/95":
              variant === "destructive",

            // Outline - enhanced with darker border and better contrast
            "border-2 border-muted-foreground/30 text-foreground bg-background hover:bg-muted hover:border-muted-foreground/50 active:bg-muted/80":
              variant === "outline",

            // Secondary - enhanced contrast with darker background
            "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground active:bg-muted/60":
              variant === "secondary",

            // Ghost - enhanced with default text color for better visibility
            "text-muted-foreground hover:bg-muted hover:text-foreground active:bg-muted/80":
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
