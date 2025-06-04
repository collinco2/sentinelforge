# SentinelForge - Threat Intelligence Platform

SentinelForge is a comprehensive threat intelligence platform that provides IOC (Indicator of Compromise) management, alert processing, and threat analysis capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Virtual environment activated (`source venv/bin/activate`)

### One-Command Startup
```bash
./start-all-services.sh
```

This will start all services in production configuration and display their status.

## 📋 Service Architecture

SentinelForge consists of 5 core services that work together:

| Service | Port | Purpose | Technology |
|---------|------|---------|------------|
| **API Server** | 5059 | Core REST API for IOCs and alerts | Flask |
| **React UI** | 3000 | Main web interface | React + TypeScript |
| **Dashboard** | 5050 | Legacy Flask dashboard | Flask |
| **Alerts Timeline API** | 5101 | Alert timeline data service | Flask |
| **TAXII API** | 8000 | STIX/TAXII threat intelligence feed | FastAPI |

### Service URLs
- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:5059
- **Legacy Dashboard**: http://localhost:5050
- **Alerts Timeline**: http://localhost:5101
- **TAXII Feed**: http://localhost:8000

## 🔧 Manual Startup (Development)

### Option 1: Production Configuration (Recommended)
```bash
# Start all services with production settings
./start-all-services.sh start

# Check service status
./start-all-services.sh status

# Stop all services
./start-all-services.sh stop

# Restart all services
./start-all-services.sh restart
```

### Option 2: Individual Service Startup
```bash
# 1. Start API Server (Required)
source venv/bin/activate
python3 api_server.py

# 2. Start React UI (Production Build)
cd sentinelforge-ui
npm run build
python3 spa-server.py 3000

# 3. Start Dashboard (Optional)
source venv/bin/activate
python3 dashboard/app.py

# 4. Start Alerts Timeline API (Optional)
source venv/bin/activate
python3 alerts_timeline_api.py --port 5101

# 5. Start TAXII API (Optional)
source venv/bin/activate
python3 -m sentinelforge.api.taxii
```

## 🔍 Service Health Checks

### Quick Status Check
```bash
# Check all services at once
./start-all-services.sh status

# Manual health checks
curl -s http://localhost:5059/api/iocs | head -5    # API Server
curl -s -I http://localhost:3000                    # React UI
curl -s -I http://localhost:5050                    # Dashboard
curl -s http://localhost:5101/api/timeline | head -5 # Timeline API
curl -s http://localhost:8000/docs                  # TAXII API
```

### Process Verification
```bash
# Check if services are running
lsof -i :5059  # API Server
lsof -i :3000  # React UI
lsof -i :5050  # Dashboard
lsof -i :5101  # Alerts Timeline
lsof -i :8000  # TAXII API
```

## 🛠 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using the port
lsof -i :PORT_NUMBER

# Kill the process
kill -9 PID_NUMBER

# Or use the stop script
./start-all-services.sh stop
```

#### 2. React Development Server Issues
If the React dev server fails to start:
```bash
cd sentinelforge-ui

# Build production version instead
npm run build
python3 spa-server.py 3000
```

#### 3. Database Connection Issues
```bash
# Check if database exists
ls -la ioc_store.db

# Recreate database if needed
python3 -c "from sentinelforge.storage import engine, Base; Base.metadata.create_all(engine)"
```

#### 4. Virtual Environment Issues
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Verify Python path
which python3

# Install dependencies if needed
pip install -r requirements.txt
```

#### 5. Permission Issues
```bash
# Make startup script executable
chmod +x start-all-services.sh

# Fix file permissions
chmod 644 *.py
```

### Service-Specific Troubleshooting

#### API Server (Port 5059)
- **Issue**: "Address already in use"
- **Solution**: `lsof -i :5059` and kill existing process
- **Logs**: Check `api_server.log`

#### React UI (Port 3000)
- **Issue**: Connection refused
- **Solution**: Use production build with `spa-server.py`
- **Logs**: Check browser console and terminal output

#### Dashboard (Port 5050)
- **Issue**: Flask app won't start
- **Solution**: Check virtual environment and dependencies
- **Logs**: Check `dashboard.log`

## 🔒 Security Notes

### Development vs Production
- **Development**: Uses `start-all-services.sh` with production builds
- **Production**: Same configuration, but consider:
  - Change default API keys in `.env`
  - Use proper SSL certificates
  - Configure firewall rules
  - Use production WSGI server for Flask apps

### Default Credentials
- **API Key**: `super-secret-token` (change in `.env`)
- **Database**: SQLite file `ioc_store.db`

## 📁 Important Files

```
sentinelforge/
├── start-all-services.sh          # Main startup script
├── api_server.py                  # Core API server
├── dashboard/app.py               # Legacy dashboard
├── alerts_timeline_api.py         # Timeline API
├── sentinelforge/api/taxii.py     # TAXII API
├── sentinelforge-ui/              # React frontend
│   ├── spa-server.py             # Production server
│   └── build/                    # Production build
├── ioc_store.db                  # SQLite database
├── requirements.txt              # Python dependencies
└── .env                          # Environment variables
```

## 🚦 Startup Sequence

The recommended startup order (handled automatically by `start-all-services.sh`):

1. **API Server** (5059) - Core data services
2. **Dashboard** (5050) - Legacy interface
3. **Alerts Timeline API** (5101) - Timeline data
4. **React UI** (3000) - Main interface

**Note**: TAXII API (8000) is optional and started separately if needed.

## 💡 Development Tips

- **Always use production configuration** even during development
- **Check service status** before starting new instances
- **Use the startup script** for consistent environment
- **Monitor logs** in respective `.log` files
- **Test API endpoints** before UI development

## 🛑 Safe Shutdown

### Graceful Shutdown (Recommended)
```bash
# Stop all services gracefully
./start-all-services.sh stop
```

### Emergency Shutdown
```bash
# Kill all SentinelForge processes
pkill -f "api_server.py"
pkill -f "spa-server.py"
pkill -f "dashboard/app.py"
pkill -f "alerts_timeline_api.py"
pkill -f "sentinelforge.api.taxii"

# Clean up PID files
rm -f .*.pid
```

### Verify Shutdown
```bash
# Check that all ports are free
lsof -i :5059 :3000 :5050 :5101 :8000
```

---

For additional documentation, see the `docs/` directory.