#!/bin/bash

# Click Track Player Systemd Service Installation Script
# This script installs and configures the Click Track Player as a systemd service

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run with sudo"
    echo "Usage: sudo ./install-service.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    print_error "Cannot determine the user to run the service as"
    print_error "Please run this script with sudo as a regular user"
    exit 1
fi

print_info "Installing Click Track Player systemd service for user: $ACTUAL_USER"

# Check if the application is installed
INSTALL_DIR="/home/$ACTUAL_USER/clicktrack"
if [ ! -d "$INSTALL_DIR" ]; then
    print_error "Installation directory not found: $INSTALL_DIR"
    print_error "Please run install.sh first"
    exit 1
fi

if [ ! -f "$INSTALL_DIR/venv/bin/clicktrack" ]; then
    print_error "Click Track Player not found in virtual environment"
    print_error "Please run install.sh first"
    exit 1
fi

# Check if service file exists
if [ ! -f "$INSTALL_DIR/clicktrack.service" ]; then
    print_error "Service file not found: $INSTALL_DIR/clicktrack.service"
    exit 1
fi

# Add user to audio group if not already a member
print_info "Configuring audio permissions..."
if ! groups "$ACTUAL_USER" | grep -q '\baudio\b'; then
    usermod -a -G audio "$ACTUAL_USER"
    print_info "Added $ACTUAL_USER to audio group"
    print_warn "User must log out and back in for audio group membership to take effect"
else
    print_info "User $ACTUAL_USER is already in audio group ✓"
fi

# Install the service file
print_info "Installing systemd service..."
SERVICE_FILE="/etc/systemd/system/clicktrack@.service"
cp "$INSTALL_DIR/clicktrack.service" "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"
print_info "Service file installed to $SERVICE_FILE"

# Reload systemd
print_info "Reloading systemd daemon..."
systemctl daemon-reload

# Enable the service
print_info "Enabling service to start on boot..."
systemctl enable "clicktrack@$ACTUAL_USER.service"

# Ask if user wants to start the service now
echo ""
read -p "Start the service now? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_info "Starting Click Track Player service..."
    systemctl start "clicktrack@$ACTUAL_USER.service"
    
    # Wait a moment for the service to start
    sleep 2
    
    # Check status
    if systemctl is-active --quiet "clicktrack@$ACTUAL_USER.service"; then
        print_info "Service started successfully ✓"
    else
        print_error "Service failed to start"
        print_info "Check status with: sudo systemctl status clicktrack@$ACTUAL_USER.service"
        print_info "Check logs with: sudo journalctl -u clicktrack@$ACTUAL_USER.service -f"
        exit 1
    fi
fi

# Print success message
echo ""
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "✓ Click Track Player service installed successfully!"
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "Service management commands:"
echo ""
echo "  Start service:   sudo systemctl start clicktrack@$ACTUAL_USER.service"
echo "  Stop service:    sudo systemctl stop clicktrack@$ACTUAL_USER.service"
echo "  Restart service: sudo systemctl restart clicktrack@$ACTUAL_USER.service"
echo "  Check status:    sudo systemctl status clicktrack@$ACTUAL_USER.service"
echo "  View logs:       sudo journalctl -u clicktrack@$ACTUAL_USER.service -f"
echo "  Disable service: sudo systemctl disable clicktrack@$ACTUAL_USER.service"
echo ""
print_info "The service will automatically start on boot"
print_info "Web interface: http://localhost:3000"
echo ""
