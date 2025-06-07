#!/bin/bash

# SentinelForge UI Server Manager
# Handles switching between development and production servers safely

set -e

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

# Function to check what's running on port 3000
check_port_3000() {
    local pid=$(lsof -ti :3000 2>/dev/null || echo "")
    if [ -z "$pid" ]; then
        echo "free"
        return 0
    fi
    
    local process=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
    local args=$(ps -p $pid -o args= 2>/dev/null || echo "")
    
    if [[ "$args" == *"spa-server.py"* ]]; then
        echo "production:$pid"
    elif [[ "$args" == *"craco start"* ]] || [[ "$args" == *"npm start"* ]]; then
        echo "development:$pid"
    else
        echo "other:$pid"
    fi
}

# Function to stop a specific server type
stop_server() {
    local server_type=$1
    local port_status=$(check_port_3000)
    
    if [ "$port_status" = "free" ]; then
        print_status "Port 3000 is already free"
        return 0
    fi
    
    local current_type=$(echo $port_status | cut -d: -f1)
    local pid=$(echo $port_status | cut -d: -f2)
    
    if [ "$server_type" = "all" ] || [ "$server_type" = "$current_type" ]; then
        print_status "Stopping $current_type server (PID: $pid)..."
        kill $pid 2>/dev/null || true
        sleep 2
        
        # Verify it's stopped
        if [ "$(check_port_3000)" = "free" ]; then
            print_success "$current_type server stopped successfully"
        else
            print_warning "Force killing server..."
            kill -9 $pid 2>/dev/null || true
            sleep 1
        fi
    fi
}

# Function to start production server
start_production() {
    print_status "Starting production server..."
    
    # Stop any existing servers
    stop_server "all"
    
    # Build the React app
    print_status "Building React application..."
    npm run build
    
    # Start production server
    print_status "Starting spa-server.py on port 3000..."
    python3 spa-server.py 3000 &
    
    # Wait a moment and verify
    sleep 3
    local port_status=$(check_port_3000)
    if [[ "$port_status" == "production:"* ]]; then
        print_success "Production server started successfully!"
        print_status "Access the application at: http://localhost:3000"
        print_status "Server type: Production (built React app)"
    else
        print_error "Failed to start production server"
        exit 1
    fi
}

# Function to start development server
start_development() {
    print_status "Starting development server..."
    
    # Stop any existing servers
    stop_server "all"
    
    # Start development server
    print_status "Starting React development server..."
    print_warning "This will start in development mode with hot reload"
    print_warning "Use Ctrl+C to stop the development server"
    
    npm start
}

# Function to show current status
show_status() {
    local port_status=$(check_port_3000)
    
    echo "=== SentinelForge UI Server Status ==="
    echo ""
    
    if [ "$port_status" = "free" ]; then
        print_status "Port 3000: FREE"
        print_status "No UI server is currently running"
    else
        local server_type=$(echo $port_status | cut -d: -f1)
        local pid=$(echo $port_status | cut -d: -f2)
        
        case $server_type in
            "production")
                print_success "Port 3000: PRODUCTION SERVER (PID: $pid)"
                print_status "Serving: Built React app from ui/build/"
                print_status "URL: http://localhost:3000"
                ;;
            "development")
                print_success "Port 3000: DEVELOPMENT SERVER (PID: $pid)"
                print_status "Serving: Live React app with hot reload"
                print_status "URL: http://localhost:3000"
                ;;
            "other")
                print_warning "Port 3000: OTHER PROCESS (PID: $pid)"
                print_warning "Unknown process is using port 3000"
                ;;
        esac
    fi
    
    echo ""
    echo "Available commands:"
    echo "  ./server-manager.sh prod     - Start production server"
    echo "  ./server-manager.sh dev      - Start development server"
    echo "  ./server-manager.sh stop     - Stop current server"
    echo "  ./server-manager.sh status   - Show this status"
}

# Main script logic
case "${1:-status}" in
    "prod"|"production")
        start_production
        ;;
    "dev"|"development")
        start_development
        ;;
    "stop")
        stop_server "all"
        print_success "All servers stopped"
        ;;
    "status")
        show_status
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        echo "Usage: $0 {prod|dev|stop|status}"
        echo ""
        echo "Commands:"
        echo "  prod     - Start production server (spa-server.py)"
        echo "  dev      - Start development server (npm start)"
        echo "  stop     - Stop any running server"
        echo "  status   - Show current server status"
        exit 1
        ;;
esac
