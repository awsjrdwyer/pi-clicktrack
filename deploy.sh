#!/bin/bash

# Click Track Player Deployment Script
# Deploys the application to a Raspberry Pi on the network

set -e  # Exit on error

# Configuration
PI_USER="pi"
PI_HOST="172.31.31.187"
PI_DIR="clicktrack"
INSTALL_SERVICE=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check if we can reach the Raspberry Pi
print_step "Checking connection to Raspberry Pi..."
if ! ping -c 1 -W 2 $PI_HOST &> /dev/null; then
    print_error "Cannot reach Raspberry Pi at $PI_HOST"
    echo "Please check:"
    echo "  - The Raspberry Pi is powered on"
    echo "  - The IP address is correct"
    echo "  - You're on the same network"
    exit 1
fi
print_success "Raspberry Pi is reachable"

# Check SSH connection
print_step "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $PI_USER@$PI_HOST exit &> /dev/null; then
    print_warning "SSH key authentication not set up"
    echo "You'll need to enter your password for each SSH command"
    echo ""
    echo "To set up passwordless SSH (recommended):"
    echo "  ssh-copy-id $PI_USER@$PI_HOST"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "SSH connection successful"
fi

# Create temporary directory for deployment
print_step "Preparing deployment package..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy files to temp directory, excluding unnecessary files
rsync -a --exclude 'venv' \
         --exclude '.git' \
         --exclude '__pycache__' \
         --exclude '*.pyc' \
         --exclude '.pytest_cache' \
         --exclude '.coverage' \
         --exclude 'htmlcov' \
         --exclude '.DS_Store' \
         --exclude '*.egg-info' \
         ./ "$TEMP_DIR/"

print_success "Deployment package prepared"

# Transfer files to Raspberry Pi
print_step "Transferring files to Raspberry Pi..."
ssh $PI_USER@$PI_HOST "mkdir -p ~/$PI_DIR"

rsync -avz --delete \
      --exclude 'venv' \
      --exclude '.git' \
      --exclude '__pycache__' \
      --exclude '*.pyc' \
      --exclude '.pytest_cache' \
      --exclude '.coverage' \
      --exclude 'htmlcov' \
      --exclude '.DS_Store' \
      --exclude '*.egg-info' \
      "$TEMP_DIR/" $PI_USER@$PI_HOST:~/$PI_DIR/

print_success "Files transferred successfully"

# Make scripts executable
print_step "Setting permissions..."
ssh $PI_USER@$PI_HOST "chmod +x ~/$PI_DIR/*.sh"
print_success "Permissions set"

# Run installation
print_step "Running installation on Raspberry Pi..."
echo ""
echo "This will:"
echo "  - Install system dependencies (requires sudo)"
echo "  - Create Python virtual environment"
echo "  - Install Python packages"
echo "  - Set up data directory"
echo ""

ssh -t $PI_USER@$PI_HOST "cd ~/$PI_DIR && ./install.sh"

if [ $? -eq 0 ]; then
    print_success "Installation completed successfully"
else
    print_error "Installation failed"
    exit 1
fi

# Install as service if requested
if [ "$INSTALL_SERVICE" = true ]; then
    echo ""
    read -p "Install as a system service (auto-start on boot)? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Installing system service..."
        ssh -t $PI_USER@$PI_HOST "cd ~/$PI_DIR && sudo ./install-service.sh"
        
        if [ $? -eq 0 ]; then
            print_success "Service installed successfully"
            
            echo ""
            read -p "Start the service now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_step "Starting service..."
                ssh $PI_USER@$PI_HOST "sudo systemctl stop clicktrack@$PI_USER.service"
                ssh $PI_USER@$PI_HOST "sudo systemctl start clicktrack@$PI_USER.service"
                sleep 2
                
                # Check service status
                if ssh $PI_USER@$PI_HOST "sudo systemctl is-active --quiet clicktrack@$PI_USER.service"; then
                    print_success "Service is running"
                else
                    print_error "Service failed to start"
                    echo "Check logs with: ssh $PI_USER@$PI_HOST 'sudo journalctl -u clicktrack@$PI_USER.service -n 50'"
                fi
            fi
        else
            print_error "Service installation failed"
        fi
    fi
fi

# Display access information
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Access the web interface at:"
echo -e "  ${GREEN}http://$PI_HOST:3000${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:    ssh $PI_USER@$PI_HOST 'sudo journalctl -u clicktrack@$PI_USER.service -f'"
echo "  Stop service: ssh $PI_USER@$PI_HOST 'sudo systemctl stop clicktrack@$PI_USER.service'"
echo "  Start service: ssh $PI_USER@$PI_HOST 'sudo systemctl start clicktrack@$PI_USER.service'"
echo "  Service status: ssh $PI_USER@$PI_HOST 'sudo systemctl status clicktrack@$PI_USER.service'"
echo ""
echo "To redeploy after making changes:"
echo "  ./deploy.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
