import React from "react";
import { Card, CardContent } from "../components/ui/card";
import { cn } from "../lib/utils";
import { LucideIcon, TrendingDown, TrendingUp } from "lucide-react";

export interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  variant?: "default" | "critical" | "success" | "warning";
  className?: string;
  change?: number;
  changePeriod?: string;
}

export function StatCard({
  title,
  value,
  icon: Icon,
  variant = "default",
  className,
  change,
  changePeriod = "vs last period",
}: StatCardProps) {
  // Determine if change is positive, negative, or neutral
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;
  const changeDisplay = change ? Math.abs(change) : null;

  return (
    <Card
      className={cn(
        "relative overflow-hidden transition-all duration-200 hover:shadow-md",
        {
          "bg-muted": variant === "default",
          "bg-red-500/10 border-red-500/20": variant === "critical",
          "bg-green-500/10 border-green-500/20": variant === "success",
          "bg-yellow-500/10 border-yellow-500/20": variant === "warning",
        },
        className
      )}
    >
      <CardContent className="px-6 py-4">
        <div className="flex items-start">
          <div
            className={cn(
              "bg-white bg-opacity-10 rounded-full p-2 mr-4",
              {
                "bg-muted-foreground/10": variant === "default",
                "bg-red-500/20": variant === "critical",
                "bg-green-500/20": variant === "success",
                "bg-yellow-500/20": variant === "warning",
              }
            )}
          >
            <Icon
              size={24}
              className={cn("text-3xl", {
                "text-muted-foreground": variant === "default",
                "text-red-500": variant === "critical",
                "text-green-500": variant === "success",
                "text-yellow-500": variant === "warning",
              })}
            />
          </div>

          <div className="space-y-2">
            <p
              className={cn("text-sm font-medium", {
                "text-muted-foreground": variant === "default",
                "text-red-500": variant === "critical",
                "text-green-500": variant === "success",
                "text-yellow-500": variant === "warning",
              })}
            >
              {title}
            </p>
            <p
              className={cn("text-2xl font-bold tracking-tight", {
                "text-foreground": variant === "default",
                "text-red-500": variant === "critical",
                "text-green-500": variant === "success",
                "text-yellow-500": variant === "warning",
              })}
            >
              {value}
            </p>
            
            {change !== undefined && (
              <div className="flex items-center gap-1 mt-1">
                {isPositive ? (
                  <TrendingUp className="text-green-500" size={16} />
                ) : isNegative ? (
                  <TrendingDown className="text-red-500" size={16} />
                ) : null}
                <span
                  className={cn("text-xs font-medium", {
                    "text-green-500": isPositive,
                    "text-red-500": isNegative,
                    "text-muted-foreground": !isPositive && !isNegative,
                  })}
                >
                  {changeDisplay}%
                  <span className="text-muted-foreground ml-1">
                    {changePeriod}
                  </span>
                </span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 