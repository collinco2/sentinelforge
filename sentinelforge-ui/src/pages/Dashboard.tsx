import React, { useState } from "react";
import { DashboardLayout } from "../layout/DashboardLayout";
import { StatCard } from "../components/StatCard";
import { IocTable } from "../components/IocTable";
import { ThreatChart } from "../components/ThreatChart";
import { Card, CardContent } from "../components/ui/card";
import { ShieldAlert, Eye, Flag, Server } from "lucide-react";
import { IOCData } from "../components/IocTable";
import { IocDetailModal } from "../components/IocDetailModal";

export function Dashboard() {
  const [isIocModalOpen, setIocModalOpen] = useState(false);
  const [selectedIoc, setSelectedIoc] = useState<IOCData | null>(null);

  const handleIocRowClick = (ioc: IOCData) => {
    setSelectedIoc(ioc);
    setIocModalOpen(true);
  };

  return (
    <DashboardLayout title="Threat Intelligence Dashboard">
      <div className="space-y-6">
        {/* Stats Section */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard 
            title="Critical Threats" 
            value="12" 
            icon={ShieldAlert}
            variant="critical"
            change={32}
            changePeriod="vs yesterday"
            className="min-h-[96px]"
          />
          
          <StatCard 
            title="Active IOCs" 
            value="1,287" 
            icon={Eye} 
            variant="default"
            change={-8}
            changePeriod="last 7 days"
            className="min-h-[96px]"
          />
          
          <StatCard 
            title="Alerts Today" 
            value="28" 
            icon={Flag} 
            variant="warning"
            change={15}
            className="min-h-[96px]"
          />

          <StatCard 
            title="Monitored Assets" 
            value="426" 
            icon={Server} 
            variant="success"
            change={0}
            changePeriod="no change"
            className="min-h-[96px]"
          />
        </div>
        
        {/* IOC Table Section */}
        <Card className="bg-card shadow-sm border-border">
          <CardContent className="p-6">
            <h2 className="text-xl font-semibold mb-4">Active Indicators of Compromise</h2>
            <IocTable 
              className="w-full" 
              onRowClick={handleIocRowClick}
              noInternalModal={true}
            />
          </CardContent>
        </Card>
        
        {/* Chart Section */}
        <Card className="bg-card shadow-sm border-border">
          <CardContent className="p-6">
            <h2 className="text-xl font-semibold mb-4">Threat Trend Analysis</h2>
            <div className="h-[300px]">
              <ThreatChart />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* IOC Detail Modal - now managed at Dashboard level */}
      {selectedIoc && (
        <IocDetailModal 
          ioc={selectedIoc} 
          isOpen={isIocModalOpen} 
          onOpenChange={(open) => {
            setIocModalOpen(open);
            if (!open) setSelectedIoc(null);
          }} 
        />
      )}
    </DashboardLayout>
  );
} 