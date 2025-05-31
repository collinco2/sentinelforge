#!/bin/bash

# SentinelForge - Unified Service Startup Script
# This script starts all the necessary services for the SentinelForge platform

set -e  # Exit on any error

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

# Function to check if a port is in use
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -i :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port is already in use (may be $service_name already running)"
        return 1
    else
        print_status "Port $port is available"
        return 0
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready on port $port..."

    while [ $attempt -le $max_attempts ]; do
        # For React development server, check if port is listening instead of HTTP response
        if [ "$service_name" = "React UI" ]; then
            if lsof -i :$port -sTCP:LISTEN >/dev/null 2>&1; then
                print_success "$service_name is ready on port $port"
                return 0
            fi
        else
            # For API services, check HTTP response
            if curl -s http://localhost:$port >/dev/null 2>&1; then
                print_success "$service_name is ready on port $port"
                return 0
            fi
        fi

        if [ $((attempt % 5)) -eq 0 ]; then
            print_status "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
        fi

        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Function to start API server
start_api_server() {
    print_status "Starting API Server on port 5059..."

    if ! check_port 5059 "API Server"; then
        print_warning "API Server may already be running on port 5059"
        return 0
    fi

    # Activate virtual environment and start API server in background
    source venv/bin/activate && python3 api_server.py > api_server.log 2>&1 &
    API_PID=$!
    echo $API_PID > .api_server.pid

    print_status "API Server started with PID $API_PID"

    # Wait for API server to be ready
    if wait_for_service 5059 "API Server"; then
        print_success "API Server is running successfully"
        return 0
    else
        print_error "API Server failed to start"
        return 1
    fi
}

# Function to start React UI (Production Build)
start_react_ui() {
    print_status "Starting React UI (Production) on port 3000..."

    if ! check_port 3000 "React UI"; then
        print_warning "React UI may already be running on port 3000"
        return 0
    fi

    # Change to sentinelforge-ui directory
    cd sentinelforge-ui

    # Check if production build exists
    if [ ! -d "build" ]; then
        print_status "Production build not found. Creating production build..."
        npm run build
        if [ $? -ne 0 ]; then
            print_error "Failed to create production build"
            cd ..
            return 1
        fi
    fi

    # Use our custom SPA server instead of serve
    # Start production server in background using custom SPA server
    python3 spa-server.py 3000 > ../react_ui.log 2>&1 &
    REACT_PID=$!
    echo $REACT_PID > ../.react_ui.pid

    print_status "React UI (Production) started with PID $REACT_PID"

    # Go back to root directory
    cd ..

    # Wait for React UI to be ready
    if wait_for_service 3000 "React UI"; then
        print_success "React UI (Production) is running successfully"
        return 0
    else
        print_error "React UI failed to start"
        return 1
    fi
}

# Function to start Dashboard (Flask)
start_dashboard() {
    print_status "Starting Dashboard on port 5050..."

    if ! check_port 5050 "Dashboard"; then
        print_warning "Dashboard may already be running on port 5050"
        return 0
    fi

    # Activate virtual environment and start Dashboard in background
    source venv/bin/activate && python3 dashboard/app.py > dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    echo $DASHBOARD_PID > .dashboard.pid

    print_status "Dashboard started with PID $DASHBOARD_PID"

    # Wait for Dashboard to be ready
    if wait_for_service 5050 "Dashboard"; then
        print_success "Dashboard is running successfully"
        return 0
    else
        print_error "Dashboard failed to start"
        return 1
    fi
}

# Function to start Alerts Timeline API
start_alerts_timeline_api() {
    print_status "Starting Alerts Timeline API on port 5101..."

    if ! check_port 5101 "Alerts Timeline API"; then
        print_warning "Alerts Timeline API may already be running on port 5101"
        return 0
    fi

    # Activate virtual environment and start alerts timeline API
    source venv/bin/activate
    python3 alerts_timeline_api.py --port 5101 > alerts_timeline_api.log 2>&1 &
    ALERTS_API_PID=$!
    echo $ALERTS_API_PID > .alerts_timeline_api.pid

    print_status "Alerts Timeline API started with PID $ALERTS_API_PID"

    # Wait for Alerts Timeline API to be ready
    if wait_for_service 5101 "Alerts Timeline API"; then
        print_success "Alerts Timeline API is running successfully"
        return 0
    else
        print_error "Alerts Timeline API failed to start"
        return 1
    fi
}

# Function to display running services
show_services() {
    echo ""
    print_success "=== SentinelForge Services Status ==="
    echo ""
    
    if [ -f .api_server.pid ] && kill -0 $(cat .api_server.pid) 2>/dev/null; then
        print_success "✓ API Server: http://localhost:5059 (PID: $(cat .api_server.pid))"
    else
        print_error "✗ API Server: Not running"
    fi
    
    if [ -f .react_ui.pid ] && kill -0 $(cat .react_ui.pid) 2>/dev/null; then
        print_success "✓ React UI: http://localhost:3000 (PID: $(cat .react_ui.pid))"
    else
        print_error "✗ React UI: Not running"
    fi
    
    if [ -f .dashboard.pid ] && kill -0 $(cat .dashboard.pid) 2>/dev/null; then
        print_success "✓ Dashboard: http://localhost:5050 (PID: $(cat .dashboard.pid))"
    else
        print_error "✗ Dashboard: Not running"
    fi

    if [ -f .alerts_timeline_api.pid ] && kill -0 $(cat .alerts_timeline_api.pid) 2>/dev/null; then
        print_success "✓ Alerts Timeline API: http://localhost:5101 (PID: $(cat .alerts_timeline_api.pid))"
    else
        print_error "✗ Alerts Timeline API: Not running"
    fi

    echo ""
    print_status "Main application URL: http://localhost:3000"
    print_status "API documentation: http://localhost:5059"
    print_status "Dashboard: http://localhost:5050"
    print_status "Alerts Timeline API: http://localhost:5101"
    echo ""
}

# Function to stop all services
stop_services() {
    print_status "Stopping all SentinelForge services..."
    
    # Stop API Server
    if [ -f .api_server.pid ]; then
        API_PID=$(cat .api_server.pid)
        if kill -0 $API_PID 2>/dev/null; then
            kill $API_PID
            print_status "Stopped API Server (PID: $API_PID)"
        fi
        rm -f .api_server.pid
    fi
    
    # Stop React UI
    if [ -f .react_ui.pid ]; then
        REACT_PID=$(cat .react_ui.pid)
        if kill -0 $REACT_PID 2>/dev/null; then
            kill $REACT_PID
            print_status "Stopped React UI (PID: $REACT_PID)"
        fi
        rm -f .react_ui.pid
    fi
    
    # Stop Dashboard
    if [ -f .dashboard.pid ]; then
        DASHBOARD_PID=$(cat .dashboard.pid)
        if kill -0 $DASHBOARD_PID 2>/dev/null; then
            kill $DASHBOARD_PID
            print_status "Stopped Dashboard (PID: $DASHBOARD_PID)"
        fi
        rm -f .dashboard.pid
    fi

    # Stop Alerts Timeline API
    if [ -f .alerts_timeline_api.pid ]; then
        ALERTS_API_PID=$(cat .alerts_timeline_api.pid)
        if kill -0 $ALERTS_API_PID 2>/dev/null; then
            kill $ALERTS_API_PID
            print_status "Stopped Alerts Timeline API (PID: $ALERTS_API_PID)"
        fi
        rm -f .alerts_timeline_api.pid
    fi

    print_success "All services stopped"
}

# Main script logic
case "${1:-start}" in
    "start")
        print_status "Starting SentinelForge services..."
        echo ""
        
        # Start services in order
        start_api_server
        sleep 3
        start_dashboard
        sleep 3
        start_alerts_timeline_api
        sleep 3
        start_react_ui

        show_services

        print_status "Main application URL: http://localhost:3000"
        print_status "API documentation: http://localhost:5059"
        print_status "Dashboard: http://localhost:5050"
        print_status "Alerts Timeline API: http://localhost:5101"
        echo ""
        print_status "All services started successfully!"
        print_status "Press Ctrl+C to stop all services"
        
        # Wait for interrupt
        trap stop_services INT TERM
        wait
        ;;
        
    "stop")
        stop_services
        ;;
        
    "status")
        show_services
        ;;
        
    "restart")
        stop_services
        sleep 2
        $0 start
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all SentinelForge services"
        echo "  stop    - Stop all SentinelForge services"
        echo "  status  - Show status of all services"
        echo "  restart - Restart all services"
        exit 1
        ;;
esac
