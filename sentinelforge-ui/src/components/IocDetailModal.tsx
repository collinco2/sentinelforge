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
  DialogFooter,
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

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getSeverityColor = (severity: IOCData['severity']) => {
    switch (severity) {
      case 'critical':
        return 'text-red-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 90) return 'bg-red-600';
    if (confidence >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getTypeIcon = (type: IOCData['type']) => {
    switch (type) {
      case 'ip':
        return <Shield className="h-4 w-4 text-purple-400" />;
      case 'domain':
        return <Globe className="h-4 w-4 text-green-400" />;
      case 'file':
        return <FileText className="h-4 w-4 text-blue-400" />;
      case 'url':
        return <Link2 className="h-4 w-4 text-teal-400" />;
      case 'email':
        return <Mail className="h-4 w-4 text-pink-400" />;
      default:
        return <Info className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
        <div className="bg-zinc-900 text-gray-100 rounded-xl shadow-xl p-6 w-[90vw] max-w-3xl relative overflow-y-auto max-h-[80vh]">
          {/* Close Button */}
          <button 
            onClick={() => onOpenChange(false)}
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-100 bg-zinc-800 hover:bg-zinc-700 rounded-full p-1 transition-colors"
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </button>
          
          {/* Header */}
          <div className="mb-6 pr-8">
            <div className="flex items-center mb-1">
              <span className={getSeverityColor(ioc.severity)}>
                {ioc.severity === 'critical' || ioc.severity === 'high' ? (
                  <AlertTriangle className="h-5 w-5 inline mr-2" />
                ) : (
                  <Info className="h-5 w-5 inline mr-2" />
                )}
              </span>
              <h2 className="text-xl font-semibold text-gray-100">IOC Details</h2>
            </div>
            <p className="text-sm text-gray-400">
              Detailed information about the indicator of compromise
            </p>
          </div>
          
          {/* Tabs */}
          <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="w-full mb-6">
              <TabsTrigger value="overview" className="flex-1">Overview</TabsTrigger>
              <TabsTrigger value="mitre" className="flex-1">MITRE ATT&CK</TabsTrigger>
              <TabsTrigger value="ml" className="flex-1">ML Explanation</TabsTrigger>
            </TabsList>
            
            {/* Overview Tab Content */}
            <TabsContent value="overview" className="space-y-6">
              {/* IOC Value */}
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-400">Value</h3>
                <div className="flex items-center">
                  <div className="mr-2">{getTypeIcon(ioc.type)}</div>
                  <code className="font-mono bg-zinc-800 p-2 rounded-md text-white w-full overflow-x-auto">
                    {ioc.value}
                  </code>
                </div>
              </div>

              {/* Type & Severity */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">Type</h3>
                  <div className="px-3 py-1.5 rounded-md bg-zinc-800 inline-block text-sm capitalize">
                    {ioc.type}
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">Severity</h3>
                  <div
                    className={`px-3 py-1.5 rounded-md inline-block text-sm capitalize ${getSeverityColor(
                      ioc.severity
                    )} bg-zinc-800`}
                  >
                    {ioc.severity}
                  </div>
                </div>
              </div>

              {/* Confidence */}
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Confidence Score</h3>
                <div className="flex items-center">
                  <div className="w-full bg-zinc-800 rounded-full h-2 mr-3">
                    <div
                      className={`h-full rounded-full ${getConfidenceColor(ioc.confidence)}`}
                      style={{ width: `${ioc.confidence}%` }}
                    />
                  </div>
                  <span className="text-sm text-white font-medium">{ioc.confidence}%</span>
                </div>
              </div>

              {/* First Observed */}
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">First Observed</h3>
                <div className="flex items-center text-gray-300">
                  <Clock className="h-4 w-4 mr-2 text-gray-400" />
                  {formatTimestamp(ioc.timestamp)}
                </div>
              </div>

              {/* Additional mock details */}
              <div className="space-y-2 border-t border-zinc-700 pt-4 mt-4">
                <h3 className="text-sm font-medium text-gray-400">Associated Alerts</h3>
                <ul className="space-y-2 text-sm text-gray-300">
                  <li className="bg-zinc-800 p-2 rounded flex justify-between">
                    <span>Network scan detected</span>
                    <span className="text-gray-400 text-xs">2 hours ago</span>
                  </li>
                  <li className="bg-zinc-800 p-2 rounded flex justify-between">
                    <span>Suspicious outbound connection</span>
                    <span className="text-gray-400 text-xs">4 hours ago</span>
                  </li>
                </ul>
              </div>
            </TabsContent>
            
            {/* MITRE ATT&CK Tab Content */}
            <TabsContent value="mitre" className="space-y-6">
              <div className="flex items-center mb-4">
                <Target className="h-5 w-5 mr-2 text-blue-400" />
                <h3 className="text-md font-medium text-gray-100">MITRE ATT&CK Framework Analysis</h3>
              </div>
              
              <div className="space-y-4">
                <div className="bg-zinc-800 p-4 rounded-md">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Tactics</h4>
                  <div className="flex flex-wrap gap-2">
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs">Initial Access</span>
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs">Command & Control</span>
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs">Exfiltration</span>
                  </div>
                </div>
                
                <div className="bg-zinc-800 p-4 rounded-md">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Techniques</h4>
                  <ul className="space-y-2">
                    <li className="flex justify-between">
                      <span className="text-sm text-gray-300">T1566 - Phishing</span>
                      <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">High Confidence</span>
                    </li>
                    <li className="flex justify-between">
                      <span className="text-sm text-gray-300">T1071 - Application Layer Protocol</span>
                      <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">Medium Confidence</span>
                    </li>
                  </ul>
                </div>
              </div>
            </TabsContent>
            
            {/* ML Explanation Tab Content */}
            <TabsContent value="ml" className="space-y-6">
              <div className="flex items-center mb-4">
                <Braces className="h-5 w-5 mr-2 text-purple-400" />
                <h3 className="text-md font-medium text-gray-100">Machine Learning Analysis</h3>
              </div>
              
              <div className="space-y-4">
                <div className="bg-zinc-800 p-4 rounded-md">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Threat Score: {ioc.confidence}/100</h4>
                  <p className="text-sm text-gray-400">This IOC was analyzed using our ML model and received a high threat score based on the following factors:</p>
                </div>
                
                <div className="bg-zinc-800 p-4 rounded-md">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Key Factors</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start">
                      <span className="text-red-400 mr-2">•</span>
                      <span className="text-gray-300">Pattern matches known malicious {ioc.type} signatures (83% similarity)</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-red-400 mr-2">•</span>
                      <span className="text-gray-300">Association with known threat actor infrastructure</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-red-400 mr-2">•</span>
                      <span className="text-gray-300">Recently observed in multiple attack campaigns</span>
                    </li>
                  </ul>
                </div>
                
                <div className="bg-zinc-800 p-4 rounded-md">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Model Information</h4>
                  <p className="text-xs text-gray-400">This analysis was performed using SentinelForge's Neural Threat Detection v2.3, last updated 7 days ago.</p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
          
          {/* Footer */}
          <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 border-t border-zinc-700 pt-4 mt-6">
            <Button
              variant="outline"
              className="bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700 mt-2 sm:mt-0"
              onClick={() => onOpenChange(false)}
            >
              Close
            </Button>
            <Button className="bg-blue-600 text-white hover:bg-blue-700">
              <ExternalLink className="h-4 w-4 mr-2" />
              View in Threat Intelligence
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
} 