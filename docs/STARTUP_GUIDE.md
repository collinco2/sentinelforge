# SentinelForge Startup Quick Reference

## 🚀 One-Command Start
```bash
./start-all-services.sh
```

## 📋 Service Ports
| Service | Port | URL |
|---------|------|-----|
| API Server | 5059 | http://localhost:5059 |
| React UI | 3000 | http://localhost:3000 |
| Dashboard | 5050 | http://localhost:5050 |
| Timeline API | 5101 | http://localhost:5101 |
| TAXII API | 8000 | http://localhost:8000 |

## 🔧 Quick Commands
```bash
# Start all services
./start-all-services.sh start

# Check status
./start-all-services.sh status

# Stop all services
./start-all-services.sh stop

# Restart all services
./start-all-services.sh restart
```

## 🔍 Health Checks
```bash
# Quick API test
curl -s http://localhost:5059/api/iocs | head -5

# Check all ports
lsof -i :5059 :3000 :5050 :5101 :8000
```

## 🛠 Common Fixes
```bash
# Port in use
lsof -i :PORT && kill -9 PID

# React issues
cd sentinelforge-ui && npm run build && python3 spa-server.py 3000

# Virtual environment
source venv/bin/activate

# Permissions
chmod +x start-all-services.sh
```

## 🛑 Emergency Stop
```bash
./start-all-services.sh stop
# OR
pkill -f "api_server.py|spa-server.py|dashboard|alerts_timeline|taxii"
```

## 📁 Key Files
- `start-all-services.sh` - Main startup script
- `api_server.py` - Core API (port 5059)
- `sentinelforge-ui/spa-server.py` - React UI (port 3000)
- `dashboard/app.py` - Dashboard (port 5050)
- `alerts_timeline_api.py` - Timeline (port 5101)
- `sentinelforge/api/taxii.py` - TAXII API (port 8000)

## 💡 Best Practices
1. Always use `start-all-services.sh` for consistency
2. Check service status before starting
3. Use production builds even in development
4. Monitor `.log` files for issues
5. Test API endpoints before UI work

---
See [README.md](../README.md) for complete documentation.
