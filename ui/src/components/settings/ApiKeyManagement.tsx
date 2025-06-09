import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
  DialogFooter,
} from "../ui/dialog";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../ui/accordion";
import { Checkbox } from "../ui/checkbox";
import { Textarea } from "../ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "../ui/tooltip";
import {
  Key,
  Plus,
  Trash2,
  RefreshCw,
  Copy,
  Eye,
  EyeOff,
  Calendar,
  Shield,
  ChevronRight,
  ChevronLeft,
  Settings,
  CheckCircle,
  Info,
  AlertCircle,
} from "lucide-react";
import { toast } from "../../lib/toast";

interface ApiKey {
  id: string;
  name: string;
  key_preview: string;
  created_at: string;
  last_used: string | null;
  access_scope: string[];
  is_active: boolean;
}

export const ApiKeyManagement: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [showFullKey, setShowFullKey] = useState(false);

  // Multi-step form state
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    accessScope: ["read"] as string[],
    expiresIn: "never" as "30d" | "90d" | "1y" | "never",
    ipRestrictions: "",
    rateLimitTier: "standard" as "basic" | "standard" | "premium",
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Confirmation dialogs state
  const [revokeDialog, setRevokeDialog] = useState<{
    isOpen: boolean;
    keyId: string;
    keyName: string;
  }>({ isOpen: false, keyId: "", keyName: "" });

  const [rotateDialog, setRotateDialog] = useState<{
    isOpen: boolean;
    keyId: string;
    keyName: string;
  }>({ isOpen: false, keyId: "", keyName: "" });

  useEffect(() => {
    fetchApiKeys();
  }, []);

  // Form validation functions
  const validateStep1 = () => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) {
      errors.name = "API key name is required";
    } else if (formData.name.trim().length < 3) {
      errors.name = "API key name must be at least 3 characters";
    } else if (formData.name.trim().length > 50) {
      errors.name = "API key name must be less than 50 characters";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateStep2 = () => {
    const errors: Record<string, string> = {};

    if (formData.accessScope.length === 0) {
      errors.accessScope = "Please select at least one access permission";
    }

    // Validate IP restrictions format if provided
    if (formData.ipRestrictions.trim()) {
      const ipLines = formData.ipRestrictions.trim().split("\n");
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/;
      const invalidIps = ipLines.filter(
        (ip) => ip.trim() && !ipRegex.test(ip.trim()),
      );

      if (invalidIps.length > 0) {
        errors.ipRestrictions =
          "Invalid IP address format. Use format: 192.168.1.1 or 192.168.1.0/24";
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const clearFieldError = (fieldName: string) => {
    if (formErrors[fieldName]) {
      setFormErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  const fetchApiKeys = async () => {
    try {
      const response = await fetch("/api/user/api-keys", {
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.api_keys || []);
      } else {
        console.error("Failed to fetch API keys");
        toast.error("Failed to load API keys");
      }
    } catch (error) {
      console.error("Error fetching API keys:", error);
      toast.error("Error loading API keys");
    } finally {
      setLoading(false);
    }
  };

  const createApiKey = async () => {
    // Validate all steps before creating
    const step1Valid = validateStep1();
    const step2Valid = validateStep2();

    if (!step1Valid || !step2Valid) {
      toast.error(
        "Please fix the validation errors before creating the API key",
      );
      return;
    }

    setCreating(true);
    try {
      const requestBody: any = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        access_scope: formData.accessScope,
        rate_limit_tier: formData.rateLimitTier,
      };

      if (formData.expiresIn !== "never") {
        requestBody.expires_in = formData.expiresIn;
      }

      if (formData.ipRestrictions.trim()) {
        requestBody.ip_restrictions = formData.ipRestrictions.trim();
      }

      const response = await fetch("/api/user/api-keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        setNewlyCreatedKey(data.api_key);
        resetForm();
        await fetchApiKeys();
        toast.success("API key created successfully");
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to create API key");
      }
    } catch (error) {
      console.error("Error creating API key:", error);
      toast.error("Error creating API key");
    } finally {
      setCreating(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      accessScope: ["read"],
      expiresIn: "never",
      ipRestrictions: "",
      rateLimitTier: "standard",
    });
    setFormErrors({});
    setCurrentStep(1);
  };

  const confirmRevokeApiKey = (keyId: string, keyName: string) => {
    setRevokeDialog({ isOpen: true, keyId, keyName });
  };

  const revokeApiKey = async () => {
    const { keyId, keyName } = revokeDialog;
    setRevokeDialog({ isOpen: false, keyId: "", keyName: "" }); // Close dialog

    try {
      const response = await fetch(`/api/user/api-keys/${keyId}`, {
        method: "DELETE",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        await fetchApiKeys();
        toast.success(`API key "${keyName}" revoked successfully`);
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to revoke API key");
      }
    } catch (error) {
      console.error("Error revoking API key:", error);
      toast.error("Error revoking API key");
    }
  };

  const confirmRotateApiKey = (keyId: string, keyName: string) => {
    setRotateDialog({ isOpen: true, keyId, keyName });
  };

  const rotateApiKey = async () => {
    const { keyId, keyName } = rotateDialog;
    setRotateDialog({ isOpen: false, keyId: "", keyName: "" }); // Close dialog

    try {
      const response = await fetch(`/api/user/api-keys/${keyId}/rotate`, {
        method: "POST",
        headers: {
          "X-Session-Token": localStorage.getItem("session_token") || "",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNewlyCreatedKey(data.api_key);
        await fetchApiKeys();
        toast.success(`API key "${keyName}" rotated successfully`);
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to rotate API key");
      }
    } catch (error) {
      console.error("Error rotating API key:", error);
      toast.error("Error rotating API key");
    }
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const handleScopeChange = (scope: string, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      accessScope: checked
        ? [...prev.accessScope, scope]
        : prev.accessScope.filter((s) => s !== scope),
    }));
  };

  const nextStep = () => {
    if (currentStep === 1) {
      if (!validateStep1()) {
        return;
      }
    } else if (currentStep === 2) {
      if (!validateStep2()) {
        return;
      }
    }
    setCurrentStep((prev) => Math.min(prev + 1, 3));
  };

  const prevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleDialogClose = () => {
    setShowCreateDialog(false);
    resetForm();
  };

  const getStepTitle = (step: number) => {
    switch (step) {
      case 1:
        return "Basic Information";
      case 2:
        return "Access & Security";
      case 3:
        return "Review & Create";
      default:
        return "";
    }
  };

  if (loading) {
    return (
      <Card data-testid="api-key-management">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Keys
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
    <Card data-testid="api-key-management">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Keys
          </div>
          <Dialog open={showCreateDialog} onOpenChange={handleDialogClose}>
            <DialogTrigger asChild>
              <Button size="sm" data-testid="create-api-key-button">
                <Plus className="h-4 w-4 mr-2" />
                Create Key
              </Button>
            </DialogTrigger>
            <DialogContent className="w-full max-w-screen-sm sm:max-w-2xl max-h-[95vh] overflow-y-auto">
              <DialogHeader className="pb-4">
                <DialogTitle className="flex items-center gap-2 text-lg sm:text-xl">
                  <Key className="h-5 w-5" />
                  Create New API Key
                </DialogTitle>
                <div className="flex items-center gap-2 mt-3">
                  {[1, 2, 3].map((step) => (
                    <div key={step} className="flex items-center">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          step === currentStep
                            ? "bg-blue-600 text-white"
                            : step < currentStep
                              ? "bg-green-600 text-white"
                              : "bg-gray-200 text-gray-600"
                        }`}
                      >
                        {step < currentStep ? (
                          <CheckCircle className="h-4 w-4" />
                        ) : (
                          step
                        )}
                      </div>
                      {step < 3 && (
                        <div
                          className={`w-12 h-1 mx-2 ${
                            step < currentStep ? "bg-green-600" : "bg-gray-200"
                          }`}
                        />
                      )}
                    </div>
                  ))}
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  Step {currentStep} of 3: {getStepTitle(currentStep)}
                </p>
              </DialogHeader>

              <div className="space-y-6 mt-6">
                {/* Step 1: Basic Information */}
                {currentStep === 1 && (
                  <div className="space-y-4 sm:space-y-6">
                    <div className="space-y-3">
                      <Label htmlFor="key-name" className="text-sm font-medium">
                        Key Name *
                      </Label>
                      <Input
                        id="key-name"
                        value={formData.name}
                        onChange={(e) => {
                          setFormData((prev) => ({
                            ...prev,
                            name: e.target.value,
                          }));
                          clearFieldError("name");
                        }}
                        placeholder="e.g., Production API Access"
                        data-testid="api-key-name-input"
                        className={`min-h-[44px] sm:min-h-[40px] ${formErrors.name ? "border-red-500" : ""}`}
                        aria-invalid={!!formErrors.name}
                        aria-describedby={
                          formErrors.name ? "key-name-error" : "key-name-help"
                        }
                      />
                      {formErrors.name && (
                        <p
                          id="key-name-error"
                          className="text-sm text-red-600 mt-1"
                        >
                          {formErrors.name}
                        </p>
                      )}
                      <p id="key-name-help" className="text-xs text-gray-500">
                        Choose a descriptive name to help identify this key's
                        purpose
                      </p>
                    </div>

                    <div className="space-y-3">
                      <Label
                        htmlFor="key-description"
                        className="text-sm font-medium"
                      >
                        Description (Optional)
                      </Label>
                      <Textarea
                        id="key-description"
                        value={formData.description}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            description: e.target.value,
                          }))
                        }
                        placeholder="Describe what this API key will be used for..."
                        rows={3}
                        className="min-h-[88px] resize-none"
                      />
                      <p className="text-xs text-gray-500">
                        Provide additional context about this key's intended use
                      </p>
                    </div>
                  </div>
                )}

                {/* Step 2: Access & Security */}
                {currentStep === 2 && (
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <Label className="text-sm font-medium">
                        Access Permissions *
                      </Label>
                      <div
                        className="space-y-3"
                        role="group"
                        aria-describedby={
                          formErrors.accessScope
                            ? "access-scope-error"
                            : "access-scope-help"
                        }
                      >
                        {[
                          {
                            id: "read",
                            label: "Read",
                            description: "View alerts, IOCs, and feeds",
                          },
                          {
                            id: "write",
                            label: "Write",
                            description: "Create and update data",
                          },
                          {
                            id: "delete",
                            label: "Delete",
                            description: "Remove alerts and IOCs",
                          },
                          {
                            id: "admin",
                            label: "Admin",
                            description: "Manage feeds and system settings",
                          },
                        ].map((scope) => (
                          <div
                            key={scope.id}
                            className="flex items-start space-x-3"
                          >
                            <Checkbox
                              id={scope.id}
                              checked={formData.accessScope.includes(scope.id)}
                              onCheckedChange={(checked) => {
                                handleScopeChange(scope.id, checked as boolean);
                                clearFieldError("accessScope");
                              }}
                            />
                            <div className="space-y-1">
                              <Label
                                htmlFor={scope.id}
                                className="text-sm font-medium"
                              >
                                {scope.label}
                              </Label>
                              <p className="text-xs text-gray-500">
                                {scope.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                      {formErrors.accessScope && (
                        <p
                          id="access-scope-error"
                          className="text-sm text-red-600 mt-1"
                        >
                          {formErrors.accessScope}
                        </p>
                      )}
                      <p
                        id="access-scope-help"
                        className="text-xs text-gray-500"
                      >
                        Select the permissions this API key should have
                      </p>
                    </div>

                    <Accordion type="single" collapsible className="w-full">
                      <AccordionItem value="advanced-security">
                        <AccordionTrigger className="text-sm font-medium">
                          <div className="flex items-center gap-2">
                            <Settings className="h-4 w-4" />
                            Advanced Security Options
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="space-y-4">
                          <div className="space-y-3">
                            <Label className="text-sm font-medium">
                              Expiration
                            </Label>
                            <select
                              value={formData.expiresIn}
                              onChange={(e) =>
                                setFormData((prev) => ({
                                  ...prev,
                                  expiresIn: e.target.value as any,
                                }))
                              }
                              className="w-full p-2 border rounded-md text-sm"
                            >
                              <option value="30d">30 days</option>
                              <option value="90d">90 days</option>
                              <option value="1y">1 year</option>
                              <option value="never">Never expires</option>
                            </select>
                          </div>

                          <div className="space-y-3">
                            <Label className="text-sm font-medium">
                              Rate Limit Tier
                            </Label>
                            <select
                              value={formData.rateLimitTier}
                              onChange={(e) =>
                                setFormData((prev) => ({
                                  ...prev,
                                  rateLimitTier: e.target.value as any,
                                }))
                              }
                              className="w-full p-2 border rounded-md text-sm"
                            >
                              <option value="basic">Basic (100 req/min)</option>
                              <option value="standard">
                                Standard (500 req/min)
                              </option>
                              <option value="premium">
                                Premium (1000 req/min)
                              </option>
                            </select>
                          </div>

                          <div className="space-y-3">
                            <Label
                              htmlFor="ip-restrictions"
                              className="text-sm font-medium"
                            >
                              IP Restrictions (Optional)
                            </Label>
                            <Textarea
                              id="ip-restrictions"
                              value={formData.ipRestrictions}
                              onChange={(e) => {
                                setFormData((prev) => ({
                                  ...prev,
                                  ipRestrictions: e.target.value,
                                }));
                                clearFieldError("ipRestrictions");
                              }}
                              placeholder="192.168.1.0/24&#10;10.0.0.1"
                              rows={3}
                              className={
                                formErrors.ipRestrictions
                                  ? "border-red-500"
                                  : ""
                              }
                              aria-invalid={!!formErrors.ipRestrictions}
                              aria-describedby={
                                formErrors.ipRestrictions
                                  ? "ip-restrictions-error"
                                  : "ip-restrictions-help"
                              }
                            />
                            {formErrors.ipRestrictions && (
                              <p
                                id="ip-restrictions-error"
                                className="text-sm text-red-600 mt-1"
                              >
                                {formErrors.ipRestrictions}
                              </p>
                            )}
                            <p
                              id="ip-restrictions-help"
                              className="text-xs text-gray-500"
                            >
                              Enter IP addresses or CIDR blocks, one per line
                            </p>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </div>
                )}

                {/* Step 3: Review & Create */}
                {currentStep === 3 && (
                  <div className="space-y-6">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                        <div>
                          <h4 className="font-medium text-blue-900">
                            Review Your API Key Configuration
                          </h4>
                          <p className="text-sm text-blue-700 mt-1">
                            Please review the settings below before creating
                            your API key.
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm font-medium text-gray-700">
                            Name
                          </Label>
                          <p className="text-sm text-gray-900 mt-1">
                            {formData.name}
                          </p>
                        </div>
                        <div>
                          <Label className="text-sm font-medium text-gray-700">
                            Expiration
                          </Label>
                          <p className="text-sm text-gray-900 mt-1">
                            {formData.expiresIn === "never"
                              ? "Never expires"
                              : formData.expiresIn}
                          </p>
                        </div>
                      </div>

                      {formData.description && (
                        <div>
                          <Label className="text-sm font-medium text-gray-700">
                            Description
                          </Label>
                          <p className="text-sm text-gray-900 mt-1">
                            {formData.description}
                          </p>
                        </div>
                      )}

                      <div>
                        <Label className="text-sm font-medium text-gray-700">
                          Access Permissions
                        </Label>
                        <div className="flex gap-2 mt-1">
                          {formData.accessScope.map((scope) => (
                            <Badge key={scope} variant="outline">
                              {scope}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm font-medium text-gray-700">
                          Rate Limit
                        </Label>
                        <p className="text-sm text-gray-900 mt-1 capitalize">
                          {formData.rateLimitTier}
                        </p>
                      </div>

                      {formData.ipRestrictions && (
                        <div>
                          <Label className="text-sm font-medium text-gray-700">
                            IP Restrictions
                          </Label>
                          <pre className="text-sm text-gray-900 mt-1 bg-gray-50 p-2 rounded border">
                            {formData.ipRestrictions}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Navigation Buttons */}
                <div className="flex flex-col sm:flex-row sm:justify-between gap-3 pt-6 border-t">
                  <div className="order-2 sm:order-1">
                    {currentStep > 1 && (
                      <Button
                        variant="outline"
                        onClick={prevStep}
                        className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
                      >
                        <ChevronLeft className="h-4 w-4 mr-2" />
                        Previous
                      </Button>
                    )}
                  </div>
                  <div className="flex flex-col-reverse sm:flex-row gap-3 sm:gap-2 order-1 sm:order-2">
                    <Button
                      variant="outline"
                      onClick={handleDialogClose}
                      className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
                    >
                      Cancel
                    </Button>
                    {currentStep < 3 ? (
                      <Button
                        onClick={nextStep}
                        className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
                      >
                        Next
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </Button>
                    ) : (
                      <Button
                        onClick={createApiKey}
                        disabled={creating}
                        data-testid="confirm-create-key"
                        className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
                      >
                        {creating ? "Creating..." : "Create API Key"}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Newly Created Key Display */}
        {newlyCreatedKey && (
          <Card className="shadow-md border-green-200 bg-green-50 dark:bg-green-900/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-800 dark:text-green-200">
                <Shield className="h-5 w-5 text-green-600" />
                New API Key Created
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <Label className="text-sm font-medium text-green-800 dark:text-green-200">
                  Your New API Key
                </Label>
                <div className="flex items-center gap-2">
                  <CopyableInput
                    value={
                      showFullKey
                        ? newlyCreatedKey
                        : `${newlyCreatedKey.substring(0, 8)}...`
                    }
                    aria-label="New API key"
                    data-testid="new-api-key-display"
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowFullKey(!showFullKey)}
                    aria-label={
                      showFullKey ? "Hide API key" : "Show full API key"
                    }
                    data-testid="toggle-key-visibility"
                  >
                    {showFullKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-green-700 dark:text-green-300">
                  Save this key securely. You won't be able to see it again.
                </p>
              </div>
            </CardContent>
            <CardFooter>
              <Button size="sm" onClick={() => setNewlyCreatedKey(null)}>
                Dismiss
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* API Keys List */}
        {apiKeys.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Key className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No API keys created yet</p>
            <p className="text-sm">Create your first API key to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {apiKeys.map((key) => (
              <Card key={key.id} className="shadow-md">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Header - stacked on mobile */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-medium truncate">{key.name}</span>
                        <Badge
                          variant={key.is_active ? "default" : "secondary"}
                          className="flex-shrink-0"
                        >
                          {key.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => confirmRotateApiKey(key.id, key.name)}
                          aria-label={`Rotate API key ${key.name}`}
                          data-testid={`rotate-key-${key.id}`}
                          className="flex items-center gap-1 min-h-[44px] sm:min-h-[36px]"
                        >
                          <RefreshCw className="h-4 w-4" />
                          <span className="sm:hidden">Rotate</span>
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => confirmRevokeApiKey(key.id, key.name)}
                          className="text-red-600 hover:text-red-700 flex items-center gap-1 min-h-[44px] sm:min-h-[36px]"
                          aria-label={`Revoke API key ${key.name}`}
                          data-testid={`revoke-key-${key.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                          <span className="sm:hidden">Revoke</span>
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <Label className="text-sm font-medium text-gray-700 mb-2 block">
                          API Key Preview
                        </Label>
                        <CopyableInput
                          value={key.key_preview}
                          aria-label={`API key preview for ${key.name}`}
                          data-testid={`api-key-preview-${key.id}`}
                          className="w-full max-w-md"
                        />
                      </div>

                      {/* Metadata - stacked on mobile */}
                      <div className="space-y-2 sm:space-y-0 sm:flex sm:items-center sm:gap-4 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3 flex-shrink-0" />
                          <span>Created {formatDate(key.created_at)}</span>
                        </div>
                        {key.last_used && (
                          <div className="flex items-center gap-1">
                            <span className="w-3 h-3 flex-shrink-0"></span>
                            <span>Last used {formatDate(key.last_used)}</span>
                          </div>
                        )}
                      </div>

                      {/* Access scope badges */}
                      <div className="flex flex-wrap gap-1">
                        {key.access_scope.map((scope) => (
                          <Badge
                            key={scope}
                            variant="outline"
                            className="text-xs"
                          >
                            {scope}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Help Text */}
        <div className="pt-6 border-t">
          <p className="text-xs text-gray-500">
            API keys provide programmatic access to SentinelForge. Keep them
            secure and rotate them regularly. Use the API documentation to learn
            how to authenticate your requests.
          </p>
        </div>
      </CardContent>

      {/* Revoke Confirmation Dialog */}
      <Dialog
        open={revokeDialog.isOpen}
        onOpenChange={(open) =>
          setRevokeDialog((prev) => ({ ...prev, isOpen: open }))
        }
      >
        <DialogContent className="w-full max-w-screen-sm sm:max-w-md">
          <DialogHeader className="pb-4">
            <DialogTitle className="flex items-center gap-2 text-lg sm:text-xl">
              <AlertCircle className="h-5 w-5 text-red-500" />
              Confirm API Key Revocation
            </DialogTitle>
            <DialogDescription className="text-sm sm:text-base">
              This action will permanently revoke the API key "
              {revokeDialog.keyName}" and cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="space-y-2">
                  <h4 className="font-medium text-red-900">Warning</h4>
                  <ul className="text-sm text-red-800 space-y-1">
                    <li>• The API key will be immediately invalidated</li>
                    <li>• Any applications using this key will lose access</li>
                    <li>• This action cannot be reversed</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3 sm:gap-2">
            <Button
              variant="outline"
              onClick={() =>
                setRevokeDialog({ isOpen: false, keyId: "", keyName: "" })
              }
              data-testid="cancel-revoke-key"
              className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={revokeApiKey}
              className="flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
              data-testid="confirm-revoke-key"
            >
              <Trash2 className="h-4 w-4" />
              Revoke Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rotate Confirmation Dialog */}
      <Dialog
        open={rotateDialog.isOpen}
        onOpenChange={(open) =>
          setRotateDialog((prev) => ({ ...prev, isOpen: open }))
        }
      >
        <DialogContent className="w-full max-w-screen-sm sm:max-w-md">
          <DialogHeader className="pb-4">
            <DialogTitle className="flex items-center gap-2 text-lg sm:text-xl">
              <RefreshCw className="h-5 w-5 text-amber-500" />
              Confirm API Key Rotation
            </DialogTitle>
            <DialogDescription className="text-sm sm:text-base">
              This will generate a new API key for "{rotateDialog.keyName}" and
              invalidate the current one.
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
                    <li>• A new API key will be generated</li>
                    <li>• The old key will be immediately invalidated</li>
                    <li>
                      • You'll need to update applications with the new key
                    </li>
                    <li>• The new key will have the same permissions</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3 sm:gap-2">
            <Button
              variant="outline"
              onClick={() =>
                setRotateDialog({ isOpen: false, keyId: "", keyName: "" })
              }
              data-testid="cancel-rotate-key"
              className="w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
            >
              Cancel
            </Button>
            <Button
              onClick={rotateApiKey}
              className="flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] sm:min-h-[40px]"
              data-testid="confirm-rotate-key"
            >
              <RefreshCw className="h-4 w-4" />
              Rotate Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};
