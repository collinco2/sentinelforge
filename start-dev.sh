#!/bin/bash

echo "Starting React development server..."
echo "Current directory: $(pwd)"
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"

# Handle problematic HOST variable
if [ -n "$HOST" ]; then
    echo "Current HOST variable: $HOST"
    # Check if HOST is a valid hostname/IP
    if [[ ! "$HOST" =~ ^(localhost|127\.0\.0\.1|0\.0\.0\.0|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})$ ]]; then
        echo "Invalid HOST detected. Unsetting it."
        unset HOST
    fi
fi

# Set environment variables
export PORT=3000
export BROWSER=none
export NODE_OPTIONS="--max-old-space-size=4096"
# Explicitly set HOST to localhost if not set
export HOST="${HOST:-localhost}"

echo "Environment variables:"
echo "  PORT=$PORT"
echo "  HOST=$HOST"
echo "  BROWSER=$BROWSER"
echo "  NODE_OPTIONS=$NODE_OPTIONS"

# Start the development server
echo "Running npm start..."
npm start

# Capture exit code
EXIT_CODE=$?
echo "npm start exited with code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
    echo "Error: Development server failed to start"
    echo "Checking for common issues..."
    
    # Check if port is in use
    lsof -i :3000 && echo "Port 3000 is already in use!"
    
    # Check node_modules
    [ ! -d "node_modules" ] && echo "node_modules directory not found!"
    
    # Check package.json
    [ ! -f "package.json" ] && echo "package.json not found!"
fi

exit $EXIT_CODE 