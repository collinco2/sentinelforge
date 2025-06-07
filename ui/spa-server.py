#!/usr/bin/env python3
"""
Simple SPA (Single Page Application) server for React apps.
Serves static files and falls back to index.html for client-side routing.
"""

import http.server
import socketserver
import os
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    """Handler that serves static files and falls back to index.html for SPA routing."""

    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Check if this is an API request
        if path.startswith("/api/"):
            return self.proxy_api_request()

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

    def proxy_api_request(self):
        """Proxy API requests to the appropriate backend server."""
        # Route timeline requests to timeline API server
        if self.path.startswith("/api/alerts/timeline"):
            api_server_url = "http://localhost:5101"
        else:
            # Route all other API requests to main API server
            api_server_url = "http://localhost:5059"

        target_url = f"{api_server_url}{self.path}"

        try:
            print(f"Proxying API request: {self.path} -> {target_url}")

            # Read request body for POST/PATCH/PUT requests
            request_body = None
            if self.command in ["POST", "PATCH", "PUT"]:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length > 0:
                    request_body = self.rfile.read(content_length)

            # Create the request with method and body
            req = urllib.request.Request(
                target_url, data=request_body, method=self.command
            )

            # Copy headers from the original request
            for header, value in self.headers.items():
                if header.lower() not in ["host", "connection"]:
                    req.add_header(header, value)

            # Make the request
            with urllib.request.urlopen(req) as response:
                # Send response status
                self.send_response(response.getcode())

                # Copy response headers
                for header, value in response.headers.items():
                    if header.lower() not in ["connection", "transfer-encoding"]:
                        self.send_header(header, value)

                # Add CORS headers
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header(
                    "Access-Control-Allow-Methods",
                    "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                )
                self.send_header(
                    "Access-Control-Allow-Headers",
                    "Content-Type, Authorization, X-Session-Token",
                )

                self.end_headers()

                # Copy response body
                self.wfile.write(response.read())

        except urllib.error.HTTPError as e:
            print(f"API request failed: {e}")
            self.send_error(e.code, e.reason)
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_error(500, "Internal Server Error")

    def do_HEAD(self):
        # Handle HEAD requests the same way as GET requests
        return self.do_GET()

    def do_POST(self):
        """Handle POST requests by proxying to API server."""
        if self.path.startswith("/api/"):
            return self.proxy_api_request()
        else:
            self.send_error(404, "Not Found")

    def do_PATCH(self):
        """Handle PATCH requests by proxying to API server."""
        if self.path.startswith("/api/"):
            return self.proxy_api_request()
        else:
            self.send_error(404, "Not Found")

    def do_PUT(self):
        """Handle PUT requests by proxying to API server."""
        if self.path.startswith("/api/"):
            return self.proxy_api_request()
        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        """Handle DELETE requests by proxying to API server."""
        if self.path.startswith("/api/"):
            return self.proxy_api_request()
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        if self.path.startswith("/api/"):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header(
                "Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            self.send_header(
                "Access-Control-Allow-Headers",
                "Content-Type, Authorization, X-Session-Token",
            )
            self.end_headers()
        else:
            self.send_error(404, "Not Found")

    def end_headers(self):
        # Add CORS headers for API requests
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Session-Token",
        )
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
        print("=" * 60)
        print("🏭 SentinelForge PRODUCTION Server")
        print("=" * 60)
        print(f"🚀 Server running at: http://localhost:{port}")
        print(f"📁 Serving from: {build_dir}")
        print("🔧 Server type: Production (spa-server.py)")
        print("📋 API Proxy: localhost:5059 (main), localhost:5101 (timeline)")
        print("=" * 60)
        print("Press Ctrl+C to stop")
        print("")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Production server stopped gracefully")


if __name__ == "__main__":
    main()
