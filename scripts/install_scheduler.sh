#!/bin/bash
"""
Installation script for SentinelForge Scheduled Feed Importer

This script sets up the scheduled feed importer as a systemd service
with proper user permissions, directories, and configuration.

Usage:
    sudo bash scripts/install_scheduler.sh
    
    # With custom options
    sudo bash scripts/install_scheduler.sh --user myuser --install-dir /opt/myapp
"""

set -e

# Default configuration
DEFAULT_USER="sentinelforge"
DEFAULT_GROUP="sentinelforge"
DEFAULT_INSTALL_DIR="/opt/sentinelforge"
DEFAULT_DATA_DIR="/opt/sentinelforge/data"
DEFAULT_LOG_DIR="/var/log/sentinelforge"
DEFAULT_CRON="0 */6 * * *"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --user)
                SERVICE_USER="$2"
                shift 2
                ;;
            --group)
                SERVICE_GROUP="$2"
                shift 2
                ;;
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --data-dir)
                DATA_DIR="$2"
                shift 2
                ;;
            --log-dir)
                LOG_DIR="$2"
                shift 2
                ;;
            --cron)
                CRON_EXPRESSION="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Set defaults
    SERVICE_USER=${SERVICE_USER:-$DEFAULT_USER}
    SERVICE_GROUP=${SERVICE_GROUP:-$DEFAULT_GROUP}
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}
    DATA_DIR=${DATA_DIR:-$DEFAULT_DATA_DIR}
    LOG_DIR=${LOG_DIR:-$DEFAULT_LOG_DIR}
    CRON_EXPRESSION=${CRON_EXPRESSION:-$DEFAULT_CRON}
}

show_help() {
    cat << EOF
SentinelForge Scheduled Feed Importer Installation Script

Usage: sudo bash scripts/install_scheduler.sh [OPTIONS]

Options:
    --user USER         Service user (default: sentinelforge)
    --group GROUP       Service group (default: sentinelforge)
    --install-dir DIR   Installation directory (default: /opt/sentinelforge)
    --data-dir DIR      Data directory (default: /opt/sentinelforge/data)
    --log-dir DIR       Log directory (default: /var/log/sentinelforge)
    --cron EXPR         CRON expression (default: "0 */6 * * *")
    --help              Show this help message

Examples:
    # Default installation
    sudo bash scripts/install_scheduler.sh
    
    # Custom user and directories
    sudo bash scripts/install_scheduler.sh --user myuser --install-dir /opt/myapp
    
    # Custom schedule (every 4 hours)
    sudo bash scripts/install_scheduler.sh --cron "0 */4 * * *"
EOF
}

# Create system user and group
create_user() {
    log_info "Creating system user and group..."
    
    if ! getent group "$SERVICE_GROUP" > /dev/null 2>&1; then
        groupadd --system "$SERVICE_GROUP"
        log_success "Created group: $SERVICE_GROUP"
    else
        log_info "Group already exists: $SERVICE_GROUP"
    fi
    
    if ! getent passwd "$SERVICE_USER" > /dev/null 2>&1; then
        useradd --system --gid "$SERVICE_GROUP" --home-dir "$INSTALL_DIR" \
                --shell /bin/false --comment "SentinelForge Service User" "$SERVICE_USER"
        log_success "Created user: $SERVICE_USER"
    else
        log_info "User already exists: $SERVICE_USER"
    fi
}

# Create directories
create_directories() {
    log_info "Creating directories..."
    
    # Installation directory
    mkdir -p "$INSTALL_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    
    # Data directory
    mkdir -p "$DATA_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$DATA_DIR"
    chmod 750 "$DATA_DIR"
    
    # Log directory
    mkdir -p "$LOG_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"
    chmod 750 "$LOG_DIR"
    
    log_success "Created directories"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8 or later."
        exit 1
    fi
    
    # Create virtual environment
    if [[ ! -d "$INSTALL_DIR/venv" ]]; then
        sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
        log_success "Created virtual environment"
    fi
    
    # Install dependencies
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install \
        apscheduler requests sqlite3 pathlib
    
    log_success "Installed Python dependencies"
}

# Copy application files
copy_files() {
    log_info "Copying application files..."
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    
    # Copy Python modules
    cp -r "$PROJECT_DIR/services" "$INSTALL_DIR/"
    cp -r "$PROJECT_DIR/config" "$INSTALL_DIR/"
    cp -r "$PROJECT_DIR/scripts" "$INSTALL_DIR/"
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/services"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/config"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/scripts"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts/run_scheduler.py"
    
    log_success "Copied application files"
}

# Install systemd service
install_service() {
    log_info "Installing systemd service..."
    
    # Create service file from template
    cat > /etc/systemd/system/sentinelforge-scheduler.service << EOF
[Unit]
Description=SentinelForge Scheduled Feed Importer
Documentation=https://github.com/collinco2/sentinelforge
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/scripts/run_scheduler.py --daemon
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sentinelforge-scheduler

# Environment variables
Environment=SENTINELFORGE_DB_PATH=$DATA_DIR/ioc_store.db
Environment=SCHEDULER_LOG_FILE=$LOG_DIR/scheduler.log
Environment=SCHEDULER_LOG_LEVEL=INFO
Environment=SCHEDULER_CRON=$CRON_EXPRESSION
Environment=SCHEDULER_TIMEOUT=30
Environment=SCHEDULER_MAX_RETRIES=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR /tmp
CapabilityBoundingSet=
AmbientCapabilities=
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    log_success "Installed systemd service"
}

# Create configuration file
create_config() {
    log_info "Creating configuration file..."
    
    cat > "$INSTALL_DIR/scheduler.conf" << EOF
# SentinelForge Scheduler Configuration
# This file is sourced by the systemd service

# Database settings
SENTINELFORGE_DB_PATH=$DATA_DIR/ioc_store.db

# Logging settings
SCHEDULER_LOG_FILE=$LOG_DIR/scheduler.log
SCHEDULER_LOG_LEVEL=INFO

# Schedule settings
SCHEDULER_CRON=$CRON_EXPRESSION
SCHEDULER_TIMEZONE=UTC

# HTTP settings
SCHEDULER_TIMEOUT=30
SCHEDULER_MAX_RETRIES=3
SCHEDULER_BASE_DELAY=1.0
SCHEDULER_MAX_DELAY=60.0

# Performance settings
MAX_CONCURRENT_IMPORTS=3
SCHEDULER_TEMP_DIR=/tmp
EOF
    
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/scheduler.conf"
    chmod 640 "$INSTALL_DIR/scheduler.conf"
    
    log_success "Created configuration file: $INSTALL_DIR/scheduler.conf"
}

# Main installation function
main() {
    log_info "Starting SentinelForge Scheduler installation..."
    
    check_root
    parse_args "$@"
    
    log_info "Installation configuration:"
    log_info "  User: $SERVICE_USER"
    log_info "  Group: $SERVICE_GROUP"
    log_info "  Install directory: $INSTALL_DIR"
    log_info "  Data directory: $DATA_DIR"
    log_info "  Log directory: $LOG_DIR"
    log_info "  CRON expression: $CRON_EXPRESSION"
    
    create_user
    create_directories
    install_dependencies
    copy_files
    create_config
    install_service
    
    log_success "Installation completed successfully!"
    
    echo
    log_info "Next steps:"
    echo "  1. Enable the service: systemctl enable sentinelforge-scheduler"
    echo "  2. Start the service:  systemctl start sentinelforge-scheduler"
    echo "  3. Check status:       systemctl status sentinelforge-scheduler"
    echo "  4. View logs:          journalctl -u sentinelforge-scheduler -f"
    echo
    log_info "Configuration file: $INSTALL_DIR/scheduler.conf"
    log_info "Service file: /etc/systemd/system/sentinelforge-scheduler.service"
}

# Run main function with all arguments
main "$@"
