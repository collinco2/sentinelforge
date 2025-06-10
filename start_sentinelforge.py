#!/usr/bin/env python3
"""
SentinelForge Startup Script
Comprehensive startup script with stability checks and proper service management
"""

import os
import sys
import time
import signal
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/startup.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class SentinelForgeStarter:
    def __init__(self):
        self.processes = {}
        self.is_running = False

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down all services...")
        self.shutdown_all()
        sys.exit(0)

    def check_port(self, port):
        """Check if a port is available"""
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(("localhost", port))
            return result == 0

    def kill_port(self, port):
        """Kill process using a specific port"""
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    subprocess.run(["kill", "-9", pid])
                    logger.info(f"🔪 Killed process {pid} on port {port}")
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Could not kill port {port}: {e}")

    def pre_flight_checks(self):
        """Perform pre-flight checks before starting services"""
        logger.info("🔍 Performing pre-flight checks...")

        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ required")
            return False

        # Check required files
        required_files = [
            "production_api_server.py",
            "ui/spa-server.py",
            "alerts_timeline_api.py",
            "ioc_store.db",
        ]

        for file_path in required_files:
            if not Path(file_path).exists():
                logger.error(f"❌ Required file missing: {file_path}")
                return False

        # Check UI build
        if not Path("ui/build/index.html").exists():
            logger.warning("⚠️  UI build not found, building...")
            if not self.build_ui():
                return False

        # Clear conflicting ports
        ports_to_clear = [3000, 5059, 5101]
        for port in ports_to_clear:
            if self.check_port(port):
                logger.warning(f"⚠️  Port {port} in use, clearing...")
                self.kill_port(port)

        logger.info("✅ Pre-flight checks completed")
        return True

    def build_ui(self):
        """Build the React UI"""
        try:
            logger.info("🔨 Building React UI...")
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd="ui",
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                logger.info("✅ UI build completed")
                return True
            else:
                logger.error(f"❌ UI build failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ UI build timed out")
            return False
        except Exception as e:
            logger.error(f"❌ UI build error: {e}")
            return False

    def start_service(self, name, command, cwd=None, wait_for_port=None):
        """Start a service and track it"""
        try:
            logger.info(f"🚀 Starting {name}...")

            process = subprocess.Popen(
                command,
                cwd=cwd or os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.processes[name] = process

            # Wait for service to be ready
            if wait_for_port:
                for i in range(30):  # Wait up to 30 seconds
                    if self.check_port(wait_for_port):
                        logger.info(f"✅ {name} ready on port {wait_for_port}")
                        return True
                    time.sleep(1)

                logger.error(f"❌ {name} failed to start on port {wait_for_port}")
                return False
            else:
                time.sleep(2)  # Give process time to start
                if process.poll() is None:
                    logger.info(f"✅ {name} started")
                    return True
                else:
                    logger.error(f"❌ {name} failed to start")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return False

    def start_all_services(self):
        """Start all SentinelForge services in correct order"""
        logger.info("🚀 Starting SentinelForge services...")

        # 1. Start API Server
        if not self.start_service(
            "API Server", ["python3", "production_api_server.py"], wait_for_port=5059
        ):
            return False

        # 2. Start Timeline API
        if not self.start_service(
            "Timeline API", ["python3", "alerts_timeline_api.py"], wait_for_port=5101
        ):
            return False

        # 3. Start React UI Server
        if not self.start_service(
            "React UI Server",
            ["python3", "spa-server.py"],
            cwd="ui",
            wait_for_port=3000,
        ):
            return False

        logger.info("🎉 All services started successfully!")
        return True

    def monitor_services(self):
        """Monitor running services"""
        logger.info("👀 Monitoring services...")

        while self.is_running:
            try:
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.error(f"❌ {name} has stopped unexpectedly")
                        return False

                time.sleep(5)

            except KeyboardInterrupt:
                break

        return True

    def shutdown_all(self):
        """Shutdown all services gracefully"""
        logger.info("🛑 Shutting down all services...")

        for name, process in self.processes.items():
            try:
                logger.info(f"🛑 Stopping {name}...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️  Force killing {name}...")
                    process.kill()

            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

        self.processes.clear()
        self.is_running = False
        logger.info("✅ All services stopped")

    def start(self):
        """Main startup sequence"""
        print("=" * 80)
        print("🏭 SentinelForge Production Startup")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python: {sys.version}")
        print(f"📁 Working Directory: {os.getcwd()}")
        print("=" * 80)

        try:
            # Pre-flight checks
            if not self.pre_flight_checks():
                logger.error("❌ Pre-flight checks failed")
                return False

            # Start services
            if not self.start_all_services():
                logger.error("❌ Failed to start services")
                self.shutdown_all()
                return False

            self.is_running = True

            # Display success message
            print("\n" + "=" * 80)
            print("🎉 SentinelForge Started Successfully!")
            print("=" * 80)
            print("📊 Dashboard: http://localhost:3000")
            print("🔌 API Server: http://localhost:5059")
            print("📈 Timeline API: http://localhost:5101")
            print("=" * 80)
            print("Press Ctrl+C to stop all services")
            print("=" * 80)

            # Monitor services
            return self.monitor_services()

        except KeyboardInterrupt:
            logger.info("🛑 Startup interrupted by user")
            self.shutdown_all()
            return True
        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            self.shutdown_all()
            return False


def main():
    """Main entry point"""
    starter = SentinelForgeStarter()
    success = starter.start()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
