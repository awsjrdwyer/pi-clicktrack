#!/bin/bash

# Click Track Player Uninstallation Script
# This script removes the Click Track Player application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_question() {
    echo -e "${BLUE}[?]${NC} $1"
}

echo ""
print_warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_warn "Click Track Player Uninstallation"
print_warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Confirm uninstallation
print_question "Are you sure you want to uninstall Click Track Player?"
read -p "Type 'yes' to continue: " -r
echo
if [ "$REPLY" != "yes" ]; then
    print_info "Uninstallation cancelled"
    exit 0
fi

# Get the actual user
ACTUAL_USER="${SUDO_USER:-$USER}"
CLICKTRACK_DIR="$HOME/.clicktrack"

# Check if running with sudo for service removal
NEEDS_SUDO=false
if systemctl list-unit-files "clicktrack@*.service" 2>/dev/null | grep -q "clicktrack@"; then
    NEEDS_SUDO=true
fi

if [ "$NEEDS_SUDO" = true ] && [ "$EUID" -ne 0 ]; then
    print_warn "Systemd service detected. Some operations require sudo."
    print_info "Re-running with sudo..."
    exec sudo -E bash "$0" "$@"
fi

# Stop and disable systemd service if it exists
if [ "$EUID" -eq 0 ]; then
    ACTUAL_USER="${SUDO_USER:-$USER}"
    SERVICE_NAME="clicktrack@$ACTUAL_USER.service"
    
    if systemctl list-unit-files "$SERVICE_NAME" 2>/dev/null | grep -q "$SERVICE_NAME"; then
        print_info "Stopping and disabling systemd service..."
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            systemctl stop "$SERVICE_NAME"
            print_info "Service stopped"
        fi
        
        if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
            systemctl disable "$SERVICE_NAME"
            print_info "Service disabled"
        fi
        
        # Remove service file
        SERVICE_FILE="/etc/systemd/system/clicktrack@.service"
        if [ -f "$SERVICE_FILE" ]; then
            rm "$SERVICE_FILE"
            systemctl daemon-reload
            print_info "Service file removed"
        fi
    fi
fi

# Ask about user data preservation
echo ""
print_question "Do you want to preserve your user data (songs, sets, configuration)?"
print_info "Data location: $CLICKTRACK_DIR"
read -p "Preserve user data? (Y/n) " -n 1 -r
echo
PRESERVE_DATA=true
if [[ $REPLY =~ ^[Nn]$ ]]; then
    PRESERVE_DATA=false
fi

# Remove virtual environment
print_info "Removing virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    print_info "Virtual environment removed"
fi

# Remove user data if requested
if [ "$PRESERVE_DATA" = false ]; then
    print_info "Removing user data..."
    if [ -d "$CLICKTRACK_DIR" ]; then
        # Create a backup just in case
        BACKUP_DIR="$HOME/.clicktrack-backup-$(date +%Y%m%d-%H%M%S)"
        print_info "Creating backup at $BACKUP_DIR"
        cp -r "$CLICKTRACK_DIR" "$BACKUP_DIR"
        
        rm -rf "$CLICKTRACK_DIR"
        print_info "User data removed (backup saved at $BACKUP_DIR)"
    fi
else
    print_info "User data preserved at $CLICKTRACK_DIR"
fi

# Remove Python package from user site-packages if installed
print_info "Removing Python package..."
if command -v pip3 &> /dev/null; then
    pip3 uninstall -y clicktrack-player 2>/dev/null || true
fi

# Print completion message
echo ""
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "✓ Click Track Player uninstalled successfully!"
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$PRESERVE_DATA" = true ]; then
    print_info "Your data has been preserved at: $CLICKTRACK_DIR"
    echo ""
    print_info "To completely remove all data, run:"
    echo "  rm -rf $CLICKTRACK_DIR"
    echo ""
fi

print_info "To reinstall Click Track Player, run:"
echo "  ./install.sh"
echo ""
