# 🏥 SentinelForge Feed Health Check API

The Feed Health Check API provides comprehensive monitoring capabilities for threat intelligence feeds in SentinelForge. It allows analysts and administrators to monitor feed availability, response times, and authentication status.

## 🚀 **Overview**

The health check system performs HTTP requests to feed URLs to verify their accessibility and response status. It supports different request methods (HEAD/GET) based on feed types and handles authentication requirements automatically.

### **Key Features**

- ✅ **Automated Health Checks** - Verify feed accessibility and response status
- ✅ **Authentication Support** - Handle API keys, basic auth, and custom authentication
- ✅ **Response Time Monitoring** - Track feed response performance
- ✅ **Historical Logging** - Maintain detailed health check history
- ✅ **RBAC Protection** - Analyst-level access control
- ✅ **Retry Logic** - Built-in retry mechanism for transient errors

---

## 📋 **API Endpoints**

### 1. **Check All Feeds Health**

**Endpoint:** `GET /api/feeds/health`

**Description:** Performs health checks on all feeds with configured URLs and returns comprehensive status information.

**Authentication:** Required (Analyst+ role)

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_feeds": 5,
    "healthy_feeds": 3,
    "unhealthy_feeds": 2,
    "health_percentage": 60.0
  },
  "feeds": [
    {
      "feed_id": 1,
      "feed_name": "IPsum Project",
      "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
      "status": "ok",
      "http_code": 200,
      "response_time_ms": 245,
      "last_checked": "2024-01-15T10:30:00Z",
      "is_active": true,
      "error_message": null
    },
    {
      "feed_id": 2,
      "feed_name": "PhishTank",
      "url": "https://data.phishtank.com/data/online-valid.json",
      "status": "unauthorized",
      "http_code": 401,
      "response_time_ms": 180,
      "last_checked": "2024-01-15T10:30:01Z",
      "is_active": true,
      "error_message": "HTTP 401: Unauthorized"
    }
  ],
  "checked_at": "2024-01-15T10:30:00Z",
  "checked_by": "analyst_user"
}
```

---

### 2. **Get Health Check History**

**Endpoint:** `GET /api/feeds/health/history`

**Description:** Retrieves historical health check records with filtering options.

**Authentication:** Required (Analyst+ role)

**Query Parameters:**
- `limit` (integer, default: 50) - Number of records to return
- `offset` (integer, default: 0) - Pagination offset
- `feed_id` (integer, optional) - Filter by specific feed ID
- `status` (string, optional) - Filter by health status
- `hours` (integer, default: 24) - Time window in hours

**Example Request:**
```bash
GET /api/feeds/health/history?limit=10&hours=24&status=ok
```

**Response:**
```json
{
  "success": true,
  "health_logs": [
    {
      "id": 123,
      "feed_id": 1,
      "feed_name": "IPsum Project",
      "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
      "status": "ok",
      "http_code": 200,
      "response_time_ms": 245,
      "error_message": null,
      "last_checked": "2024-01-15T10:30:00Z",
      "checked_by": 1,
      "checked_by_username": "analyst_user"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 10,
    "offset": 0,
    "has_more": true
  },
  "filters": {
    "feed_id": null,
    "status": "ok",
    "hours": 24
  }
}
```

---

### 3. **Check Specific Feed Health**

**Endpoint:** `GET /api/feeds/{feed_id}/health`

**Description:** Performs a health check on a specific feed and returns current status plus recent history.

**Authentication:** Required (Analyst+ role)

**Path Parameters:**
- `feed_id` (integer) - ID of the feed to check

**Response:**
```json
{
  "success": true,
  "current_health": {
    "feed_id": 1,
    "feed_name": "IPsum Project",
    "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
    "status": "ok",
    "http_code": 200,
    "response_time_ms": 245,
    "last_checked": "2024-01-15T10:30:00Z",
    "is_active": true,
    "error_message": null
  },
  "recent_checks": [
    {
      "id": 122,
      "status": "ok",
      "http_code": 200,
      "response_time_ms": 230,
      "last_checked": "2024-01-15T09:30:00Z",
      "error_message": null
    }
  ],
  "feed_details": {
    "id": 1,
    "name": "IPsum Project",
    "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
    "feed_type": "txt",
    "is_active": true
  }
}
```

---

## 📊 **Health Status Values**

| Status | Description | HTTP Codes |
|--------|-------------|------------|
| `ok` | Feed is accessible and responding normally | 200 |
| `unreachable` | Feed URL is not accessible | 404, 4xx (except auth) |
| `unauthorized` | Authentication failed | 401, 403 |
| `timeout` | Request timed out | N/A |
| `rate_limited` | Rate limited by feed provider | 429 |
| `server_error` | Server error on feed side | 5xx |
| `error` | Other request error (network, DNS, etc.) | N/A |

---

## 🔧 **Technical Implementation**

### **Request Strategy**

The health check system uses different HTTP methods based on feed characteristics:

- **HEAD requests** - Used for CSV and TXT feeds (faster, no content download)
- **GET requests** - Used for JSON and STIX feeds, or when HEAD is not supported
- **Stream mode** - GET requests use streaming to avoid downloading full content

### **Authentication Handling**

The system automatically handles various authentication methods:

```python
# API Key in header
headers["Authorization"] = f"Bearer {api_key}"

# API Key in query parameters (PhishTank)
params["api_key"] = api_key

# Basic Authentication
auth = (username, password)
```

### **Retry Logic**

Built-in retry strategy for transient errors:

- **Total retries:** 2 attempts
- **Status codes:** 429, 500, 502, 503, 504
- **Backoff factor:** 0.5 seconds
- **Timeout:** 10 seconds per request

### **Database Schema**

The `feed_health_logs` table stores all health check results:

```sql
CREATE TABLE feed_health_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    feed_name TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    http_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    last_checked DATETIME NOT NULL,
    checked_by INTEGER NOT NULL,
    FOREIGN KEY (feed_id) REFERENCES threat_feeds (id)
);
```

---

## 🔐 **Security & Access Control**

### **RBAC Requirements**

All health check endpoints require authentication and specific role permissions:

- **Minimum Role:** Analyst
- **Allowed Roles:** Analyst, Auditor, Admin
- **Authentication:** JWT token in Authorization header

### **Rate Limiting**

Health checks include built-in protection against abuse:

- **Request timeout:** 10 seconds
- **Retry limits:** Maximum 2 retries per feed
- **Concurrent limits:** Processed sequentially to avoid overwhelming feeds

---

## 🚀 **Usage Examples**

### **cURL Examples**

```bash
# Check all feeds health
curl -H "Authorization: Bearer <token>" \
     http://localhost:5059/api/feeds/health

# Get health history for last 48 hours
curl -H "Authorization: Bearer <token>" \
     "http://localhost:5059/api/feeds/health/history?hours=48&limit=20"

# Check specific feed
curl -H "Authorization: Bearer <token>" \
     http://localhost:5059/api/feeds/1/health

# Filter history by status
curl -H "Authorization: Bearer <token>" \
     "http://localhost:5059/api/feeds/health/history?status=ok"
```

### **Python Example**

```python
import requests

headers = {"Authorization": "Bearer your_token_here"}
base_url = "http://localhost:5059"

# Check all feeds
response = requests.get(f"{base_url}/api/feeds/health", headers=headers)
health_data = response.json()

print(f"Health percentage: {health_data['summary']['health_percentage']}%")

# Check specific feed
response = requests.get(f"{base_url}/api/feeds/1/health", headers=headers)
feed_health = response.json()

print(f"Feed status: {feed_health['current_health']['status']}")
```

### **JavaScript Example**

```javascript
const token = 'your_token_here';
const baseUrl = 'http://localhost:5059';

// Check all feeds health
fetch(`${baseUrl}/api/feeds/health`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  console.log(`Health: ${data.summary.health_percentage}%`);
  data.feeds.forEach(feed => {
    console.log(`${feed.feed_name}: ${feed.status}`);
  });
});
```

---

## 🔍 **Monitoring & Alerting**

### **Health Metrics**

Key metrics available for monitoring:

- **Overall health percentage** - Percentage of healthy feeds
- **Response times** - Average and individual feed response times
- **Error rates** - Frequency of failed health checks
- **Authentication failures** - Feeds with auth issues

### **Recommended Monitoring**

1. **Dashboard Integration** - Display health percentage and status
2. **Alerting Rules** - Alert when health drops below threshold
3. **Trend Analysis** - Monitor response time trends
4. **Error Tracking** - Track and resolve authentication issues

---

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Authentication Failures**
   - Verify API keys are current and valid
   - Check authentication configuration in feed settings

2. **Timeout Issues**
   - Some feeds may be slow; consider increasing timeout
   - Check network connectivity to feed URLs

3. **Rate Limiting**
   - Implement delays between health checks
   - Use API keys where available to increase limits

### **Error Codes**

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 401 | Authentication required | Provide valid token |
| 403 | Insufficient permissions | Use Analyst+ role |
| 404 | Feed not found | Check feed ID exists |
| 500 | Server error | Check logs for details |

---

## 📈 **Performance Considerations**

- **Batch Processing** - All feeds checked sequentially
- **Memory Usage** - Minimal (streaming responses)
- **Network Impact** - Uses HEAD requests where possible
- **Database Growth** - Health logs accumulate over time (consider cleanup)

The Feed Health Check API provides comprehensive monitoring capabilities while maintaining security and performance standards for production environments.
