import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  className?: string;
}

export function StatCard({ title, value, subtitle, icon: Icon, className }: StatCardProps) {
  return (
    <Card className={cn("bg-zinc-900 text-zinc-100 border-zinc-800 shadow-md rounded-2xl p-4 transition hover:scale-[1.01]", className)}>
      <CardContent className="flex flex-col space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-zinc-400">{title}</p>
          {Icon && <Icon className="h-5 w-5 text-zinc-500" />}
        </div>
        <p className="text-2xl font-semibold tracking-tight">{value}</p>
        {subtitle && <p className="text-xs text-zinc-500">{subtitle}</p>}
      </CardContent>
    </Card>
  );
} 