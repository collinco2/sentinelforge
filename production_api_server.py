#!/usr/bin/env python3
"""
SentinelForge Production API Server
Stable production-grade server with proper error handling and monitoring
"""

import os
import sys
import logging
import signal
import time
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from api_server
from api_server import app, init_database, init_auth_tables

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api_server.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class ProductionServer:
    def __init__(self):
        self.app = app
        self.port = int(os.environ.get("API_PORT", 5059))
        self.host = os.environ.get("API_HOST", "0.0.0.0")
        self.workers = int(os.environ.get("API_WORKERS", 1))
        self.is_running = False

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.is_running = False

    def health_check(self):
        """Perform basic health checks"""
        try:
            # Check database connectivity
            init_database()
            init_auth_tables()
            logger.info("✅ Database health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False

    def start_production_server(self):
        """Start the production server with Gunicorn"""
        if not self.health_check():
            logger.error("Health check failed, aborting startup")
            sys.exit(1)

        logger.info("🚀 Starting SentinelForge Production API Server")
        logger.info(f"📍 Host: {self.host}")
        logger.info(f"🔌 Port: {self.port}")
        logger.info(f"👥 Workers: {self.workers}")

        # Configure Flask app for production
        self.app.config.update({"DEBUG": False, "TESTING": False, "ENV": "production"})

        try:
            # Import gunicorn
            from gunicorn.app.base import BaseApplication

            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    config = {
                        key: value
                        for key, value in self.options.items()
                        if key in self.cfg.settings and value is not None
                    }
                    for key, value in config.items():
                        self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                "bind": f"{self.host}:{self.port}",
                "workers": self.workers,
                "worker_class": "sync",
                "worker_connections": 1000,
                "timeout": 30,
                "keepalive": 2,
                "max_requests": 1000,
                "max_requests_jitter": 50,
                "preload_app": True,
                "access_log_format": '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
                "accesslog": "logs/api_access.log",
                "errorlog": "logs/api_error.log",
                "loglevel": "info",
            }

            self.is_running = True
            StandaloneApplication(self.app, options).run()

        except ImportError:
            logger.warning(
                "Gunicorn not available, falling back to Flask development server"
            )
            self.start_development_server()
        except Exception as e:
            logger.error(f"Failed to start production server: {e}")
            sys.exit(1)

    def start_development_server(self):
        """Fallback to Flask development server with stability improvements"""
        logger.info("🔧 Starting Flask development server (fallback mode)")

        # Disable auto-reload to prevent instability
        self.app.config.update(
            {
                "DEBUG": False,  # Disable debug mode for stability
                "USE_RELOADER": False,  # Disable auto-reload
                "THREADED": True,
            }
        )

        try:
            self.is_running = True
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True,
            )
        except Exception as e:
            logger.error(f"Failed to start development server: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    print("=" * 60)
    print("🏭 SentinelForge Production API Server")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print("=" * 60)

    server = ProductionServer()

    try:
        server.start_production_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        sys.exit(1)
    finally:
        logger.info("🛑 SentinelForge API Server stopped")


if __name__ == "__main__":
    main()
