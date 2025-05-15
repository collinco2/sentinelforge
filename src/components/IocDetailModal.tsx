import React, { useState } from 'react';
import { 
  Clock, 
  AlertTriangle, 
  Shield, 
  Info, 
  ExternalLink, 
  Globe,
  FileText, 
  Link2,
  Mail,
  X,
  Target,
  Braces
} from 'lucide-react';
import { IOCData } from './IocTable';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
  DialogFooter,
  DialogDescription
} from './ui/dialog';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';

interface IocDetailModalProps {
  ioc: IOCData | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function IocDetailModal({ ioc, isOpen, onOpenChange }: IocDetailModalProps) {
  const [activeTab, setActiveTab] = useState<string>("overview");
  
  if (!ioc) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="bg-zinc-900 text-gray-100 max-w-3xl w-[90vw] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center">
            <span className={
              ioc.severity === 'critical' ? 'text-red-500' :
              ioc.severity === 'high' ? 'text-orange-500' :
              ioc.severity === 'medium' ? 'text-yellow-500' :
              ioc.severity === 'low' ? 'text-blue-400' : 'text-gray-400'
            }>
              {ioc.severity === 'critical' || ioc.severity === 'high' ? (
                <AlertTriangle className="h-5 w-5 inline mr-2" />
              ) : (
                <Info className="h-5 w-5 inline mr-2" />
              )}
            </span>
            <DialogTitle className="text-xl font-semibold text-gray-100">IOC Details</DialogTitle>
          </div>
          <DialogDescription className="text-gray-400">
            Detailed information about the indicator of compromise
          </DialogDescription>
          
          <DialogClose asChild>
            <button
              className="absolute top-4 right-4 text-gray-400 hover:text-white rounded-full p-1 transition-colors z-50"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </DialogClose>
        </DialogHeader>

        {/* Tabs & Content */}
        <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full mb-6">
            <TabsTrigger value="overview" className="flex-1">Overview</TabsTrigger>
            <TabsTrigger value="mitre" className="flex-1">MITRE ATT&CK</TabsTrigger>
            <TabsTrigger value="ml" className="flex-1">ML Explanation</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-400">Value</h3>
              <code className="font-mono bg-zinc-800 p-2 rounded-md text-white w-full block overflow-x-auto">
                {ioc.value}
              </code>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Type</h3>
                <div className="px-3 py-1.5 rounded-md bg-zinc-800 inline-block text-sm capitalize">
                  {ioc.type}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Severity</h3>
                <div className="px-3 py-1.5 rounded-md bg-zinc-800 inline-block text-sm capitalize">
                  {ioc.severity}
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Confidence Score</h3>
              <div className="flex items-center">
                <div className="w-full bg-zinc-800 rounded-full h-2 mr-3">
                  <div
                    className={`h-full rounded-full ${
                      ioc.confidence > 90 ? 'bg-red-600' :
                      ioc.confidence >= 70 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${ioc.confidence}%` }}
                  />
                </div>
                <span className="text-sm text-white font-medium">{ioc.confidence}%</span>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">First Observed</h3>
              <div className="flex items-center text-gray-300">
                <Clock className="h-4 w-4 mr-2 text-gray-400" />
                {new Date(ioc.timestamp).toLocaleString()}
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="mitre" className="space-y-4">
            <div className="bg-zinc-800 p-4 rounded-md">
              <h4 className="text-sm font-medium text-gray-300 mb-2">MITRE ATT&CK Framework</h4>
              <p className="text-sm text-gray-400">Tactical analysis of this threat indicator</p>
            </div>
          </TabsContent>
          
          <TabsContent value="ml" className="space-y-4">
            <div className="bg-zinc-800 p-4 rounded-md">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Machine Learning Analysis</h4>
              <p className="text-sm text-gray-400">This indicator was analyzed by our ML model</p>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="border-t border-zinc-700 pt-4 mt-6">
          <DialogClose asChild>
            <button
              className="inline-flex items-center justify-center rounded-md font-medium bg-zinc-800 border border-zinc-700 text-gray-300 hover:bg-zinc-700 px-4 py-2 text-sm cursor-pointer pointer-events-auto"
            >
              Close
            </button>
          </DialogClose>
          <Button className="bg-blue-600 text-white hover:bg-blue-700">
            <ExternalLink className="h-4 w-4 mr-2" />
            View in Threat Intelligence
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 