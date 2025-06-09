#!/usr/bin/env python3
"""
Simple SPA Server for SentinelForge React UI
A lightweight, reliable server for serving Single Page Applications
"""

import http.server
import socketserver
import os
import sys
import mimetypes
from urllib.parse import urlparse
import json
import urllib.request
import urllib.error


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    """
    HTTP request handler for Single Page Applications.
    Serves static files normally, but serves index.html for all other routes.
    """

    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=os.getcwd(), **kwargs)

    def do_GET(self):
        """Handle GET requests with SPA routing support"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Check if this is an API request
        if path.startswith("/api/"):
            return self.proxy_api_request()

        # Remove leading slash for file system operations
        if path.startswith("/"):
            path = path[1:]

        # If no path, serve index.html
        if not path:
            path = "index.html"

        # Check if the requested file exists
        if os.path.isfile(path):
            # File exists, serve it normally
            super().do_GET()
        elif path.startswith("static/"):
            # Static file doesn't exist, return 404
            self.send_error(404, f"File not found: {path}")
        elif path.endswith(".json") or path.endswith(".ico") or path.endswith(".txt"):
            # Specific file types that should return 404 if not found
            super().do_GET()
        else:
            # For all other paths (React routes), serve index.html
            self.serve_index_html()

    def serve_index_html(self):
        """Serve the index.html file for SPA routing"""
        try:
            with open("index.html", "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)

        except FileNotFoundError:
            self.send_error(404, "index.html not found")
        except Exception as e:
            self.send_error(500, f"Error serving index.html: {str(e)}")

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

            # Create request
            req = urllib.request.Request(
                target_url, data=request_body, method=self.command
            )

            # Copy headers from original request
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ["host", "content-length"]:
                    req.add_header(header_name, header_value)

            # Make request to backend
            with urllib.request.urlopen(req) as response:
                # Send response status
                self.send_response(response.getcode())

                # Copy response headers
                for header_name, header_value in response.headers.items():
                    if header_name.lower() not in ["server", "date"]:
                        self.send_header(header_name, header_value)

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

    def log_message(self, format, *args):
        """Custom log format"""
        print(
            f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}"
        )


def main():
    """Main server function"""
    # Get port from command line argument or default to 3000
    port = 3000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)

    # Check if we're in the build directory
    if not os.path.isfile("index.html"):
        print("Error: index.html not found in current directory")
        print("Please run this server from the build directory")
        sys.exit(1)

    # Create server
    try:
        with socketserver.TCPServer(("", port), SPAHandler) as httpd:
            print("=" * 60)
            print("🚀 Simple SPA Server for SentinelForge")
            print("=" * 60)
            print(f"📁 Serving from: {os.getcwd()}")
            print(f"🌐 Server running at: http://localhost:{port}")
            print(f"🔧 Server type: Simple SPA Server with API Proxy")
            print("📋 API Proxy: localhost:5059 (main), localhost:5101 (timeline)")
            print("=" * 60)
            print("📋 Features:")
            print("  ✅ SPA routing support")
            print("  ✅ Static file serving")
            print("  ✅ API request proxying")
            print("  ✅ CORS support")
            print("  ✅ Proper MIME types")
            print("=" * 60)
            print("Press Ctrl+C to stop")
            print()

            # Start serving
            httpd.serve_forever()

    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {port} is already in use")
            print("Please stop any existing servers or use a different port")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
