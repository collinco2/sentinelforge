# 🏥 SentinelForge Feed Health Monitoring System

Comprehensive automated health monitoring for threat intelligence feeds with real-time status tracking, database logging, and scheduled checks.

## 📋 Overview

The Feed Health Monitoring System provides:

- **Automated Health Checks**: Regular monitoring of all active threat feeds
- **Database Logging**: Persistent storage of health check results in `feed_health_logs` table
- **Real-time API**: Cached health status with force refresh capability
- **Cron Integration**: Standalone scripts for external scheduling
- **Server Startup**: Automatic health check on API server startup
- **Admin Controls**: Scheduler management and manual trigger endpoints

## 🚀 Quick Start

### Automatic Startup (Recommended)

The health monitoring system starts automatically when you run the API server:

```bash
python3 api_server.py
```

This will:
1. Run an initial health check on startup
2. Start a background scheduler with 1-minute intervals
3. Cache results for fast API responses

### Manual Health Check

```bash
# One-time health check
python3 services/feed_health_monitor.py --check-now

# Check specific feed
python3 services/feed_health_monitor.py --feed-id 5

# Start cron scheduler
python3 services/feed_health_monitor.py --start-cron --interval 5
```

### Cron Job Setup

```bash
# Add to crontab for 1-minute intervals
* * * * * /usr/bin/python3 /path/to/sentinelforge/scripts/health_check_cron.py

# Add to crontab for 5-minute intervals  
*/5 * * * * /usr/bin/python3 /path/to/sentinelforge/scripts/health_check_cron.py
```

## 🌐 API Endpoints

### Get Health Status

```http
GET /api/feeds/health
```

**Parameters:**
- `force=true` - Force fresh check (bypass cache)
- `feed_id=<id>` - Check specific feed only

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_feeds": 5,
    "healthy_feeds": 4,
    "unhealthy_feeds": 1,
    "health_percentage": 80.0
  },
  "feeds": [
    {
      "feed_id": 1,
      "feed_name": "MalwareDomainList - Domains",
      "url": "https://www.malwaredomainlist.com/hostslist/hosts.txt",
      "status": "ok",
      "http_code": 200,
      "response_time_ms": 1250,
      "last_checked": "2024-12-10T10:30:00Z",
      "is_active": true
    }
  ],
  "checked_at": "2024-12-10T10:30:00Z",
  "checked_by": "admin",
  "from_cache": false,
  "cache_age_seconds": 0
}
```

### Trigger Health Check

```http
POST /api/feeds/health/trigger
```

**Body (optional):**
```json
{
  "feed_id": 5  // Check specific feed only
}
```

**Response:** Same as GET endpoint with additional fields:
```json
{
  "triggered_by": "admin",
  "trigger_type": "manual"
}
```

### Manage Scheduler (Admin Only)

```http
GET /api/feeds/health/scheduler
```

**Response:**
```json
{
  "success": true,
  "scheduler": {
    "running": true,
    "jobs": [
      {
        "id": "feed_health_check",
        "name": "Feed Health Check",
        "next_run": "2024-12-10T10:31:00Z",
        "trigger": "interval[0:01:00]"
      }
    ]
  }
}
```

```http
POST /api/feeds/health/scheduler
```

**Body:**
```json
{
  "action": "start",        // "start" or "stop"
  "interval_minutes": 5     // For start action
}
```

## 🗄️ Database Schema

### feed_health_logs Table

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
    checked_by INTEGER DEFAULT 0,
    FOREIGN KEY (feed_id) REFERENCES threat_feeds (id)
);
```

### Health Status Values

| Status | Description | HTTP Codes |
|--------|-------------|------------|
| `ok` | Feed is healthy and accessible | 200-299 |
| `unauthorized` | Authentication required | 401 |
| `forbidden` | Access forbidden | 403 |
| `not_found` | Feed URL not found | 404 |
| `rate_limited` | Rate limit exceeded | 429 |
| `server_error` | Server-side error | 500-599 |
| `timeout` | Request timed out | - |
| `unreachable` | Connection failed | - |
| `ssl_error` | SSL certificate error | - |
| `error` | Other request error | - |

## ⚙️ Configuration

### Health Check Settings

The health monitor can be configured via environment variables or code:

```python
# Timeout settings
REQUEST_TIMEOUT = 30  # seconds

# Cache settings  
CACHE_TTL = 300  # 5 minutes

# Retry settings
MAX_RETRIES = 3
BACKOFF_FACTOR = 1

# Scheduler settings
DEFAULT_INTERVAL = 1  # minutes
```

### Feed-Specific Configuration

Feeds can have custom health check settings in their `format_config`:

```json
{
  "health_check": {
    "method": "HEAD",           // or "GET"
    "timeout": 30,              // seconds
    "follow_redirects": true,
    "verify_ssl": true,
    "custom_headers": {
      "User-Agent": "SentinelForge-Monitor/1.0"
    }
  }
}
```

## 🔧 Advanced Usage

### Custom Health Check Logic

```python
from services.feed_health_monitor import FeedHealthMonitor

# Initialize monitor
monitor = FeedHealthMonitor(db_path="custom.db", log_level="DEBUG")

# Run health check for specific feed
result = monitor.run_health_check(feed_id=5, checked_by=user_id)

# Get cached results
cached = monitor.get_cached_health()

# Start scheduler with custom interval
monitor.start_cron_scheduler(interval_minutes=10)
```

### Monitoring Integration

```python
# Example Prometheus metrics integration
from prometheus_client import Gauge, Counter

health_gauge = Gauge('feed_health_status', 'Feed health status', ['feed_name'])
check_counter = Counter('feed_health_checks_total', 'Total health checks', ['status'])

def update_metrics(health_results):
    for result in health_results:
        status_value = 1 if result['status'] == 'ok' else 0
        health_gauge.labels(feed_name=result['feed_name']).set(status_value)
        check_counter.labels(status=result['status']).inc()
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_feed_health_monitor.py
```

**Test Coverage:**
- ✅ Database table creation and logging
- ✅ Standalone health check functionality  
- ✅ API endpoint authentication and responses
- ✅ Cron job script execution
- ✅ Cache functionality and TTL
- ✅ Scheduler management
- ✅ Error handling and edge cases

## 📊 Monitoring Dashboard

### Health Status Indicators

The UI displays health status with color-coded badges:

- 🟢 **Green (ok)**: Feed is healthy and accessible
- 🟡 **Yellow (warning)**: Timeout, rate limited, or authentication issues
- 🔴 **Red (error)**: Unreachable, server error, or other failures
- ⚪ **Gray (unknown)**: Status not yet determined

### Real-time Updates

The dashboard automatically refreshes health status every 30 seconds and shows:

- Overall health percentage
- Individual feed status with response times
- Last check timestamp
- Error details for failed feeds
- Historical health trends

## 🚨 Troubleshooting

### Common Issues

**Health checks taking too long:**
- Reduce timeout values in feed configuration
- Use HEAD requests instead of GET for simple availability checks
- Check network connectivity to feed URLs

**Scheduler not starting:**
- Ensure APScheduler is installed: `pip install apscheduler`
- Check for port conflicts or permission issues
- Review server logs for startup errors

**Database errors:**
- Verify database file permissions
- Check disk space availability
- Ensure SQLite version compatibility

**API authentication failures:**
- Verify session token validity
- Check user role permissions (Analyst+ required)
- Ensure API server is running and accessible

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python3 services/feed_health_monitor.py --check-now --log-level DEBUG
```

## 🔐 Security Considerations

- **Admin Access**: Scheduler management requires admin role
- **Rate Limiting**: Respects feed provider rate limits
- **SSL Verification**: Validates SSL certificates by default
- **Audit Logging**: All health checks logged with user attribution
- **Error Handling**: Graceful failure without exposing sensitive data

## 📈 Performance

- **Caching**: 5-minute TTL reduces API response time to <50ms
- **Parallel Checks**: Multiple feeds checked concurrently
- **Efficient Queries**: Optimized database queries with proper indexing
- **Memory Usage**: Minimal memory footprint with cleanup
- **Network Optimization**: Connection pooling and retry strategies

The Feed Health Monitoring System provides comprehensive, automated monitoring of threat intelligence feeds with enterprise-grade reliability and performance.
