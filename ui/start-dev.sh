#!/bin/bash

echo "Starting React development server..."
echo "Current directory: $(pwd)"
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"

# Handle problematic HOST variable
if [ -n "$HOST" ]; then
    echo "Current HOST environment variable: $HOST"
    # Check if HOST is a valid hostname/IP that webpack-dev-server can bind to
    if [[ ! "$HOST" =~ ^(localhost|127\.0\.0\.1|0\.0\.0\.0)$ && ! "$HOST" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "Warning: HOST variable '$HOST' might be problematic. Overriding to 'localhost'."
        export HOST="localhost"
    fi
else
    # If HOST is not set, default to localhost
    export HOST="localhost"
fi

# Set environment variables for the React app
export PORT="${PORT:-3000}" # Use PORT from env or default to 3000
export BROWSER="none" # Prevent opening browser automatically
export NODE_OPTIONS="--max-old-space-size=4096" # Increase memory limit

echo "Effective environment variables for npm start:"
echo "  PORT=$PORT"
echo "  HOST=$HOST"
echo "  BROWSER=$BROWSER"
echo "  NODE_OPTIONS=$NODE_OPTIONS"

# Pre-flight check: Port
echo "Checking if port $PORT is in use..."
if lsof -i :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "Error: Port $PORT is already in use by another process."
    echo "Please stop the other process or choose a different port."
    exit 1
fi
echo "Port $PORT is free."

# Start the development server
echo "Running npm start..."
npm start

# Capture exit code
EXIT_CODE=$?
echo "npm start exited with code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
    echo "--------------------------------------------------"
    echo "Error: Development server failed to start or exited prematurely."
    echo "Common issues to check:"
    echo "1. HOST environment variable: Ensure it's 'localhost' or a valid IP. Current effective HOST: $HOST"
    echo "2. Port $PORT: Check if it became occupied during startup."
    echo "3. Webpack/Craco config: Review craco.config.js for schema mismatches (we've set allowedHosts: 'all')."
    echo "4. Memory: We've set NODE_OPTIONS to $NODE_OPTIONS. If it's a memory issue, system logs (Console.app on macOS) might have clues."
    echo "5. Node.js version: You are using $(node --version). Consider trying an LTS version (e.g., v20.x or v22.x) via nvm if problems persist."
    echo "6. Corrupted node_modules: Try removing node_modules and package-lock.json, then run 'npm install'."
    echo "--------------------------------------------------"
fi

exit $EXIT_CODE 