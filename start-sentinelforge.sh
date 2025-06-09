#!/bin/bash
# 🚀 SentinelForge Automated Startup Script
# Starts all required services in the correct order

echo "🚀 Starting SentinelForge Services"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to start
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Waiting for $service_name to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            echo -e " ${GREEN}✅ Started${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    echo -e " ${RED}❌ Failed to start${NC}"
    return 1
}

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
    echo -e "${RED}❌ Error: api_server.py not found${NC}"
    echo "Please run this script from the SentinelForge root directory"
    exit 1
fi

echo ""
echo "📋 Starting Services:"
echo "===================="

# 1. Start API Server
echo -e "${BLUE}1. Starting API Server (port 5059)...${NC}"
if check_port 5059; then
    echo -e "   ${YELLOW}⚠️  Port 5059 already in use${NC}"
else
    python3 api_server.py > api_server.log 2>&1 &
    API_PID=$!
    echo "   📝 API Server PID: $API_PID"
    
    if wait_for_service "API Server" 5059; then
        echo "   📄 Logs: api_server.log"
    else
        echo -e "   ${RED}❌ Failed to start API Server${NC}"
        exit 1
    fi
fi

# 2. Start React UI Server
echo -e "${BLUE}2. Starting React UI Server (port 3000)...${NC}"
if check_port 3000; then
    echo -e "   ${YELLOW}⚠️  Port 3000 already in use${NC}"
else
    cd ui/build
    python3 ../simple-spa-server.py 3000 > ../../react_ui.log 2>&1 &
    UI_PID=$!
    cd ../..
    echo "   📝 React UI PID: $UI_PID"
    
    if wait_for_service "React UI Server" 3000; then
        echo "   📄 Logs: react_ui.log"
    else
        echo -e "   ${RED}❌ Failed to start React UI Server${NC}"
        exit 1
    fi
fi

# 3. Start Timeline API (optional)
echo -e "${BLUE}3. Starting Timeline API (port 5101)...${NC}"
if check_port 5101; then
    echo -e "   ${YELLOW}⚠️  Port 5101 already in use${NC}"
else
    python3 alerts_timeline_api.py > timeline_api.log 2>&1 &
    TIMELINE_PID=$!
    echo "   📝 Timeline API PID: $TIMELINE_PID"
    
    if wait_for_service "Timeline API" 5101; then
        echo "   📄 Logs: timeline_api.log"
    else
        echo -e "   ${YELLOW}⚠️  Timeline API failed to start (optional service)${NC}"
    fi
fi

echo ""
echo "🔍 Running Health Check:"
echo "======================="

# Wait a moment for services to fully initialize
sleep 3

# Run health check
if [ -f "check-services.sh" ]; then
    ./check-services.sh
else
    echo "Health check script not found, performing basic checks..."
    
    # Basic connectivity test
    if curl -s -f http://localhost:3000/ > /dev/null; then
        echo -e "${GREEN}✅ React UI accessible${NC}"
    else
        echo -e "${RED}❌ React UI not accessible${NC}"
    fi
    
    if curl -s -f http://localhost:5059/api/session > /dev/null; then
        echo -e "${GREEN}✅ API Server accessible${NC}"
    else
        echo -e "${RED}❌ API Server not accessible${NC}"
    fi
fi

echo ""
echo "🎉 SentinelForge Startup Complete!"
echo "=================================="
echo -e "${GREEN}🌐 Access SentinelForge at: http://localhost:3000${NC}"
echo -e "${GREEN}🔐 Login with: admin / admin123${NC}"
echo ""
echo "📋 Service Management:"
echo "• View logs: tail -f *.log"
echo "• Stop services: pkill -f 'api_server.py|simple-spa-server.py|alerts_timeline_api.py'"
echo "• Health check: ./check-services.sh"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running and handle Ctrl+C
trap 'echo -e "\n🛑 Stopping all services..."; pkill -f "api_server.py|simple-spa-server.py|alerts_timeline_api.py"; exit 0' INT

# Wait indefinitely
while true; do
    sleep 1
done
