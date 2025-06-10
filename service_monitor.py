#!/usr/bin/env python3
"""
SentinelForge Service Health Monitor
Monitors all services and provides automatic restart capabilities
"""

import os
import sys
import time
import json
import logging
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/service_monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class ServiceMonitor:
    def __init__(self):
        self.services = {
            "api_server": {
                "name": "API Server",
                "url": "http://localhost:5059/api/session",
                "port": 5059,
                "process_name": "production_api_server.py",
                "start_command": ["python3", "production_api_server.py"],
                "health_endpoint": "/api/session",
                "expected_response": {"authenticated": False},
                "restart_count": 0,
                "last_restart": None,
                "status": "unknown",
            },
            "ui_server": {
                "name": "React UI Server",
                "url": "http://localhost:3000",
                "port": 3000,
                "process_name": "spa-server.py",
                "start_command": ["python3", "ui/spa-server.py"],
                "health_endpoint": "/",
                "expected_response": None,  # Just check for 200 status
                "restart_count": 0,
                "last_restart": None,
                "status": "unknown",
            },
            "timeline_api": {
                "name": "Timeline API",
                "url": "http://localhost:5101",
                "port": 5101,
                "process_name": "alerts_timeline_api.py",
                "start_command": ["python3", "alerts_timeline_api.py"],
                "health_endpoint": "/",
                "expected_response": None,
                "restart_count": 0,
                "last_restart": None,
                "status": "unknown",
            },
        }

        self.max_restarts = 3
        self.restart_window = timedelta(minutes=10)
        self.check_interval = 30  # seconds

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

    def check_port(self, port):
        """Check if a port is in use"""
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(("localhost", port))
            return result == 0

    def check_process(self, process_name):
        """Check if a process is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name], capture_output=True, text=True
            )
            return len(result.stdout.strip()) > 0
        except Exception:
            return False

    def health_check(self, service_name):
        """Perform health check on a service"""
        service = self.services[service_name]

        try:
            # Check if port is listening
            if not self.check_port(service["port"]):
                service["status"] = "port_down"
                return False

            # Check HTTP endpoint
            response = requests.get(
                service["url"] + service["health_endpoint"], timeout=5
            )

            if response.status_code == 200:
                # Check response content if expected
                if service["expected_response"]:
                    try:
                        data = response.json()
                        if data == service["expected_response"]:
                            service["status"] = "healthy"
                            return True
                        else:
                            service["status"] = "unhealthy_response"
                            return False
                    except:
                        service["status"] = "invalid_json"
                        return False
                else:
                    service["status"] = "healthy"
                    return True
            else:
                service["status"] = f"http_{response.status_code}"
                return False

        except requests.exceptions.ConnectionError:
            service["status"] = "connection_refused"
            return False
        except requests.exceptions.Timeout:
            service["status"] = "timeout"
            return False
        except Exception as e:
            service["status"] = f"error_{str(e)[:20]}"
            return False

    def can_restart(self, service_name):
        """Check if service can be restarted (within limits)"""
        service = self.services[service_name]

        # Check restart count
        if service["restart_count"] >= self.max_restarts:
            if service["last_restart"]:
                time_since_restart = datetime.now() - service["last_restart"]
                if time_since_restart < self.restart_window:
                    return False
                else:
                    # Reset restart count after window
                    service["restart_count"] = 0

        return True

    def restart_service(self, service_name):
        """Restart a service"""
        service = self.services[service_name]

        if not self.can_restart(service_name):
            logger.error(f"❌ Cannot restart {service['name']} - too many restarts")
            return False

        logger.info(f"🔄 Restarting {service['name']}...")

        try:
            # Kill existing process
            subprocess.run(
                ["pkill", "-f", service["process_name"]], capture_output=True
            )

            # Wait a moment
            time.sleep(2)

            # Start new process
            subprocess.Popen(
                service["start_command"],
                cwd=os.getcwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Update restart tracking
            service["restart_count"] += 1
            service["last_restart"] = datetime.now()

            logger.info(f"✅ {service['name']} restart initiated")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to restart {service['name']}: {e}")
            return False

    def monitor_services(self):
        """Main monitoring loop"""
        logger.info("🔍 Starting SentinelForge Service Monitor")

        while True:
            try:
                status_report = {
                    "timestamp": datetime.now().isoformat(),
                    "services": {},
                }

                for service_name in self.services:
                    service = self.services[service_name]
                    is_healthy = self.health_check(service_name)

                    status_report["services"][service_name] = {
                        "name": service["name"],
                        "status": service["status"],
                        "healthy": is_healthy,
                        "restart_count": service["restart_count"],
                    }

                    if is_healthy:
                        logger.info(f"✅ {service['name']}: {service['status']}")
                    else:
                        logger.warning(f"⚠️  {service['name']}: {service['status']}")

                        # Attempt restart if unhealthy
                        if self.can_restart(service_name):
                            self.restart_service(service_name)
                        else:
                            logger.error(
                                f"❌ {service['name']} failed - restart limit exceeded"
                            )

                # Save status report
                with open("logs/service_status.json", "w") as f:
                    json.dump(status_report, f, indent=2)

                # Wait before next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("🛑 Service monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                time.sleep(5)


def main():
    """Main entry point"""
    print("=" * 60)
    print("🔍 SentinelForge Service Monitor")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    monitor = ServiceMonitor()
    monitor.monitor_services()


if __name__ == "__main__":
    main()
