# SentinelForge UI Server Guide

## 🚨 IMPORTANT: Two Different Servers!

SentinelForge has **TWO DIFFERENT WAYS** to serve the React UI. Understanding the difference is crucial to avoid confusion.

## 🏭 Production Server (Recommended)

**What it is**: Serves the built React application from `ui/build/` directory
**Command**: `python3 spa-server.py 3000`
**Port**: 3000
**When to use**: Normal usage, testing, production deployment

### ✅ Advantages:
- Fast and stable
- Matches production environment exactly
- Includes API proxy to backend services
- No development dependencies needed

### ❌ Disadvantages:
- Requires rebuild after code changes
- No hot reload

### 🔧 How to Start:
```bash
cd ui
npm run build              # Build the React app
python3 spa-server.py 3000 # Start production server
```

### 🎯 How to Identify:
- Console shows: "🏭 SentinelForge PRODUCTION Server"
- Browser title: "SentinelForge" (no dev indicators)
- Sidebar shows: "SentinelForge" (no development badge)

## 🔧 Development Server (Development Only)

**What it is**: Live React development server with hot reload
**Command**: `npm start`
**Port**: 3000 (same as production!)
**When to use**: Only when actively developing React components

### ✅ Advantages:
- Hot reload - instant code changes
- React development tools
- Detailed error messages

### ❌ Disadvantages:
- Slower than production
- Development-only features
- Requires Node.js and npm dependencies

### 🔧 How to Start:
```bash
cd ui
npm start  # Starts development server
```

### 🎯 How to Identify:
- Console shows: "🚀 SentinelForge UI Server: DEVELOPMENT"
- Sidebar shows: "🔧 Development Mode" badge
- Browser console has React development messages

## ⚠️ Port Conflict Problem

**BOTH SERVERS USE PORT 3000!** This causes major confusion:

### Problem Scenarios:
1. **Production running + Start development**: Development fails silently, browser still shows production
2. **Development running + Start production**: Production can't start, error messages
3. **Wrong server running**: You make code changes but don't see them (because production is serving old build)

### 🔍 How to Check What's Running:
```bash
# Check what's using port 3000
lsof -i :3000

# Look for:
# - "Python spa-server.py" = Production server
# - "node" or "npm start" = Development server
```

## 🔄 Server Management Commands

### Using the Smart Manager (Recommended):
```bash
cd ui

# Check current status
./server-manager.sh status

# Start production server (stops any existing server first)
./server-manager.sh prod

# Start development server (stops any existing server first)  
./server-manager.sh dev

# Stop any running server
./server-manager.sh stop
```

### Using NPM Scripts:
```bash
cd ui

# Start production (auto-stops dev, builds, starts prod)
npm run start:prod

# Start development (auto-stops prod, starts dev)
npm run start:dev

# Check if port is free
npm run server:status
```

### Manual Commands:
```bash
# Stop any server on port 3000
lsof -i :3000  # Get PID
kill <PID>     # Stop the process

# Start production manually
npm run build
python3 spa-server.py 3000

# Start development manually
npm start
```

## 🎯 Quick Decision Guide

### Use Production Server When:
- ✅ Normal daily usage
- ✅ Testing features
- ✅ Demonstrating the application
- ✅ You want fast, stable performance
- ✅ You're not actively changing React code

### Use Development Server When:
- ✅ Actively developing React components
- ✅ Need hot reload for rapid iteration
- ✅ Debugging React-specific issues
- ✅ Working on UI/UX changes

## 🚨 Common Mistakes to Avoid

1. **Making code changes while production server is running**
   - Changes won't appear until you rebuild and restart
   
2. **Starting development server when production is running**
   - Development server fails silently, you see old production version
   
3. **Forgetting to build before starting production**
   - Production serves old version of your code
   
4. **Not checking which server is running**
   - Leads to confusion about why changes aren't appearing

## 🛠 Troubleshooting

### "My changes aren't showing up!"
1. Check which server is running: `./server-manager.sh status`
2. If production is running: Stop it, rebuild, restart it
3. If development is running: Changes should appear automatically

### "Port 3000 is already in use"
1. Check what's using it: `lsof -i :3000`
2. Stop the existing process: `kill <PID>`
3. Start your desired server

### "Can't access the application"
1. Check if any server is running: `lsof -i :3000`
2. If nothing is running: Start production server
3. If something else is running: Stop it and start SentinelForge server

## 📋 Best Practices

1. **Default to production server** for normal usage
2. **Use the server manager script** to avoid conflicts
3. **Always check status** before starting a server
4. **Build before production** to include latest changes
5. **Use development only when actively coding** React components

---

**Remember**: When in doubt, use the production server! It's faster, more stable, and matches the real deployment environment.
