import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import {
  AlertTriangle,
  Shield,
  Loader2,
  ExternalLink,
  FileText,
  Info,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";

// Define the public IOC data interface
interface PublicIocData {
  value: string;
  type: string;
  score: number;
  category: string;
  first_seen: string;
  threat_class: string;
  malicious_probability: number;
  view_count: number;
  share_id: string;
  attack_techniques: Array<{
    id: string;
    name: string;
    confidence: string;
  }>;
  feature_importance: Array<{
    feature: string;
    weight: number;
    description: string;
  }>;
}

// Interface for ML explanation data
interface PublicExplanationData {
  value: string;
  score: number;
  explanation: {
    summary: string;
    feature_breakdown: Array<{
      feature: string;
      value: string;
      weight: number;
    }>;
  };
}

export function ShareableIocView() {
  const { iocValue } = useParams<{ iocValue: string }>();
  const [iocData, setIocData] = useState<PublicIocData | null>(null);
  const [explanationData, setExplanationData] =
    useState<PublicExplanationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch the IOC data
        const encodedValue = encodeURIComponent(iocValue || "");
        const response = await axios.get(
          `http://localhost:5059/api/ioc/share?value=${encodedValue}`,
        );
        setIocData(response.data);

        // Fetch the ML explanation
        try {
          const explainResponse = await axios.get(
            `http://localhost:5059/api/explain/share/${encodedValue}`,
          );
          setExplanationData(explainResponse.data);
        } catch (explainError) {
          console.error("Error fetching ML explanation:", explainError);
          // Don't set an error for this - it's optional
        }
      } catch (err) {
        console.error("Error fetching shared IOC:", err);
        setError(
          axios.isAxiosError(err) && err.response?.status === 404
            ? "The requested threat intelligence indicator was not found."
            : "An error occurred while loading the threat intelligence data.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    if (iocValue) {
      fetchData();
    } else {
      setError("No indicator specified");
      setIsLoading(false);
    }
  }, [iocValue]);

  // Function to render severity badge with appropriate color
  const renderSeverityBadge = (category: string) => {
    const severityColors = {
      critical: "bg-red-700 hover:bg-red-600",
      high: "bg-orange-700 hover:bg-orange-600",
      medium: "bg-yellow-700 hover:bg-yellow-600",
      low: "bg-blue-700 hover:bg-blue-600",
    };

    const color =
      severityColors[category as keyof typeof severityColors] || "bg-gray-700";

    return (
      <Badge className={`${color} text-white`}>
        {category.charAt(0).toUpperCase() + category.slice(1)}
      </Badge>
    );
  };

  // Function to format date
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch (e) {
      return dateString;
    }
  };

  // Function to render the weight bar
  const renderWeightBar = (weight: number) => {
    const percentage = Math.min(Math.abs(weight * 100), 100);
    const barColor = weight >= 0 ? "bg-red-600" : "bg-blue-600";

    return (
      <div className="flex items-center w-full gap-2">
        <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
          <div
            className={`h-full ${barColor} rounded-full`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-xs text-gray-400 w-12 text-right">
          {(weight * 100).toFixed(0)}%
        </span>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-zinc-900 text-gray-200 flex items-center justify-center">
        <div className="flex flex-col items-center p-8">
          <Loader2 className="h-12 w-12 text-blue-500 animate-spin mb-4" />
          <h2 className="text-xl font-medium">
            Loading Threat Intelligence...
          </h2>
          <p className="text-gray-400 mt-2">
            Retrieving the latest data for this indicator
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-900 text-gray-200 flex items-center justify-center p-4">
        <Card className="bg-zinc-800 border-zinc-700 shadow-lg max-w-2xl w-full">
          <CardContent className="pt-6 flex flex-col items-center text-center">
            <AlertTriangle className="h-16 w-16 text-red-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-200 mb-2">
              Threat Intelligence Not Available
            </h2>
            <p className="text-gray-400 mb-4">{error}</p>
            <Button
              variant="default"
              className="bg-blue-600 hover:bg-blue-500"
              onClick={() => (window.location.href = "/")}
            >
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-900 text-gray-200 p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold flex items-center">
              <Shield className="mr-2 h-6 w-6 text-blue-500" />
              SentinelForge Threat Intelligence
            </h1>
            <p className="text-gray-400 mt-1">Public shareable threat report</p>
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="text-gray-300 border-gray-700 bg-zinc-800 px-3 py-1"
            >
              <Info className="h-4 w-4 mr-1 text-gray-400" />
              <span className="text-xs md:text-sm">
                {iocData?.view_count || 0} views
              </span>
            </Badge>
            <Badge
              variant="outline"
              className="text-gray-300 border-gray-700 bg-zinc-800 px-3 py-1"
            >
              <FileText className="h-4 w-4 mr-1 text-gray-400" />
              <span className="text-xs md:text-sm">
                ID: {iocData?.share_id || "unknown"}
              </span>
            </Badge>
          </div>
        </div>

        {/* IOC overview card */}
        <Card className="bg-zinc-800 border-zinc-700 shadow-lg mb-6">
          <CardHeader>
            <CardTitle className="text-xl text-gray-200">
              Indicator Details
            </CardTitle>
            <CardDescription className="text-gray-400">
              Basic information about this threat indicator
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">
                    Indicator
                  </h3>
                  <code className="block bg-zinc-900 p-3 rounded font-mono text-gray-200 border border-zinc-700 break-all">
                    {iocData?.value}
                  </code>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">
                    Type
                  </h3>
                  <p className="text-gray-200 capitalize">{iocData?.type}</p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">
                    First Observed
                  </h3>
                  <p className="text-gray-200">
                    {formatDate(iocData?.first_seen || "")}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">
                    Severity
                  </h3>
                  <div className="flex items-center space-x-2">
                    {renderSeverityBadge(iocData?.category || "medium")}
                    <span className="text-gray-300">
                      {iocData?.score.toFixed(1)} / 10
                    </span>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">
                    Probability
                  </h3>
                  <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{
                        width: `${(iocData?.malicious_probability || 0) * 100}%`,
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    {((iocData?.malicious_probability || 0) * 100).toFixed(1)}%
                    confidence score
                  </p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-1">
                    Classification
                  </h3>
                  <p className="text-gray-200">
                    {iocData?.threat_class || "Unknown"}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Techniques and tactics */}
        {iocData?.attack_techniques && iocData.attack_techniques.length > 0 && (
          <Card className="bg-zinc-800 border-zinc-700 shadow-lg mb-6">
            <CardHeader>
              <CardTitle className="text-xl text-gray-200">
                MITRE ATT&CK Techniques
              </CardTitle>
              <CardDescription className="text-gray-400">
                Associated attack techniques for this indicator
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {iocData.attack_techniques.map((technique, index) => (
                  <div
                    key={index}
                    className="p-3 bg-zinc-900 border border-zinc-700 rounded-md flex items-start"
                  >
                    <div className="flex-1">
                      <div className="font-mono text-xs text-blue-400 mb-1">
                        {technique.id}
                      </div>
                      <h4 className="font-medium text-gray-200">
                        {technique.name}
                      </h4>
                    </div>
                    <Badge
                      className={
                        technique.confidence === "high"
                          ? "bg-red-700"
                          : technique.confidence === "medium"
                            ? "bg-orange-700"
                            : "bg-blue-700"
                      }
                    >
                      {technique.confidence}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* ML explanation */}
        {explanationData && (
          <Card className="bg-zinc-800 border-zinc-700 shadow-lg mb-6">
            <CardHeader>
              <CardTitle className="text-xl text-gray-200">
                ML Analysis
              </CardTitle>
              <CardDescription className="text-gray-400">
                Machine learning insights for this indicator
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-300 mb-4">
                {explanationData.explanation.summary}
              </p>

              {explanationData.explanation.feature_breakdown.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-gray-400">
                    Key Factors
                  </h3>

                  <div className="space-y-3">
                    {explanationData.explanation.feature_breakdown.map(
                      (feature, index) => (
                        <div key={index} className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-300">
                              {feature.feature}
                            </span>
                            {feature.value && (
                              <span className="text-xs text-gray-400">
                                {feature.value}
                              </span>
                            )}
                          </div>
                          {renderWeightBar(feature.weight)}
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            This report was generated by SentinelForge Threat Intelligence
            Platform
          </p>
          <p className="mt-1">
            Learn more about threat intelligence at{" "}
            <a
              href="https://sentinelforge.example.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 flex items-center justify-center mt-1"
            >
              sentinelforge.example.com
              <ExternalLink className="h-3 w-3 ml-1" />
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
