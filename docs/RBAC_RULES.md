# 🛡️ SentinelForge Role-Based Access Control (RBAC) Rules

## 📋 Overview

SentinelForge implements a comprehensive Role-Based Access Control (RBAC) system to ensure proper authorization and security for sensitive operations. This document outlines the roles, permissions, and access control rules.

## 🎭 User Roles

### 👁️ **Viewer**
- **Purpose**: Read-only access for monitoring and observation
- **Typical Users**: Junior analysts, stakeholders, external auditors
- **Access Level**: Minimal - view-only permissions

### 🔍 **Analyst**
- **Purpose**: Active threat analysis and response
- **Typical Users**: Security analysts, incident responders
- **Access Level**: Operational - can modify alert assessments

### 📊 **Auditor**
- **Purpose**: Compliance monitoring and audit trail review
- **Typical Users**: Compliance officers, internal auditors, supervisors
- **Access Level**: Oversight - can view all audit data

### ⚙️ **Admin**
- **Purpose**: Full system administration and management
- **Typical Users**: Security team leads, system administrators
- **Access Level**: Complete - all permissions

## 🔐 Permissions Matrix

| Feature | Viewer | Analyst | Auditor | Admin |
|---------|--------|---------|---------|-------|
| **View Alerts** | ✅ | ✅ | ✅ | ✅ |
| **View IOCs** | ✅ | ✅ | ✅ | ✅ |
| **View Dashboard** | ✅ | ✅ | ✅ | ✅ |
| **Override Risk Scores** | ❌ | ✅ | ❌ | ✅ |
| **View Audit Trail** | ❌ | ❌ | ✅ | ✅ |
| **Export Data** | ❌ | ✅ | ✅ | ✅ |
| **System Configuration** | ❌ | ❌ | ❌ | ✅ |

## 🔒 API Endpoint Security

### **Risk Score Override**
- **Endpoint**: `PATCH /api/alert/<id>/override`
- **Required Roles**: `analyst`, `admin`
- **Response Codes**:
  - `200`: Success (authorized user)
  - `401`: Unauthorized (no authentication)
  - `403`: Forbidden (insufficient permissions)

### **Audit Trail Access**
- **Endpoint**: `GET /api/audit`
- **Required Roles**: `auditor`, `admin`
- **Response Codes**:
  - `200`: Success (authorized user)
  - `401`: Unauthorized (no authentication)
  - `403`: Forbidden (insufficient permissions)

### **User Information**
- **Endpoint**: `GET /api/user/current`
- **Required Roles**: Any authenticated user
- **Response Codes**:
  - `200`: Success (any valid user)
  - `401`: Unauthorized (no authentication)

## 🎯 Frontend Access Control

### **UI Element Restrictions**

#### **Risk Score Override Button**
```typescript
// Shown only for analysts and admins
{canOverrideRiskScores() && (
  <Button onClick={handleOverride}>
    Override Risk Score
  </Button>
)}

// Disabled with tooltip for other roles
{!canOverrideRiskScores() && (
  <Tooltip content="You do not have permission to override risk scores">
    <Button disabled>Override Risk Score</Button>
  </Tooltip>
)}
```

#### **Audit Trail Tab**
```typescript
// Shown only for auditors and admins
{canViewAuditTrail() && (
  <TabsTrigger value="audit">
    Audit Trail
  </TabsTrigger>
)}
```

### **Permission Checking Functions**
```typescript
// Check specific permissions
const canOverride = user?.permissions?.can_override_risk_scores ?? false;
const canViewAudit = user?.permissions?.can_view_audit_trail ?? false;

// Check role membership
const hasRole = (requiredRoles: UserRole[]) => 
  user && requiredRoles.includes(user.role);
```

## 🔧 Implementation Details

### **Backend Authentication**
```python
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def override_alert_risk_score(alert_id):
    """Override risk score - requires analyst or admin role."""
    current_user = g.current_user
    # Implementation...
```

### **Frontend Permission Hooks**
```typescript
const { canOverrideRiskScores, canViewAuditTrail } = useAuth();

// Use in components
if (!canOverrideRiskScores()) {
  toast({
    title: "Permission Denied",
    description: "You do not have permission to perform this action.",
    variant: "destructive",
  });
  return;
}
```

## 🧪 Testing RBAC

### **Backend API Tests**
```bash
# Run RBAC API tests
python3 test_rbac_api.py
```

### **Frontend Component Tests**
```bash
# Run React RBAC tests
npm test RBAC.test.tsx
```

### **Manual Testing**
1. Use the User Role Selector in the top navigation
2. Switch between different roles (Admin, Analyst, Auditor, Viewer)
3. Verify UI elements appear/disappear based on permissions
4. Test API calls return appropriate status codes

## 🚨 Security Considerations

### **Defense in Depth**
- **Frontend**: UI restrictions prevent unauthorized actions
- **Backend**: API validation enforces permissions
- **Database**: Audit trail provides accountability

### **Error Handling**
- **Graceful Degradation**: UI adapts to user permissions
- **Clear Messaging**: Users understand why actions are restricted
- **Logging**: All permission checks are logged for audit

### **Session Management**
- **Token-based**: Secure session tokens for authentication
- **Expiration**: Sessions expire after 24 hours
- **Validation**: Every request validates current permissions

## 📊 Audit and Compliance

### **Audit Trail Features**
- **Immutable Records**: All risk score overrides are permanently logged
- **User Attribution**: Every action is tied to a specific user
- **Justification Required**: Analysts must provide reasoning for overrides
- **Timestamp Accuracy**: UTC timestamps for global consistency

### **Compliance Support**
- **SOX**: Financial system security controls
- **HIPAA**: Healthcare data protection
- **PCI DSS**: Payment card industry standards
- **SOC 2**: Service organization controls
- **ISO 27001**: Information security management

## 🔄 Role Management

### **Demo Users** (for testing)
```typescript
const demoUsers = [
  { id: 1, username: "admin", role: UserRole.ADMIN },
  { id: 2, username: "analyst", role: UserRole.ANALYST },
  { id: 3, username: "auditor", role: UserRole.AUDITOR },
  { id: 4, username: "viewer", role: UserRole.VIEWER },
];
```

### **Production Deployment**
- Replace demo authentication with enterprise SSO
- Integrate with Active Directory or LDAP
- Implement proper user provisioning workflows
- Add role assignment management interface

## 🛠️ Troubleshooting

### **Common Issues**

#### **403 Forbidden Errors**
- **Cause**: User lacks required role for action
- **Solution**: Verify user role and required permissions
- **Check**: `GET /api/user/current` to see current permissions

#### **UI Elements Not Appearing**
- **Cause**: Frontend permission checks failing
- **Solution**: Check `useAuth()` hook returns correct permissions
- **Debug**: Console log user object and permission flags

#### **Authentication Failures**
- **Cause**: Missing or invalid session token
- **Solution**: Re-authenticate or refresh session
- **Check**: Verify `X-Demo-User-ID` header for demo mode

---

## 📞 Support

For RBAC-related issues or questions:
- **Security Team**: security@sentinelforge.com
- **Technical Support**: support@sentinelforge.com
- **Documentation**: [SentinelForge Wiki](./README.md)

---

*Last Updated: June 2025 | Version 1.0*
*This document is part of the SentinelForge security platform documentation.*
