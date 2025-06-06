#!/usr/bin/env python3
"""
🔐 Email Service for SentinelForge Password Reset
Handles sending password reset emails using SendGrid integration.
"""

import logging
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

# Email configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENTINELFORGE_FROM_EMAIL", "no-reply@sentinelforge.com")
FRONTEND_URL = os.getenv("SENTINELFORGE_FRONTEND_URL", "http://localhost:3000")

# Setup Jinja2 for email templates
template_dir = os.path.join(os.path.dirname(__file__), "email_templates")
if not os.path.exists(template_dir):
    os.makedirs(template_dir, exist_ok=True)
    logger.info(f"Created email templates directory: {template_dir}")

env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(["html", "xml"]),
)


def send_password_reset_email(email: str, username: str, reset_token: str) -> bool:
    """
    Send password reset email to user.

    Args:
        email: User's email address
        username: User's username
        reset_token: Secure reset token

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not SENDGRID_API_KEY:
        logger.error(
            "SENDGRID_API_KEY not configured. Cannot send password reset email."
        )
        return False

    try:
        # Generate reset URL
        reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"

        # Render email template
        try:
            template = env.get_template("password_reset.html")
            html_content = template.render(
                username=username,
                reset_url=reset_url,
                frontend_url=FRONTEND_URL,
            )
        except Exception as e:
            logger.warning(f"Failed to load HTML template, using fallback: {e}")
            html_content = create_fallback_html_content(username, reset_url)

        # Create email message
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=email,
            subject="SentinelForge - Password Reset Request",
            html_content=html_content,
        )

        # Send email via SendGrid
        client = SendGridAPIClient(SENDGRID_API_KEY)
        response = client.send(message)

        if response.status_code >= 300:
            logger.error(f"SendGrid error: {response.status_code} - {response.body}")
            return False

        logger.info(f"Password reset email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        return False


def create_fallback_html_content(username: str, reset_url: str) -> str:
    """Create fallback HTML content if template is not available."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SentinelForge - Password Reset</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .button {{ 
                display: inline-block; 
                background: #6366f1; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 20px 0;
            }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ SentinelForge</h1>
                <h2>Password Reset Request</h2>
            </div>
            <div class="content">
                <p>Hello {username},</p>
                <p>We received a request to reset your password for your SentinelForge account.</p>
                <p>Click the button below to reset your password:</p>
                <p><a href="{reset_url}" class="button">Reset Password</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p><strong>This link will expire in 1 hour for security reasons.</strong></p>
                <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
            </div>
            <div class="footer">
                <p>© 2024 SentinelForge. All rights reserved.</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """


def send_password_reset_confirmation_email(email: str, username: str) -> bool:
    """
    Send confirmation email after successful password reset.

    Args:
        email: User's email address
        username: User's username

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY not configured. Cannot send confirmation email.")
        return False

    try:
        # Create confirmation email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SentinelForge - Password Reset Successful</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .success {{ background: #10b981; color: white; padding: 10px; border-radius: 5px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ SentinelForge</h1>
                    <h2>Password Reset Successful</h2>
                </div>
                <div class="content">
                    <div class="success">
                        <p><strong>✅ Your password has been successfully reset!</strong></p>
                    </div>
                    <p>Hello {username},</p>
                    <p>This email confirms that your SentinelForge account password has been successfully changed.</p>
                    <p>If you did not make this change, please contact your administrator immediately.</p>
                    <p>You can now log in to SentinelForge using your new password:</p>
                    <p><a href="{FRONTEND_URL}/login">Login to SentinelForge</a></p>
                </div>
                <div class="footer">
                    <p>© 2024 SentinelForge. All rights reserved.</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create email message
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=email,
            subject="SentinelForge - Password Reset Successful",
            html_content=html_content,
        )

        # Send email via SendGrid
        client = SendGridAPIClient(SENDGRID_API_KEY)
        response = client.send(message)

        if response.status_code >= 300:
            logger.error(f"SendGrid error: {response.status_code} - {response.body}")
            return False

        logger.info(f"Password reset confirmation email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send password reset confirmation email to {email}: {e}"
        )
        return False


def test_email_configuration() -> bool:
    """Test if email configuration is properly set up."""
    if not SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY environment variable not set")
        return False

    logger.info("Email configuration test passed")
    return True


if __name__ == "__main__":
    # Test email configuration
    if test_email_configuration():
        print("✅ Email service configuration is valid")
    else:
        print("❌ Email service configuration is invalid")
