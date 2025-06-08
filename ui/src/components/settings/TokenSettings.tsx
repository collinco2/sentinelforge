import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Alert, AlertDescription } from "../ui/alert";
import { RefreshCw, Clock, Shield, AlertCircle } from "lucide-react";
import { toast } from "../../lib/toast";

interface TokenInfo {
  issued_at: string;
  expires_at: string;
  token_id: string;
  is_valid: boolean;
}

export const TokenSettings: React.FC = () => {
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [isRotating, setIsRotating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTokenInfo();
  }, []);

  const fetchTokenInfo = async () => {
    try {
      const response = await fetch("/api/auth/token-info", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTokenInfo(data);
      } else {
        console.error("Failed to fetch token info");
      }
    } catch (error) {
      console.error("Error fetching token info:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRotateToken = async () => {
    setIsRotating(true);
    try {
      const response = await fetch("/api/auth/rotate-token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();

        // Update stored token
        if (data.session_token) {
          localStorage.setItem("session_token", data.session_token);
        }

        // Refresh token info
        await fetchTokenInfo();

        toast.success("Authentication token rotated successfully");
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to rotate token");
      }
    } catch (error) {
      toast.error("Error rotating token");
    } finally {
      setIsRotating(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getTimeUntilExpiry = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();

    if (diffMs <= 0) return "Expired";

    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? "s" : ""}`;
    if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? "s" : ""}`;

    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    return `${diffMinutes} minute${diffMinutes > 1 ? "s" : ""}`;
  };

  const isTokenExpiringSoon = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();
    const diffHours = diffMs / (1000 * 60 * 60);
    return diffHours < 24; // Less than 24 hours
  };

  if (loading) {
    return (
      <Card data-testid="token-settings">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Authentication Tokens
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="token-settings">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Authentication Tokens
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {tokenInfo ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Issued At</span>
                </div>
                <p className="text-sm text-gray-600 ml-6">
                  {formatDate(tokenInfo.issued_at)}
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Expires At</span>
                </div>
                <div className="ml-6 space-y-1">
                  <p className="text-sm text-gray-600">
                    {formatDate(tokenInfo.expires_at)}
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={tokenInfo.is_valid ? "default" : "destructive"}
                      className="text-xs"
                    >
                      {tokenInfo.is_valid ? "Valid" : "Expired"}
                    </Badge>
                    {tokenInfo.is_valid && (
                      <span className="text-xs text-gray-500">
                        ({getTimeUntilExpiry(tokenInfo.expires_at)} remaining)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium">Token ID</span>
              </div>
              <p className="text-sm text-gray-600 ml-6 font-mono">
                {tokenInfo.token_id}
              </p>
            </div>

            {tokenInfo.is_valid &&
              isTokenExpiringSoon(tokenInfo.expires_at) && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Your authentication token will expire soon. Consider
                    rotating it to maintain access.
                  </AlertDescription>
                </Alert>
              )}

            <div className="pt-4 border-t">
              <Button
                onClick={handleRotateToken}
                disabled={isRotating}
                className="flex items-center gap-2"
                data-testid="rotate-token-button"
              >
                <RefreshCw
                  className={`h-4 w-4 ${isRotating ? "animate-spin" : ""}`}
                />
                {isRotating ? "Rotating..." : "Rotate Token"}
              </Button>
              <p className="text-xs text-gray-500 mt-2">
                Rotating your token will invalidate the current token and
                generate a new one. You may need to re-authenticate in other
                sessions.
              </p>
            </div>
          </>
        ) : (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Unable to load token information. Please try refreshing the page.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
