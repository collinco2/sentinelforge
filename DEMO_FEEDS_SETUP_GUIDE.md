# 🚀 SentinelForge Demo Feed Setup Guide

This guide covers the comprehensive demo feed setup system for SentinelForge, providing instant threat intelligence data for testing and demonstration purposes.

## 📋 Overview

The demo feed setup system provides two approaches for preloading sample threat feeds:

1. **Script-based**: `scripts/seed_feeds.py` - Command-line tool
2. **API-based**: `POST /api/admin/setup-demo-feeds` - REST endpoint

Both approaches create the same 5 demo feeds with sample IOC data across multiple formats.

## 📦 Demo Feeds Included

### 1. MalwareDomainList - Domains (TXT)
- **Type**: Domain IOCs
- **Format**: Plain text, one domain per line
- **Sample Data**: 5 malicious domains
- **Use Case**: Testing domain-based threat detection

### 2. Abuse.ch URLhaus - Malware URLs (CSV)
- **Type**: URL IOCs  
- **Format**: CSV with headers (url, threat, tags)
- **Sample Data**: 4 malicious URLs with threat classification
- **Use Case**: Testing URL-based threat detection and tagging

### 3. IPsum Threat Intelligence (TXT)
- **Type**: IP Address IOCs
- **Format**: Plain text, one IP per line
- **Sample Data**: 5 malicious IP addresses
- **Use Case**: Testing IP-based threat detection

### 4. MITRE ATT&CK STIX Feed (JSON)
- **Type**: Mixed IOCs (domains, hashes)
- **Format**: STIX 2.0 bundle format
- **Sample Data**: 2 indicators in STIX format
- **Use Case**: Testing STIX parsing and structured threat intelligence

### 5. Emerging Threats - Compromised IPs (TXT)
- **Type**: IP Address IOCs
- **Format**: Plain text with comments
- **Sample Data**: 5 compromised IP addresses
- **Use Case**: Testing IP threat feeds with comment handling

## 🛠️ Script-based Setup

### Usage

```bash
# Basic feed registration (no IOC import)
python scripts/seed_feeds.py --confirm

# Full setup with IOC data import
python scripts/seed_feeds.py --confirm --import-data

# Interactive mode (prompts for confirmation)
python scripts/seed_feeds.py
```

### Features

- ✅ Admin authentication required
- ✅ Interactive confirmation prompts
- ✅ Sample file generation in `feeds/demo/`
- ✅ Database feed registration
- ✅ Optional IOC data import
- ✅ Comprehensive error handling
- ✅ Detailed progress reporting

### Example Output

```
🚀 SentinelForge Demo Feed Seeder
==================================================

🔐 Admin authentication required
Username: admin
Password: ****
✅ Authenticated as admin (Admin)

📁 Creating sample feed files...
  ✅ Created feeds/demo/demo_malwaredomainlist_domains.txt
  ✅ Created feeds/demo/demo_abuse_ch_urlhaus_malware_urls.csv
  ✅ Created feeds/demo/demo_ipsum_threat_intelligence.txt
  ✅ Created feeds/demo/demo_mitre_att_ck_stix_feed.json
  ✅ Created feeds/demo/demo_emerging_threats_compromised_ips.txt

📋 Registering demo feeds...
  ✅ Registered: MalwareDomainList - Domains
  ✅ Registered: Abuse.ch URLhaus - Malware URLs
  ✅ Registered: IPsum Threat Intelligence
  ✅ Registered: MITRE ATT&CK STIX Feed
  ✅ Registered: Emerging Threats - Compromised IPs
🎉 Successfully registered 5 demo feeds

📥 Importing sample IOC data...
  📊 Processing MalwareDomainList - Domains...
    ✅ Imported 5 IOCs
  📊 Processing Abuse.ch URLhaus - Malware URLs...
    ✅ Imported 4 IOCs
  📊 Processing IPsum Threat Intelligence...
    ✅ Imported 5 IOCs
  📊 Processing MITRE ATT&CK STIX Feed...
    ✅ Imported 2 IOCs
  📊 Processing Emerging Threats - Compromised IPs...
    ✅ Imported 5 IOCs
🎉 Sample data import completed successfully

🎉 Demo feed setup completed successfully!
📁 Sample files created in: feeds/demo
🌐 Access feeds via: http://localhost:3000/feeds
📊 Sample IOC data has been imported
🔍 View IOCs at: http://localhost:3000/iocs
```

## 🌐 API-based Setup

### Endpoint

```
POST /api/admin/setup-demo-feeds
```

### Authentication

- **Required**: Admin role
- **Method**: Session token or API key
- **Header**: `X-Session-Token: <token>`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `confirm` | boolean | Yes | Confirmation flag (query param or body) |
| `import_data` | boolean | No | Whether to import sample IOC data |

### Usage Examples

#### 1. Feed Registration Only

```bash
curl -X POST "http://localhost:5059/api/admin/setup-demo-feeds?confirm=true" \
  -H "X-Session-Token: <your-session-token>"
```

#### 2. Full Setup with Data Import

```bash
curl -X POST "http://localhost:5059/api/admin/setup-demo-feeds?confirm=true&import_data=true" \
  -H "X-Session-Token: <your-session-token>"
```

#### 3. JSON Body Parameters

```bash
curl -X POST "http://localhost:5059/api/admin/setup-demo-feeds" \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: <your-session-token>" \
  -d '{"confirm": true, "import_data": true}'
```

### Response Format

```json
{
  "success": true,
  "message": "Demo feeds setup completed successfully",
  "feeds_created": [
    {
      "id": "abc123...",
      "name": "MalwareDomainList - Domains",
      "type": "txt"
    },
    {
      "id": "def456...",
      "name": "Abuse.ch URLhaus - Malware URLs", 
      "type": "csv"
    }
  ],
  "total_feeds": 5,
  "iocs_imported": 21,
  "import_data": true
}
```

### Error Responses

#### Missing Confirmation
```json
{
  "error": "Confirmation required",
  "message": "Add ?confirm=true or include 'confirm': true in request body to proceed"
}
```

#### Insufficient Permissions
```json
{
  "error": "Insufficient permissions",
  "message": "This action requires one of the following roles: ['admin']",
  "user_role": "analyst"
}
```

## 🔧 Technical Implementation

### Database Schema

The system uses the existing SentinelForge database schema:

- **threat_feeds**: Feed configurations and metadata
- **iocs**: Individual indicators of compromise
- **feed_import_logs**: Import history and statistics

### Feed Configuration Format

Each demo feed includes:

```python
{
    "name": "Feed Display Name",
    "feed_type": "txt|csv|json",
    "description": "Human-readable description",
    "url": "https://example.com/feed-url",
    "ioc_type": "domain|ip|url|hash|mixed",
    "format_config": {
        # Format-specific parsing configuration
    },
    "sample_data": [
        # Sample IOC data for import
    ]
}
```

### Supported Formats

| Format | Extension | Parser | Use Case |
|--------|-----------|--------|----------|
| TXT | `.txt` | Line-based with regex | Simple lists, IP ranges |
| CSV | `.csv` | Header-based columns | Structured data with metadata |
| JSON | `.json` | STIX 2.0 bundles | Complex threat intelligence |

### Deduplication Logic

- **IOCs**: Deduplicated by `(ioc_type, ioc_value)` combination
- **Feeds**: Skipped if feed name already exists
- **Import Logs**: New log entry created for each import attempt

## 🧪 Testing and Validation

### Automated Testing

Run the comprehensive test suite:

```bash
python test_demo_feeds_setup.py
```

### Test Coverage

- ✅ API endpoint authentication and authorization
- ✅ Feed registration without data import
- ✅ Feed registration with data import
- ✅ Script execution with various flags
- ✅ Sample file generation and validation
- ✅ Format parsing for all supported types
- ✅ Database integration and data persistence

### Manual Verification

1. **Check Feeds**: Visit `http://localhost:3000/feeds`
2. **Check IOCs**: Visit `http://localhost:3000/iocs`
3. **Check Import Logs**: Use API endpoint `/api/feeds/import-logs`

## 🔐 Security Considerations

### Access Control

- **Admin Only**: Both script and API require admin role
- **Confirmation Required**: Prevents accidental execution
- **Audit Logging**: All operations logged with user attribution

### Data Safety

- **Duplicate Prevention**: Existing feeds/IOCs are not overwritten
- **Transaction Safety**: Database operations use transactions
- **Error Handling**: Graceful failure with rollback on errors

## 📊 Use Cases

### 1. Development and Testing

```bash
# Quick setup for development
python scripts/seed_feeds.py --confirm --import-data
```

### 2. Demo Environments

```bash
# API-based setup for automated deployment
curl -X POST "http://localhost:5059/api/admin/setup-demo-feeds?confirm=true&import_data=true" \
  -H "X-Session-Token: $ADMIN_TOKEN"
```

### 3. QA Validation

```bash
# Test feed parsing without importing data
python scripts/seed_feeds.py --confirm
```

### 4. Training Environments

- Provides realistic threat intelligence data
- Covers all major IOC types and formats
- Includes proper metadata and tagging

## 🚀 Getting Started

1. **Start SentinelForge**: Ensure API server is running on port 5059
2. **Admin Access**: Have admin credentials ready
3. **Choose Method**: Script or API based on your needs
4. **Execute Setup**: Run with confirmation flag
5. **Verify Results**: Check feeds and IOCs in the UI

The demo feed setup system provides a comprehensive foundation for testing, development, and demonstration of SentinelForge's threat intelligence capabilities.
