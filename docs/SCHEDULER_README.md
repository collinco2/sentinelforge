# 🕐 SentinelForge Scheduled Feed Importer

A comprehensive CRON-based scheduled feed importer for the SentinelForge Threat Intelligence platform. This system automatically fetches and imports threat intelligence feeds on configurable schedules with robust error handling, retry logic, and comprehensive logging.

## 🚀 **Features**

- **Automated Scheduling**: CRON-based scheduling with APScheduler
- **Robust Error Handling**: Exponential backoff, retry logic, and graceful failure handling
- **Authentication Support**: API keys, basic auth, and custom authentication methods
- **Comprehensive Logging**: File and stdout logging with configurable levels
- **Framework Integration**: Ready-to-use Flask and FastAPI integrations
- **Production Ready**: Systemd service, Docker support, and monitoring endpoints
- **Security Focused**: Input validation, rate limiting, and secure credential handling

## 📋 **Quick Start**

### 1. Install Dependencies

```bash
# Install required packages
pip install apscheduler requests

# Optional: For Flask/FastAPI integration
pip install flask fastapi uvicorn
```

### 2. Run Once (Testing)

```bash
# Run a single import cycle
python services/scheduled_importer.py --run-once

# Run with custom database
python services/scheduled_importer.py --run-once --db-path /path/to/db.sqlite
```

### 3. Run with Scheduler

```bash
# Start with default schedule (every 6 hours)
python services/scheduled_importer.py

# Custom CRON schedule (every 4 hours)
python services/scheduled_importer.py --cron "0 */4 * * *"
```

### 4. Flask Integration

```python
from flask import Flask
from services.background_tasks import setup_flask_importer

app = Flask(__name__)
importer = setup_flask_importer(app, cron_expression="0 */6 * * *")

if __name__ == '__main__':
    app.run()
```

### 5. FastAPI Integration

```python
from fastapi import FastAPI
from services.background_tasks import setup_fastapi_importer

app = FastAPI()
importer = setup_fastapi_importer(app, cron_expression="0 */6 * * *")

# Run with: uvicorn app:app
```

## 🔧 **Configuration**

### Environment Variables

```bash
# Database settings
export SENTINELFORGE_DB_PATH="/path/to/ioc_store.db"

# Logging settings
export SCHEDULER_LOG_FILE="scheduled_importer.log"
export SCHEDULER_LOG_LEVEL="INFO"

# Schedule settings
export SCHEDULER_CRON="0 */6 * * *"
export SCHEDULER_TIMEZONE="UTC"

# HTTP settings
export SCHEDULER_TIMEOUT="30"
export SCHEDULER_MAX_RETRIES="3"
export SCHEDULER_BASE_DELAY="1.0"
export SCHEDULER_MAX_DELAY="60.0"
```

### CRON Expressions

| Schedule | CRON Expression | Description |
|----------|----------------|-------------|
| Every hour | `0 * * * *` | Run at the top of every hour |
| Every 6 hours | `0 */6 * * *` | Run every 6 hours (default) |
| Daily at midnight | `0 0 * * *` | Run once per day at midnight |
| Business hours | `0 9-17 * * 1-5` | Every hour, 9-5, Mon-Fri |
| Weekly | `0 0 * * 0` | Every Sunday at midnight |

## 📁 **File Structure**

```
services/
├── scheduled_importer.py      # Core scheduler implementation
├── background_tasks.py        # Flask/FastAPI integration
└── ingestion.py              # Feed ingestion service

config/
└── scheduler_config.py       # Configuration management

scripts/
├── run_scheduler.py          # Standalone script
├── install_scheduler.sh      # Installation script
└── sentinelforge-scheduler.service  # Systemd service

examples/
├── flask_app_with_scheduler.py     # Flask example
└── fastapi_app_with_scheduler.py   # FastAPI example

docs/
└── SCHEDULER_README.md       # This file
```

## 🔄 **Usage Examples**

### Standalone Script

```bash
# Run once and exit
python scripts/run_scheduler.py --run-once

# Run as daemon with custom config
python scripts/run_scheduler.py --daemon \
    --cron "0 */4 * * *" \
    --db-path /opt/sentinelforge/db.sqlite \
    --log-file /var/log/sentinelforge/scheduler.log

# Test configuration
python scripts/run_scheduler.py --test-config
```

### Flask Application

```python
from flask import Flask
from services.background_tasks import FlaskScheduledImporter

app = Flask(__name__)

# Initialize with auto-start
importer = FlaskScheduledImporter(
    app=app,
    cron_expression="0 */6 * * *",
    auto_start=True
)

@app.route('/api/feeds/status')
def feed_status():
    return importer.run_manual_import()

if __name__ == '__main__':
    app.run()
```

### FastAPI Application

```python
from fastapi import FastAPI
from services.background_tasks import FastAPIScheduledImporter

app = FastAPI()

# Initialize with auto-start
importer = FastAPIScheduledImporter(
    app=app,
    cron_expression="0 */6 * * *",
    auto_start=True
)

@app.get("/api/feeds/status")
async def feed_status():
    return await importer.run_manual_import()
```

## 🐳 **Docker Deployment**

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY services/ ./services/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd --create-home --shell /bin/bash scheduler

# Set permissions
RUN chown -R scheduler:scheduler /app
USER scheduler

# Run scheduler
CMD ["python", "scripts/run_scheduler.py", "--daemon"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  scheduler:
    build: .
    environment:
      - SENTINELFORGE_DB_PATH=/data/ioc_store.db
      - SCHEDULER_CRON=0 */6 * * *
      - SCHEDULER_LOG_LEVEL=INFO
    volumes:
      - ./data:/data
      - ./logs:/var/log/sentinelforge
    restart: unless-stopped
```

## 🖥️ **Systemd Service**

### Installation

```bash
# Install as systemd service
sudo bash scripts/install_scheduler.sh

# Enable and start
sudo systemctl enable sentinelforge-scheduler
sudo systemctl start sentinelforge-scheduler

# Check status
sudo systemctl status sentinelforge-scheduler

# View logs
sudo journalctl -u sentinelforge-scheduler -f
```

### Manual Service Setup

```bash
# Copy service file
sudo cp scripts/sentinelforge-scheduler.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable sentinelforge-scheduler
sudo systemctl start sentinelforge-scheduler
```

## 📊 **Monitoring & API Endpoints**

### Health Check

```bash
# Check service health
curl http://localhost:5000/api/health

# Response
{
  "status": "healthy",
  "database": "connected",
  "feed_count": 11,
  "scheduler_running": true
}
```

### Manual Import

```bash
# Trigger manual import
curl -X POST http://localhost:5000/api/admin/feeds/import

# Import specific feed
curl -X POST http://localhost:5000/api/feeds/1/import
```

### Scheduler Control

```bash
# Get scheduler status
curl http://localhost:5000/api/admin/feeds/scheduler/status

# Start scheduler
curl -X POST http://localhost:5000/api/admin/feeds/scheduler/start

# Stop scheduler
curl -X POST http://localhost:5000/api/admin/feeds/scheduler/stop
```

## 🔍 **Troubleshooting**

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database path and permissions
   ls -la /path/to/ioc_store.db
   
   # Test database connectivity
   sqlite3 /path/to/ioc_store.db "SELECT COUNT(*) FROM threat_feeds;"
   ```

2. **Authentication Failures**
   ```bash
   # Check feed authentication configuration
   sqlite3 /path/to/ioc_store.db "SELECT name, requires_auth, auth_config FROM threat_feeds WHERE enabled=1;"
   ```

3. **Import Failures**
   ```bash
   # Check logs for specific errors
   tail -f scheduled_importer.log | grep ERROR
   
   # Test individual feed
   python -c "
   from services.scheduled_importer import ScheduledFeedImporter
   importer = ScheduledFeedImporter()
   feeds = importer.get_enabled_feeds()
   result = importer.import_feed(feeds[0])
   print(result)
   "
   ```

### Log Analysis

```bash
# View recent logs
tail -100 scheduled_importer.log

# Filter by log level
grep "ERROR" scheduled_importer.log
grep "WARNING" scheduled_importer.log

# Monitor real-time
tail -f scheduled_importer.log | grep -E "(ERROR|WARNING|SUCCESS)"
```

## 🔐 **Security Considerations**

- **Credentials**: Store API keys in environment variables, never in code
- **File Permissions**: Restrict access to configuration and log files
- **Network Security**: Use HTTPS for all external feed connections
- **Input Validation**: All IOC data is validated before database insertion
- **Rate Limiting**: Built-in protection against feed abuse
- **Audit Logging**: Complete trail of all import operations

## 📈 **Performance Tuning**

- **Batch Size**: Default 1000 IOCs per transaction (configurable)
- **Concurrent Imports**: Limit concurrent feed imports (default: 3)
- **Memory Usage**: ~100MB for 10,000 IOC processing
- **Database Optimization**: Use indexes on IOC value and type columns
- **Retry Strategy**: Exponential backoff with configurable delays

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.
