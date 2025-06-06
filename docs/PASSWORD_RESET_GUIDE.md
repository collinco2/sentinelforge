# 🔐 SentinelForge Password Reset System

A complete email-based password reset and account recovery system for SentinelForge with secure token generation, email delivery, and user-friendly interface.

## ✨ Features

- **🔒 Secure Token Generation**: Cryptographically secure tokens with 1-hour expiry
- **📧 Email Integration**: SendGrid-powered email delivery with professional templates
- **🎨 User-Friendly Interface**: Modern React components with password strength indicators
- **🛡️ Security-First**: Rate limiting, audit logging, and comprehensive validation
- **🧪 Comprehensive Testing**: Full test suite for backend functionality

## 🚀 Quick Start

### 1. **Access Password Reset**
- Go to the login page: `http://localhost:3000/login`
- Click **"Forgot your password?"** link
- Enter your email address and click **"Send Reset Email"**

### 2. **Check Your Email**
- Look for an email from SentinelForge with reset instructions
- Click the **"Reset Password"** button in the email
- Or copy/paste the reset link into your browser

### 3. **Set New Password**
- Enter your new password (minimum 8 characters)
- Confirm the password
- Click **"Reset Password"**
- You'll be redirected to login with your new password

## 🔧 Configuration

### Email Setup (Required)

1. **Get SendGrid API Key**:
   ```bash
   # Sign up at https://sendgrid.com
   # Create an API key with Mail Send permissions
   ```

2. **Set Environment Variables**:
   ```bash
   export SENDGRID_API_KEY="your_sendgrid_api_key_here"
   export SENTINELFORGE_FROM_EMAIL="no-reply@yourdomain.com"
   export SENTINELFORGE_FRONTEND_URL="http://localhost:3000"
   ```

3. **Or Create .env File**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

### Test Email Configuration
```bash
python3 -c "from email_service import test_email_configuration; print('✅ Email configured' if test_email_configuration() else '❌ Email not configured')"
```

## 🔗 API Endpoints

### Request Password Reset
```bash
POST /api/request-password-reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

### Reset Password
```bash
POST /api/reset-password
Content-Type: application/json

{
  "token": "secure_reset_token_from_email",
  "new_password": "newSecurePassword123"
}
```

**Response:**
```json
{
  "message": "Password has been successfully reset. You can now log in with your new password."
}
```

## 🎨 Frontend Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/forgot-password` | `PasswordResetRequestPage` | Email input form |
| `/reset-password?token=...` | `PasswordResetPage` | New password form |

## 🔒 Security Features

### Token Security
- **Cryptographically Secure**: Uses `secrets.token_urlsafe(32)` for token generation
- **Time-Limited**: 1-hour expiry for all reset tokens
- **Single-Use**: Tokens are invalidated after successful password reset
- **IP Tracking**: Logs IP addresses for audit purposes

### Password Requirements
- **Minimum Length**: 8 characters
- **Strength Indicator**: Real-time password strength feedback
- **Confirmation**: Double-entry password confirmation

### Rate Limiting & Abuse Prevention
- **Email Enumeration Protection**: Same response for valid/invalid emails
- **Audit Logging**: All password reset activities are logged
- **Token Validation**: Server-side validation of all tokens and inputs

## 🧪 Testing

### Run Password Reset Tests
```bash
python3 test_auth_reset.py
```

### Manual Testing
```bash
# Test password reset request
curl -X POST http://localhost:5059/api/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst1@example.com"}'

# Test with demo user email (if configured)
curl -X POST http://localhost:5059/api/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@sentinelforge.com"}'
```

## 📧 Email Templates

### Password Reset Email Features
- **Professional Design**: Modern, responsive HTML template
- **Security Information**: Clear expiry time and security notices
- **Accessibility**: ARIA labels and screen reader friendly
- **Branding**: SentinelForge branding and styling
- **Fallback Support**: Plain text version for email clients

### Email Template Location
```
email_templates/
├── password_reset.html    # Main reset email template
└── (future templates)     # Additional email templates
```

## 🛠️ Troubleshooting

### Common Issues

1. **Email Not Received**
   - Check spam/junk folder
   - Verify SendGrid API key is configured
   - Check email service logs for errors

2. **Invalid Reset Token**
   - Token may have expired (1-hour limit)
   - Token may have already been used
   - Request a new password reset

3. **Password Reset Fails**
   - Check password meets minimum requirements
   - Ensure passwords match in confirmation field
   - Verify token is still valid

### Debug Commands
```bash
# Check if email service is configured
python3 -c "from email_service import test_email_configuration; test_email_configuration()"

# Check database tables
sqlite3 ioc_store.db "SELECT * FROM password_reset_tokens ORDER BY created_at DESC LIMIT 5;"

# View API server logs
tail -f api_server.log
```

## 🔄 Integration with Existing System

### Database Schema
The password reset system adds one new table:
```sql
CREATE TABLE password_reset_tokens (
    token_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT 0,
    used_at TIMESTAMP NULL,
    ip_address TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
```

### Authentication Integration
- Uses existing `users` table and authentication system
- Integrates with current password hashing (SHA-256 + salt)
- Maintains compatibility with existing login flow
- Supports all user roles (admin, analyst, auditor, viewer)

## 📝 Demo Users

For testing, you can use these demo accounts:

| Username | Email | Role |
|----------|-------|------|
| `admin` | `admin@sentinelforge.com` | Administrator |
| `analyst1` | `analyst1@sentinelforge.com` | Analyst |
| `auditor1` | `auditor1@sentinelforge.com` | Auditor |
| `viewer1` | `viewer1@sentinelforge.com` | Viewer |

*Note: Demo emails may not be configured in the database. Update user emails in the database for testing.*

## 🎯 Next Steps

1. **Configure SendGrid**: Set up your SendGrid account and API key
2. **Test Email Flow**: Send a test password reset email
3. **Customize Templates**: Modify email templates to match your branding
4. **Set Up Monitoring**: Monitor password reset usage and potential abuse
5. **Documentation**: Train users on the new password reset process

---

**🛡️ SentinelForge Password Reset System - Secure, User-Friendly, Production-Ready**
