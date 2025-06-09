import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  // Base styles with enhanced focus visibility for WCAG 2.1
  "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        // Primary - maintains good contrast
        default:
          "bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/95",

        // Destructive - maintains good contrast
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-destructive/95",

        // Outline - enhanced with darker border and better contrast
        outline:
          "border-2 border-muted-foreground/30 text-foreground bg-background hover:bg-muted hover:border-muted-foreground/50 active:bg-muted/80",

        // Secondary - enhanced contrast with darker background
        secondary:
          "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground active:bg-muted/60",

        // Ghost - enhanced with default text color for better visibility
        ghost:
          "text-muted-foreground hover:bg-muted hover:text-foreground active:bg-muted/80",

        // Link - maintains primary color for good contrast
        link: "underline-offset-4 hover:underline text-primary hover:text-primary/80",
      },
      size: {
        default: "h-10 py-2 px-4",
        sm: "h-9 px-3 rounded-md",
        lg: "h-11 px-8 rounded-md",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export type ButtonVariant =
  | "default"
  | "destructive"
  | "outline"
  | "secondary"
  | "ghost"
  | "link";
export type ButtonSize = "default" | "sm" | "lg" | "icon";
