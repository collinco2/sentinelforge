import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Alert, AlertDescription } from "../ui/alert";
import { Input } from "../ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "../ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "../ui/dialog";
import { RefreshCw, Clock, Shield, AlertCircle, Copy } from "lucide-react";
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
  const [showRotateDialog, setShowRotateDialog] = useState(false);

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
    setShowRotateDialog(false); // Close the confirmation dialog

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

  // Reusable CopyableInput component
  const CopyableInput: React.FC<{
    value: string;
    placeholder?: string;
    readOnly?: boolean;
    className?: string;
    "aria-label"?: string;
    "data-testid"?: string;
  }> = ({
    value,
    placeholder,
    readOnly = true,
    className,
    "aria-label": ariaLabel,
    "data-testid": dataTestId,
  }) => {
    const [showTooltip, setShowTooltip] = React.useState(false);

    const handleCopy = async () => {
      try {
        await navigator.clipboard.writeText(value);
        setShowTooltip(true);
        setTimeout(() => setShowTooltip(false), 2000);
        toast.success("Copied!");
      } catch (error) {
        toast.error("Failed to copy to clipboard");
      }
    };

    return (
      <div className="relative">
        <Input
          value={value}
          placeholder={placeholder}
          readOnly={readOnly}
          className={`pr-10 font-mono text-sm ${className || ""}`}
          aria-label={ariaLabel}
          data-testid={dataTestId}
        />
        <TooltipProvider>
          <Tooltip open={showTooltip}>
            <TooltipTrigger asChild>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0 hover:bg-muted"
                onClick={handleCopy}
                aria-label="Copy to clipboard"
                data-testid={`${dataTestId}-copy`}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">
              <p>Copied!</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    );
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
    <div className="space-y-6" data-testid="token-settings">
      {/* Token Information Card */}
      <Card className="shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Current Token Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tokenInfo ? (
            <div className="space-y-6">
              <div className="space-y-6 md:grid md:grid-cols-2 md:gap-6 md:space-y-0">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">Issued At</span>
                  </div>
                  <p className="text-sm text-gray-600 ml-6 break-all">
                    {formatDate(tokenInfo.issued_at)}
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">Expires At</span>
                  </div>
                  <div className="ml-6 space-y-2">
                    <p className="text-sm text-gray-600 break-all">
                      {formatDate(tokenInfo.expires_at)}
                    </p>
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                      <Badge
                        variant={tokenInfo.is_valid ? "default" : "destructive"}
                        className="text-xs w-fit"
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

              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Token ID</span>
                </div>
                <div className="ml-6">
                  <CopyableInput
                    value={tokenInfo.token_id}
                    aria-label="Authentication token ID"
                    data-testid="token-id-display"
                    className="w-full max-w-md"
                  />
                </div>
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
            </div>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Unable to load token information. Please try refreshing the
                page.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Token Rotation Card */}
      {tokenInfo && (
        <Card className="shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5" />
              Token Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4 leading-relaxed">
              Rotating your token will invalidate the current token and generate
              a new one. You may need to re-authenticate in other sessions.
            </p>
          </CardContent>
          <CardFooter className="flex flex-col sm:flex-row">
            <Dialog open={showRotateDialog} onOpenChange={setShowRotateDialog}>
              <DialogTrigger asChild>
                <Button
                  disabled={isRotating}
                  className="flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px]"
                  data-testid="rotate-token-button"
                >
                  <RefreshCw
                    className={`h-4 w-4 ${isRotating ? "animate-spin" : ""}`}
                  />
                  {isRotating ? "Rotating..." : "Rotate Token"}
                </Button>
              </DialogTrigger>
              <DialogContent className="w-full max-w-screen-sm sm:max-w-md">
                <DialogHeader className="pb-4">
                  <DialogTitle className="flex items-center gap-2 text-lg sm:text-xl">
                    <AlertCircle className="h-5 w-5 text-amber-500" />
                    Confirm Token Rotation
                  </DialogTitle>
                  <DialogDescription className="text-sm sm:text-base">
                    This action will invalidate your current authentication
                    token and generate a new one.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                      <div className="space-y-2">
                        <h4 className="font-medium text-amber-900">
                          Important Notice
                        </h4>
                        <ul className="text-sm text-amber-800 space-y-1">
                          <li>
                            • You may need to re-authenticate in other sessions
                          </li>
                          <li>• Any saved API tokens will remain valid</li>
                          <li>• This action cannot be undone</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3 sm:gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowRotateDialog(false)}
                    data-testid="cancel-rotate-token"
                    className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleRotateToken}
                    disabled={isRotating}
                    className="flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
                    data-testid="confirm-rotate-token"
                  >
                    <RefreshCw className="h-4 w-4" />
                    {isRotating ? "Rotating..." : "Rotate Token"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};
