# 🔧 SentinelForge Settings Page Documentation

## Overview

The Settings page provides a comprehensive, centralized interface for authenticated users to manage their personal preferences, security settings, and API access within SentinelForge.

## 🎯 Features Implemented

### ✅ 1. Layout & Routing
- **Route**: `/settings` added to React Router configuration
- **Sidebar Navigation**: "Settings" menu item with Settings icon from Lucide
- **Layout**: Uses `DashboardLayout` with responsive two-column grid
- **Page Title**: "Settings" with descriptive subtitle

### ✅ 2. Authentication Tokens (`TokenSettings.tsx`)
- **Current Token Info**: Displays issued date, expiration, and token ID
- **Token Status**: Shows validity with color-coded badges
- **Expiration Warning**: Alerts when token expires within 24 hours
- **Token Rotation**: 
  - "Rotate Token" button calls `POST /api/auth/rotate-token`
  - Automatically updates stored session token
  - Shows success/error feedback via toast notifications

### ✅ 3. UI Preferences (`UIPreferences.tsx`)
- **Theme Selector**: Light, Dark, System Default options
  - Uses radio group for selection
  - Applies theme changes immediately via Tailwind dark mode
  - Persists to localStorage
- **Table Density**: Compact vs Comfortable options
- **Default Landing Page**: Dropdown with available pages
  - Dashboard, IOC Management, Feed Management, Alerts, Reports
- **Real-time Preview**: Shows current settings summary

### ✅ 4. Notification Preferences (`NotificationSettings.tsx`)
- **Email Alerts**: Toggle for critical alerts and security events
- **Slack Notifications**: Toggle for Slack channel integration
- **Weekly Summary**: Toggle for digest emails
- **Backend Integration**: 
  - Calls `PATCH /api/user/preferences` for server sync
  - Falls back to localStorage if API unavailable
  - Real-time save with visual feedback

### ✅ 5. API Key Management (`ApiKeyManagement.tsx`)
- **List Existing Keys**: Shows name, preview, creation date, last used
- **Create New Keys**: 
  - Modal dialog with name input
  - Calls `POST /api/user/api-keys`
  - Shows full key once (with show/hide toggle)
  - Copy to clipboard functionality
- **Key Operations**:
  - **Rotate**: `POST /api/user/api-keys/{id}/rotate`
  - **Revoke**: `DELETE /api/user/api-keys/{id}`
  - Confirmation dialogs for destructive actions
- **Security Features**:
  - Only shows key previews (first 8 chars + ...)
  - Access scope badges
  - Active/inactive status indicators

### ✅ 6. Password Change (`PasswordChangeForm.tsx`)
- **Form Fields**: Current password, new password, confirm password
- **Password Strength Indicator**:
  - Real-time validation with visual progress bar
  - Requirements checklist (length, uppercase, lowercase, numbers, special chars)
  - Color-coded strength levels (weak/medium/strong)
- **Security Features**:
  - Show/hide password toggles for all fields
  - Password match validation
  - Prevents reusing current password
- **Backend Integration**: `POST /api/auth/change-password`
- **Error Handling**: Field-specific errors, rate limiting, network errors

### ✅ 7. Access Control & UX
- **Role-Based Access**: Restricted to Analyst, Auditor, Admin roles
- **Accessibility**: 
  - ARIA labels on all interactive elements
  - Keyboard navigation support
  - Screen reader friendly
- **Responsive Design**: Mobile-friendly layout with proper breakpoints
- **Loading States**: Spinners and disabled states during async operations
- **Toast Notifications**: Success/error feedback for all actions

### ✅ 8. Maintainability
- **Modular Components**: Each section in separate component file
- **TypeScript**: Full type safety with interfaces and prop typing
- **Test IDs**: `data-testid` attributes for automated testing
- **Error Boundaries**: Graceful fallbacks for API failures
- **Development Mode**: Special notices and debugging info

## 📁 File Structure

```
ui/src/
├── components/
│   ├── settings/
│   │   ├── TokenSettings.tsx          # Authentication token management
│   │   ├── UIPreferences.tsx          # Theme and UI customization
│   │   ├── NotificationSettings.tsx   # Email/Slack notification toggles
│   │   ├── ApiKeyManagement.tsx       # API key CRUD operations
│   │   └── PasswordChangeForm.tsx     # Secure password change
│   └── ui/
│       └── radio-group.tsx            # New Radix UI radio group component
├── pages/
│   └── SettingsPage.tsx               # Main settings page layout
└── App.tsx                            # Updated with /settings route
```

## 🔌 API Endpoints

### Authentication
- `GET /api/auth/token-info` - Get current token information
- `POST /api/auth/rotate-token` - Rotate authentication token
- `POST /api/auth/change-password` - Change user password

### User Preferences
- `GET /api/user/preferences` - Get notification preferences
- `PATCH /api/user/preferences` - Update notification preferences

### API Keys
- `GET /api/user/api-keys` - List user's API keys
- `POST /api/user/api-keys` - Create new API key
- `POST /api/user/api-keys/{id}/rotate` - Rotate specific API key
- `DELETE /api/user/api-keys/{id}` - Revoke API key

## 🎨 Design System

### Components Used
- **shadcn/ui**: Card, Button, Input, Label, Select, Switch, Dialog, Alert
- **Radix UI**: Radio Group, Tooltip, Popover (via shadcn/ui)
- **Lucide Icons**: Settings, Shield, Lock, Key, Bell, etc.
- **Tailwind CSS**: Responsive utilities, dark mode, color schemes

### Color Coding
- **Green**: Success states, valid inputs, active features
- **Red**: Errors, destructive actions, invalid inputs
- **Yellow/Orange**: Warnings, expiring tokens, medium strength
- **Blue**: Primary actions, information, active states
- **Gray**: Disabled states, secondary information

## 🔒 Security Considerations

### Token Management
- Tokens are stored securely in localStorage
- Automatic rotation with seamless session continuity
- Expiration warnings prevent unexpected logouts

### Password Security
- Real-time strength validation
- Prevents common weak passwords
- Secure transmission (HTTPS required)
- Session invalidation after password change

### API Key Security
- Keys shown only once during creation
- Secure preview format (partial display)
- Immediate revocation capability
- Audit trail for key operations

## 🧪 Testing

### Test IDs Available
- `settings-page` - Main settings container
- `token-settings` - Token management section
- `ui-preferences` - UI customization section
- `notification-settings` - Notification toggles
- `api-key-management` - API key management
- `password-change-form` - Password change form
- Component-specific test IDs for buttons, inputs, toggles

### Manual Testing
- Use `test-settings-page.tsx` for component verification
- Test all form validations and error states
- Verify responsive behavior across devices
- Test accessibility with screen readers

## 🚀 Deployment Notes

### Dependencies Added
- `@radix-ui/react-radio-group` - For theme selection UI

### Build Status
- ✅ TypeScript compilation successful
- ✅ ESLint warnings resolved
- ✅ Production build optimized
- ✅ No runtime errors detected

### Browser Support
- Modern browsers with ES6+ support
- Mobile Safari and Chrome
- Desktop Firefox, Chrome, Safari, Edge

## 🔄 Future Enhancements

### Potential Additions
- **Session Management**: View and revoke active sessions
- **Two-Factor Authentication**: TOTP/SMS setup
- **Data Export**: Download user data and settings
- **Advanced Notifications**: Custom alert rules and filters
- **Team Settings**: Shared preferences for organizations
- **Audit Log**: View settings change history

### Integration Opportunities
- **SSO Integration**: SAML/OAuth provider settings
- **Webhook Configuration**: Custom notification endpoints
- **API Rate Limiting**: User-specific rate limit configuration
- **Custom Dashboards**: Personalized dashboard layouts
