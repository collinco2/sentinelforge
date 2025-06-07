/**
 * 🔐 Password Reset Request Page - Email Input Form
 *
 * Allows users to request a password reset by entering their email address.
 * Provides secure password reset functionality with user-friendly interface.
 */

import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Alert, AlertDescription } from "../components/ui/alert";
import { Loader2, Shield, ArrowLeft, Mail, CheckCircle } from "lucide-react";

export default function PasswordResetRequestPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    // Basic email validation
    if (!email || !email.includes("@")) {
      setError("Please enter a valid email address");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/request-password-reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });

      if (response.ok) {
        setSuccess(true);
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Failed to send reset email");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
        <div className="w-full max-w-md space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="flex justify-center">
              <Shield className="h-12 w-12 text-purple-500" />
            </div>
            <h1 className="text-3xl font-bold text-white">SentinelForge</h1>
            <p className="text-slate-400">Password Reset Request</p>
          </div>

          {/* Success Card */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <CheckCircle className="h-16 w-16 text-green-500" />
              </div>
              <CardTitle className="text-white">Check Your Email</CardTitle>
              <CardDescription className="text-slate-300">
                Reset instructions have been sent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                <p className="text-green-300 text-sm text-center">
                  If an account with <strong>{email}</strong> exists, we've sent
                  password reset instructions to that email address.
                </p>
              </div>

              <div className="space-y-3 text-sm text-slate-400">
                <div className="flex items-start space-x-2">
                  <Mail className="h-4 w-4 mt-0.5 text-purple-400" />
                  <p>Check your email inbox and spam folder</p>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400 mt-0.5">⏰</span>
                  <p>The reset link will expire in 1 hour</p>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-purple-400 mt-0.5">🔒</span>
                  <p>Click the link in the email to reset your password</p>
                </div>
              </div>

              <div className="pt-4 space-y-3">
                <Button
                  onClick={() => {
                    setSuccess(false);
                    setEmail("");
                  }}
                  variant="outline"
                  className="w-full border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white"
                >
                  Send Another Reset Email
                </Button>

                <Link to="/login">
                  <Button
                    variant="ghost"
                    className="w-full text-slate-400 hover:text-white hover:bg-slate-700"
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Login
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center text-sm text-slate-400">
            <p>© 2024 SentinelForge. All rights reserved.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <Shield className="h-12 w-12 text-purple-500" />
          </div>
          <h1 className="text-3xl font-bold text-white">SentinelForge</h1>
          <p className="text-slate-400">Reset Your Password</p>
        </div>

        {/* Reset Request Form */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Forgot Password?</CardTitle>
            <CardDescription className="text-slate-300">
              Enter your email address and we'll send you a link to reset your
              password.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert className="mb-4 border-red-500/50 bg-red-500/10">
                <AlertDescription className="text-red-300">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label
                  htmlFor="email"
                  className="text-sm font-medium text-slate-300"
                >
                  Email Address
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                  className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-400 focus:border-purple-500"
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                disabled={isLoading || !email}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending Reset Email...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    Send Reset Email
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <Link to="/login">
                <Button
                  variant="ghost"
                  className="text-slate-400 hover:text-white hover:bg-slate-700"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Login
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Security Notice */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <p className="text-xs text-slate-400 text-center">
            🔒 For security reasons, we don't reveal whether an email address is
            registered. If you don't receive an email, please check your spam
            folder or contact your administrator.
          </p>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-slate-400">
          <p>© 2024 SentinelForge. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
