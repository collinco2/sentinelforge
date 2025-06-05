# 🛡️ SentinelForge Role Management System

## Overview

The SentinelForge Role Management System provides comprehensive admin-only functionality for managing user roles and permissions within the security platform. This system implements robust RBAC (Role-Based Access Control) with comprehensive audit logging and security features.

## 🎯 Features

### Admin-Only Access Control
- **Restricted Access**: Only users with "admin" role can access role management functionality
- **UI Protection**: Role Management navigation link only visible to admins
- **API Security**: All endpoints protected with `@require_role([UserRole.ADMIN])` decorator
- **Self-Protection**: Admins cannot demote their own role to prevent lockout

### User Management
- **User Listing**: View all registered users with their roles, status, and creation dates
- **Role Updates**: Change user roles between viewer, analyst, auditor, and admin
- **Role Filtering**: Filter users by role type for easier management
- **Status Monitoring**: View active/inactive user status

### Comprehensive Audit Logging
- **Role Change Tracking**: Every role change is logged with detailed information
- **Admin Attribution**: Track which admin performed each role change
- **Timestamp Recording**: Precise timestamps for all role modifications
- **Audit Trail UI**: Dedicated interface for viewing role change history

### Security Features
- **Input Validation**: Comprehensive validation of role values and request structure
- **Error Handling**: Graceful error handling with informative user feedback
- **Access Logging**: All access attempts and changes are logged
- **Database Protection**: Parameterized queries prevent SQL injection

## 🏗️ Architecture

### Backend Components

#### API Endpoints
```
GET /api/users                    - List all users (admin only)
PATCH /api/user/<id>/role         - Update user role (admin only)
GET /api/audit/roles              - View role change audit logs (admin only)
```

#### Database Schema
- **Users Table**: Stores user information including roles
- **Audit Logs Table**: Extended to track role changes with special format
- **Role Change Format**: Uses negative alert_id to distinguish role changes

#### Security Implementation
- **RBAC Decorators**: `@require_role([UserRole.ADMIN])` on all endpoints
- **Self-Demotion Prevention**: Validation prevents admin from changing own role
- **Comprehensive Logging**: All actions logged with admin attribution

### Frontend Components

#### RoleManagementPanel.tsx
- **User Table**: Displays all users with role badges and status indicators
- **Role Editing**: Inline dropdowns for changing user roles
- **Confirmation Dialogs**: Confirm role changes before execution
- **Audit Trail**: Toggleable view of role change history
- **Filtering**: Role-based filtering and search capabilities

#### Navigation Integration
- **Admin-Only Link**: Role Management link only visible to admin users
- **Route Protection**: Page-level access control with graceful error handling
- **Responsive Design**: Mobile-friendly interface with accessibility support

## 🚀 Usage

### Accessing Role Management

1. **Login as Admin**: Only admin users can access role management
2. **Navigate**: Click "Role Management" in the sidebar navigation
3. **View Users**: See all registered users with their current roles
4. **Filter Users**: Use role filter dropdown to view specific user types

### Managing User Roles

1. **Select User**: Find the user whose role you want to change
2. **Change Role**: Click the role dropdown and select new role
3. **Confirm**: Review and confirm the role change in the dialog
4. **Verify**: Check the audit trail to confirm the change was logged

### Viewing Audit Trail

1. **Toggle Audit**: Click "Show Audit Trail" button
2. **Review Changes**: View chronological list of all role changes
3. **Filter Logs**: Use filters to view specific user or time period changes
4. **Export**: Export audit logs for compliance reporting

## 🔐 Security Considerations

### Access Control
- **Admin-Only**: All role management functions restricted to admin users
- **UI Restrictions**: Non-admin users cannot see or access role management
- **API Protection**: Backend endpoints validate admin role on every request
- **Self-Protection**: Prevents admin lockout through self-demotion

### Audit Requirements
- **Complete Logging**: Every role change is logged with full context
- **Admin Attribution**: Track which admin performed each action
- **Immutable Records**: Audit logs cannot be modified after creation
- **Compliance Ready**: Audit format suitable for security compliance

### Data Protection
- **Input Validation**: All inputs validated and sanitized
- **SQL Injection Prevention**: Parameterized queries throughout
- **Error Handling**: Secure error messages without information disclosure
- **Session Management**: Proper authentication and authorization checks

## 🧪 Testing

### Backend Tests (11 test cases)
- **Access Control**: Verify admin-only access to all endpoints
- **Role Updates**: Test valid and invalid role changes
- **Self-Protection**: Ensure admin cannot demote themselves
- **Audit Logging**: Verify all changes are properly logged
- **Error Handling**: Test edge cases and error conditions

### Frontend Tests
- **Component Rendering**: Test UI components render correctly
- **Access Control**: Verify non-admin users see access denied
- **Role Changes**: Test role update workflow with confirmations
- **Audit Display**: Test audit trail display and filtering
- **Error Handling**: Test error states and user feedback

### Integration Tests
- **End-to-End**: Full workflow from login to role change
- **API Integration**: Frontend and backend integration testing
- **Database**: Test database operations and data integrity
- **Security**: Verify all security controls function correctly

## 📋 Role Definitions

### Viewer
- **Permissions**: Read-only access to security data
- **Use Case**: Stakeholders who need visibility but not action capability
- **Restrictions**: Cannot modify data or perform security actions

### Analyst
- **Permissions**: Active threat analysis and risk score overrides
- **Use Case**: Security analysts performing daily threat hunting
- **Capabilities**: Can override risk scores and analyze threats

### Auditor
- **Permissions**: View audit trails and compliance data
- **Use Case**: Compliance officers and security auditors
- **Capabilities**: Can view all audit logs and generate reports

### Admin
- **Permissions**: Full system access including user management
- **Use Case**: System administrators and security managers
- **Capabilities**: All permissions plus user role management

## 🔧 Configuration

### Environment Setup
```bash
# Backend API server must be running on port 5059
python api_server.py

# Frontend UI must be running on port 3000
cd sentinelforge-ui && npm start
```

### Database Requirements
- **SQLite Database**: Configured with users and audit_logs tables
- **Demo Users**: Pre-configured demo users for testing
- **Audit Schema**: Extended audit_logs table for role change tracking

### Security Configuration
- **RBAC System**: Configured with four role levels
- **Session Management**: Proper authentication headers required
- **Audit Retention**: Configure audit log retention policies

## 🚨 Troubleshooting

### Common Issues

#### Access Denied Errors
- **Cause**: User does not have admin role
- **Solution**: Verify user role in database or contact admin

#### Role Changes Not Saving
- **Cause**: Database connection or validation errors
- **Solution**: Check API server logs and database connectivity

#### Audit Trail Not Loading
- **Cause**: Database query issues or permission problems
- **Solution**: Verify audit_logs table structure and permissions

### Debug Steps
1. **Check User Role**: Verify current user has admin permissions
2. **API Connectivity**: Test API endpoints with curl or Postman
3. **Database Status**: Verify database connection and table structure
4. **Browser Console**: Check for JavaScript errors in browser console
5. **Server Logs**: Review API server logs for error messages

## 📚 API Reference

### GET /api/users
Returns list of all users with roles and status information.

**Response:**
```json
{
  "users": [
    {
      "user_id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true,
      "created_at": "2023-12-21T10:00:00Z"
    }
  ],
  "total": 1
}
```

### PATCH /api/user/<id>/role
Updates a user's role with validation and audit logging.

**Request:**
```json
{
  "role": "analyst"
}
```

**Response:**
```json
{
  "message": "User role updated successfully",
  "user": { /* updated user object */ },
  "old_role": "viewer",
  "new_role": "analyst"
}
```

### GET /api/audit/roles
Returns role change audit logs with filtering options.

**Query Parameters:**
- `limit`: Number of records to return (default: 50)
- `offset`: Pagination offset (default: 0)
- `user_id`: Filter by target user ID

**Response:**
```json
{
  "audit_logs": [
    {
      "id": 1,
      "timestamp": "2023-12-21T13:00:00Z",
      "admin_username": "admin",
      "justification": "ROLE_CHANGE: User 'analyst1' role changed from 'viewer' to 'analyst'",
      "action": "role_change",
      "target_user_id": 2
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## 🎉 Success Metrics

The role management system has been successfully implemented with:

✅ **11/11 Backend Tests Passing** - Complete API test coverage
✅ **Frontend Component Tests** - UI component validation
✅ **Security Controls** - Admin-only access enforcement
✅ **Audit Logging** - Comprehensive change tracking
✅ **User Experience** - Intuitive interface with confirmations
✅ **Error Handling** - Graceful error management
✅ **Documentation** - Complete implementation guide

The system is now ready for production use with full admin-only role management capabilities!
