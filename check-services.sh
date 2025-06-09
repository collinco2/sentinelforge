#!/bin/bash
# 🔍 SentinelForge Service Health Check Script
# Verifies all required services are running and accessible

echo "🔍 SentinelForge Service Health Check"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running on a port
check_service() {
    local service_name=$1
    local port=$2
    local endpoint=$3
    
    echo -n "Checking $service_name (port $port)... "
    
    if curl -s -f "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        return 0
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        return 1
    fi
}

# Function to check authentication
check_auth() {
    echo -n "Testing authentication... "
    
    response=$(curl -s -X POST http://localhost:3000/api/login \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}' \
        -w "%{http_code}")
    
    if [[ "$response" == *"200" ]]; then
        echo -e "${GREEN}✅ WORKING${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Check all services
echo ""
echo "📋 Service Status:"
echo "=================="

all_good=true

# Check React UI Server
if ! check_service "React UI Server" "3000" "/"; then
    all_good=false
    echo "   💡 Start with: cd ui/build && python3 ../simple-spa-server.py 3000"
fi

# Check API Server
if ! check_service "API Server" "5059" "/api/session"; then
    all_good=false
    echo "   💡 Start with: python3 api_server.py"
fi

# Check Timeline API (optional)
if ! check_service "Timeline API" "5101" "/api/alerts/timeline"; then
    echo "   ℹ️  Timeline API is optional but recommended"
fi

echo ""
echo "🔐 Authentication Test:"
echo "======================"

# Test authentication if API server is running
if ! check_auth; then
    all_good=false
    echo "   💡 Ensure API server is running and database is accessible"
fi

echo ""
echo "📊 Summary:"
echo "==========="

if $all_good; then
    echo -e "${GREEN}✅ All critical services are running correctly!${NC}"
    echo "🌐 Access SentinelForge at: http://localhost:3000"
    echo "🔐 Login with: admin / admin123"
else
    echo -e "${RED}❌ Some services need attention${NC}"
    echo "Please start the missing services and run this check again."
fi

echo ""
echo "📋 Available User Accounts:"
echo "=========================="
echo "• admin / admin123 (Full access)"
echo "• analyst1 / analyst123 (Risk score overrides)"
echo "• auditor1 / auditor123 (Audit trail access)"
echo "• viewer1 / viewer123 (Read-only access)"
