#!/usr/bin/env python3
"""
Simple SPA (Single Page Application) server for React apps.
Serves static files and falls back to index.html for client-side routing.
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    """Handler that serves static files and falls back to index.html for SPA routing."""

    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Remove leading slash for file system check
        file_path = path[1:] if path.startswith("/") else path

        # If no path, serve index.html
        if not file_path:
            file_path = "index.html"

        # Check if the requested file exists
        if os.path.isfile(file_path):
            # File exists, serve it normally
            return super().do_GET()

        # Check if it's a static asset (has file extension)
        if "." in os.path.basename(file_path):
            # It's a file request but file doesn't exist, return 404
            return super().do_GET()

        # It's likely a client-side route, serve index.html
        # Store original path for logging
        original_path = self.path
        self.path = "/index.html"
        print(f"SPA fallback: {original_path} -> /index.html")
        return super().do_GET()

    def do_HEAD(self):
        # Handle HEAD requests the same way as GET requests
        return self.do_GET()

    def end_headers(self):
        # Add CORS headers for API requests
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000

    # Change to the build directory
    build_dir = os.path.join(os.path.dirname(__file__), "build")
    if os.path.exists(build_dir):
        os.chdir(build_dir)
        print(f"Serving from: {build_dir}")
    else:
        print(f"Build directory not found: {build_dir}")
        sys.exit(1)

    # Start the server
    with socketserver.TCPServer(("", port), SPAHandler) as httpd:
        print(f"SPA server running at http://localhost:{port}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == "__main__":
    main()
