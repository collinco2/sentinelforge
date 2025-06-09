#!/bin/bash

# SentinelForge React UI Health Check Script
# Performs comprehensive health checks on the running server

set -e

# Configuration
PORT=3000
TIMEOUT=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is listening
check_port_listening() {
    if nc -z localhost $PORT 2>/dev/null; then
        return 0  # Port is listening
    else
        return 1  # Port is not listening
    fi
}

# Function to check HTTP response
check_http_response() {
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT --max-time $TIMEOUT http://localhost:$PORT 2>/dev/null)
    if [ "$response_code" = "200" ]; then
        return 0  # HTTP OK
    else
        return 1  # HTTP error
    fi
}

# Function to check if server process is running
check_server_process() {
    if pgrep -f "spa-server.py" > /dev/null; then
        return 0  # Process running
    else
        return 1  # Process not running
    fi
}

# Function to test specific routes
test_routes() {
    local routes=("/" "/button-test" "/dashboard" "/settings")
    local failed_routes=()
    
    for route in "${routes[@]}"; do
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT --max-time $TIMEOUT "http://localhost:$PORT$route" 2>/dev/null)
        if [ "$response_code" != "200" ]; then
            failed_routes+=("$route")
        fi
    done
    
    if [ ${#failed_routes[@]} -eq 0 ]; then
        return 0  # All routes OK
    else
        echo "${failed_routes[@]}"
        return 1  # Some routes failed
    fi
}

# Main health check function
perform_health_check() {
    echo "============================================================"
    echo "🏥 SentinelForge React UI Health Check"
    echo "============================================================"
    echo "🕐 $(date)"
    echo "============================================================"
    
    # Check 1: Server process
    print_status "Checking server process..."
    if check_server_process; then
        local pid=$(pgrep -f "spa-server.py")
        print_success "Server process running (PID: $pid)"
    else
        print_error "Server process not running"
        return 1
    fi
    
    # Check 2: Port listening
    print_status "Checking port $PORT..."
    if check_port_listening; then
        print_success "Port $PORT is listening"
    else
        print_error "Port $PORT is not listening"
        return 1
    fi
    
    # Check 3: HTTP response
    print_status "Testing HTTP connectivity..."
    if check_http_response; then
        print_success "HTTP server responding correctly"
    else
        print_error "HTTP server not responding"
        return 1
    fi
    
    # Check 4: Route testing
    print_status "Testing application routes..."
    if failed_routes=$(test_routes); then
        print_success "All routes responding correctly"
    else
        print_error "Failed routes: $failed_routes"
        return 1
    fi
    
    # Check 5: Resource usage
    print_status "Checking resource usage..."
    local pid=$(pgrep -f "spa-server.py")
    local cpu_usage=$(ps -p $pid -o %cpu= | tr -d ' ')
    local mem_usage=$(ps -p $pid -o %mem= | tr -d ' ')
    print_success "CPU: ${cpu_usage}%, Memory: ${mem_usage}%"
    
    echo "============================================================"
    print_success "🎉 All health checks passed!"
    echo "============================================================"
    echo "📊 Server Status: HEALTHY"
    echo "🌐 Access URL: http://localhost:$PORT"
    echo "🧪 Test Page: http://localhost:$PORT/button-test"
    echo "📋 Dashboard: http://localhost:$PORT/dashboard"
    echo "⚙️  Settings: http://localhost:$PORT/settings"
    echo "============================================================"
    
    return 0
}

# Run health check
if perform_health_check; then
    exit 0
else
    echo "============================================================"
    print_error "❌ Health check failed!"
    echo "============================================================"
    print_status "Suggested actions:"
    echo "  1. Check server logs for errors"
    echo "  2. Restart server: ./server-manager.sh restart"
    echo "  3. Check for port conflicts: lsof -i :$PORT"
    echo "============================================================"
    exit 1
fi
