/**
 * Form Validation Example Component
 * Demonstrates best practices for inline validation with ARIA compliance
 */

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { Checkbox } from "./ui/checkbox";
import { Alert, AlertDescription } from "./ui/alert";
import { CheckCircle, AlertCircle, Mail, User, Lock } from "lucide-react";

interface FormData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  bio: string;
  terms: boolean;
}

interface FormErrors {
  [key: string]: string;
}

export const FormValidationExample: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
    bio: "",
    terms: false,
  });

  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Validation functions
  const validateEmail = (email: string): string => {
    if (!email.trim()) {
      return "Email address is required";
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return "Please enter a valid email address";
    }
    return "";
  };

  const validateUsername = (username: string): string => {
    if (!username.trim()) {
      return "Username is required";
    }
    if (username.trim().length < 3) {
      return "Username must be at least 3 characters";
    }
    if (username.trim().length > 20) {
      return "Username must be less than 20 characters";
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return "Username can only contain letters, numbers, and underscores";
    }
    return "";
  };

  const validatePassword = (password: string): string => {
    if (!password) {
      return "Password is required";
    }
    if (password.length < 8) {
      return "Password must be at least 8 characters";
    }
    if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
      return "Password must contain at least one uppercase letter, one lowercase letter, and one number";
    }
    return "";
  };

  const validateConfirmPassword = (
    confirmPassword: string,
    password: string,
  ): string => {
    if (!confirmPassword) {
      return "Please confirm your password";
    }
    if (confirmPassword !== password) {
      return "Passwords do not match";
    }
    return "";
  };

  const validateTerms = (terms: boolean): string => {
    if (!terms) {
      return "You must accept the terms and conditions";
    }
    return "";
  };

  // Clear individual field error
  const clearFieldError = (fieldName: string) => {
    if (formErrors[fieldName]) {
      setFormErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  // Handle field changes with real-time validation clearing
  const handleFieldChange = (
    fieldName: keyof FormData,
    value: string | boolean,
  ) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    clearFieldError(fieldName);
  };

  // Validate all fields
  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    const emailError = validateEmail(formData.email);
    if (emailError) errors.email = emailError;

    const usernameError = validateUsername(formData.username);
    if (usernameError) errors.username = usernameError;

    const passwordError = validatePassword(formData.password);
    if (passwordError) errors.password = passwordError;

    const confirmPasswordError = validateConfirmPassword(
      formData.confirmPassword,
      formData.password,
    );
    if (confirmPasswordError) errors.confirmPassword = confirmPasswordError;

    const termsError = validateTerms(formData.terms);
    if (termsError) errors.terms = termsError;

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    // Simulate API call
    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setSubmitSuccess(true);

      // Reset form
      setFormData({
        email: "",
        username: "",
        password: "",
        confirmPassword: "",
        bio: "",
        terms: false,
      });
      setFormErrors({});

      // Hide success message after 3 seconds
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (error) {
      setFormErrors({ general: "An error occurred. Please try again." });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Form Validation Example
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Demonstrates inline validation with ARIA compliance and real-time
            error clearing.
          </p>
        </CardHeader>
        <CardContent>
          {submitSuccess && (
            <Alert className="mb-6">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Form submitted successfully! All validation patterns are working
                correctly.
              </AlertDescription>
            </Alert>
          )}

          {formErrors.general && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{formErrors.general}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">
                Email Address *
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleFieldChange("email", e.target.value)}
                  placeholder="Enter your email address"
                  className={`pl-10 ${formErrors.email ? "border-red-500" : ""}`}
                  aria-invalid={!!formErrors.email}
                  aria-describedby={
                    formErrors.email ? "email-error" : "email-help"
                  }
                />
              </div>
              {formErrors.email && (
                <p id="email-error" className="text-sm text-red-600 mt-1">
                  {formErrors.email}
                </p>
              )}
              <p id="email-help" className="text-xs text-muted-foreground">
                We'll use this email to send you important updates.
              </p>
            </div>

            {/* Username Field */}
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium">
                Username *
              </Label>
              <Input
                id="username"
                value={formData.username}
                onChange={(e) => handleFieldChange("username", e.target.value)}
                placeholder="Choose a unique username"
                className={formErrors.username ? "border-red-500" : ""}
                aria-invalid={!!formErrors.username}
                aria-describedby={
                  formErrors.username
                    ? "username-error username-help"
                    : "username-help"
                }
              />
              {formErrors.username && (
                <p id="username-error" className="text-sm text-red-600 mt-1">
                  {formErrors.username}
                </p>
              )}
              <p id="username-help" className="text-xs text-muted-foreground">
                3-20 characters, letters, numbers, and underscores only.
              </p>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                Password *
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) =>
                    handleFieldChange("password", e.target.value)
                  }
                  placeholder="Create a strong password"
                  className={`pl-10 ${formErrors.password ? "border-red-500" : ""}`}
                  aria-invalid={!!formErrors.password}
                  aria-describedby={
                    formErrors.password
                      ? "password-error password-help"
                      : "password-help"
                  }
                />
              </div>
              {formErrors.password && (
                <p id="password-error" className="text-sm text-red-600 mt-1">
                  {formErrors.password}
                </p>
              )}
              <p id="password-help" className="text-xs text-muted-foreground">
                At least 8 characters with uppercase, lowercase, and number.
              </p>
            </div>

            {/* Confirm Password Field */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium">
                Confirm Password *
              </Label>
              <Input
                id="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) =>
                  handleFieldChange("confirmPassword", e.target.value)
                }
                placeholder="Confirm your password"
                className={formErrors.confirmPassword ? "border-red-500" : ""}
                aria-invalid={!!formErrors.confirmPassword}
                aria-describedby={
                  formErrors.confirmPassword
                    ? "confirm-password-error"
                    : undefined
                }
              />
              {formErrors.confirmPassword && (
                <p
                  id="confirm-password-error"
                  className="text-sm text-red-600 mt-1"
                >
                  {formErrors.confirmPassword}
                </p>
              )}
            </div>

            {/* Bio Field (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="bio" className="text-sm font-medium">
                Bio (Optional)
              </Label>
              <Textarea
                id="bio"
                value={formData.bio}
                onChange={(e) => handleFieldChange("bio", e.target.value)}
                placeholder="Tell us about yourself..."
                rows={3}
                aria-describedby="bio-help"
              />
              <p id="bio-help" className="text-xs text-muted-foreground">
                Share a brief description about yourself (optional).
              </p>
            </div>

            {/* Terms Checkbox */}
            <div className="space-y-2">
              <div className="flex items-start space-x-3">
                <Checkbox
                  id="terms"
                  checked={formData.terms}
                  onCheckedChange={(checked) =>
                    handleFieldChange("terms", checked as boolean)
                  }
                  aria-invalid={!!formErrors.terms}
                  aria-describedby={
                    formErrors.terms ? "terms-error" : undefined
                  }
                />
                <div className="space-y-1">
                  <Label htmlFor="terms" className="text-sm font-medium">
                    I accept the terms and conditions *
                  </Label>
                  {formErrors.terms && (
                    <p id="terms-error" className="text-sm text-red-600">
                      {formErrors.terms}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Creating Account..." : "Create Account"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default FormValidationExample;
