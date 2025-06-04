# 🛡️ SentinelForge Analyst Guide: Risk Score Override & Audit Trail

## 📋 Overview

This guide provides security analysts with comprehensive instructions on when and how to override alert risk scores, ensuring accountability through the immutable audit trail system.

## 🎯 When to Override Risk Scores

### ✅ **Appropriate Override Scenarios**

1. **False Positives**
   - Legitimate administrative activities flagged as suspicious
   - Known good software triggering behavioral alerts
   - Scheduled maintenance activities causing anomalies

2. **Additional Context Available**
   - Threat intelligence confirms higher/lower severity
   - Business context changes risk assessment
   - Correlation with other security events

3. **Environmental Factors**
   - Test environment activities in production alerts
   - Known network changes affecting baseline
   - Approved security tool testing

4. **Escalation Needs**
   - Critical asset involvement requires higher priority
   - Compliance requirements demand specific risk levels
   - Executive or customer-facing systems affected

### ❌ **Inappropriate Override Scenarios**

- Personal preference without technical justification
- Workload management (hiding alerts to reduce queue)
- Uncertainty about alert validity (investigate first)
- Pressure to meet SLA metrics without proper analysis

## 📝 Writing Effective Justifications

### 🌟 **Best Practices**

1. **Be Specific and Technical**
   ```
   ✅ Good: "False positive - legitimate PowerShell execution by Domain Admin for scheduled backup script (backup-db.ps1) verified in change management system CM-2024-0156"
   
   ❌ Poor: "Not malicious"
   ```

2. **Include Evidence Sources**
   ```
   ✅ Good: "Escalating to HIGH - IOC matches APT29 campaign per CISA alert AA23-347A, targeting similar infrastructure"
   
   ❌ Poor: "Looks suspicious"
   ```

3. **Reference Business Context**
   ```
   ✅ Good: "Reducing to LOW - authorized penetration testing by CyberSec Corp per SOW-2024-003, testing window 2024-06-04 14:00-18:00 UTC"
   
   ❌ Poor: "Pen test"
   ```

### 📋 **Justification Template**

```
[DECISION]: [BRIEF_REASON] - [DETAILED_EXPLANATION] [EVIDENCE/REFERENCE]

Examples:
- FALSE_POSITIVE: Legitimate admin activity - PowerShell execution by john.doe@company.com for approved maintenance task per ticket INC-12345
- ESCALATION: Critical asset targeted - Domain controller DC01 involved, escalating per security playbook SEC-PB-001
- THREAT_INTEL: IOC correlation - Hash matches known Emotet variant per VirusTotal analysis, family confidence 95%
```

## 🔍 Reviewing the Audit Trail

### 📊 **Understanding Audit Entries**

Each audit entry contains:
- **Timestamp**: When the override occurred (UTC)
- **User**: Analyst who made the change
- **Score Change**: Original → Override score
- **Justification**: Analyst's reasoning
- **Alert Context**: Associated alert details

### 🔎 **Audit Trail Best Practices**

1. **Regular Review**
   - Check audit trail before making new overrides
   - Understand previous analyst decisions
   - Look for patterns in override reasoning

2. **Quality Assurance**
   - Verify justifications meet standards
   - Escalate unclear or insufficient reasoning
   - Document lessons learned for team training

3. **Compliance Support**
   - Use audit trail for incident response documentation
   - Support regulatory compliance reporting
   - Provide evidence for security control effectiveness

## 🏛️ Compliance & Governance

### 📋 **Regulatory Support**

The audit trail system supports compliance with:

- **SOX (Sarbanes-Oxley)**: Financial system security controls
- **HIPAA**: Healthcare data protection requirements  
- **PCI DSS**: Payment card industry security standards
- **SOC 2**: Service organization control frameworks
- **ISO 27001**: Information security management systems

### 🔒 **Data Integrity**

- **Immutable Records**: Audit entries cannot be modified or deleted
- **User Attribution**: Every change tracked to specific analyst
- **Timestamp Accuracy**: UTC timestamps for global consistency
- **Retention Policy**: Audit logs retained per organizational policy

## 🚀 Getting Started Workflow

### 1️⃣ **Access Alert Details**
- Navigate to Alerts page
- Click on alert to open detail modal
- Review alert information and IOCs

### 2️⃣ **Assess Override Need**
- Evaluate current risk score accuracy
- Consider business context and threat landscape
- Check previous audit trail entries

### 3️⃣ **Perform Override**
- Click edit icon (✏️) next to Risk Score
- Adjust score using slider or direct input
- **Required**: Provide detailed justification
- Click Save to commit changes

### 4️⃣ **Verify Audit Entry**
- Switch to "Audit Trail" tab
- Confirm new entry appears with correct details
- Review justification for clarity and completeness

## 📞 Support & Escalation

### 🆘 **When to Escalate**

- Uncertain about override appropriateness
- Complex alerts requiring senior analyst review
- Potential security incidents requiring immediate attention
- Technical issues with override functionality

### 📧 **Contact Information**

- **Security Operations Center**: soc@company.com
- **Senior Analyst On-Call**: +1-555-SOC-HELP
- **Technical Support**: support@sentinelforge.com

---

## 📚 Additional Resources

- [SentinelForge User Documentation](./README.md)
- [Security Playbooks](./playbooks/)
- [Threat Intelligence Integration](./threat-intel.md)
- [Incident Response Procedures](./incident-response.md)

---

*Last Updated: June 2025 | Version 1.0*
*This guide is part of the SentinelForge security platform documentation.*
