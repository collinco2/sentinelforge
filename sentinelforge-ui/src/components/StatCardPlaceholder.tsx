import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import React from "react";

interface StatCardPlaceholderProps {
  className?: string;
  children?: React.ReactNode;
}

export function StatCardPlaceholder({ className, children }: StatCardPlaceholderProps) {
  return (
    <Card className={cn("bg-card border-border shadow-sm", className)}>
      <CardContent className="p-6">
        <div className="space-y-3">
          <div className="h-4 w-24 bg-muted rounded animate-pulse" />
          <div className="h-8 w-16 bg-muted rounded animate-pulse" />
          <div className="h-3 w-32 bg-muted/70 rounded animate-pulse" />
        </div>
        {children}
      </CardContent>
    </Card>
  );
} 