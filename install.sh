#!/bin/bash

# Click Track Player Installation Script
# This script installs the Click Track Player application on Raspberry Pi

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

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_warn "This script is designed for Linux systems (Raspberry Pi OS)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_info "Starting Click Track Player installation..."

# Check for Python 3.9+
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

print_info "Python $PYTHON_VERSION detected ✓"

# Install system dependencies
print_info "Installing system dependencies..."
print_info "This may require sudo password..."

# Detect package manager
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
else
    print_warn "Could not detect package manager. Skipping system dependencies."
    print_warn "You may need to manually install: portaudio19-dev, libasound2-dev, libjack-dev"
    PKG_MANAGER=""
fi

if [ -n "$PKG_MANAGER" ]; then
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        sudo apt-get update
        sudo apt-get install -y \
            python3-pip \
            python3-dev \
            python3-venv \
            portaudio19-dev \
            libasound2-dev \
            libjack-dev \
            alsa-utils \
            || print_warn "Some system dependencies may have failed to install"
    elif [ "$PKG_MANAGER" = "dnf" ] || [ "$PKG_MANAGER" = "yum" ]; then
        sudo $PKG_MANAGER install -y \
            python3-pip \
            python3-devel \
            portaudio-devel \
            alsa-lib-devel \
            jack-audio-connection-kit-devel \
            alsa-utils \
            || print_warn "Some system dependencies may have failed to install"
    fi
    print_info "System dependencies installed ✓"
fi

# Create ~/.clicktrack directory structure
print_info "Creating application directories..."
CLICKTRACK_DIR="$HOME/.clicktrack"
mkdir -p "$CLICKTRACK_DIR"
mkdir -p "$CLICKTRACK_DIR/logs"
mkdir -p "$CLICKTRACK_DIR/backups"

print_info "Created directory structure:"
print_info "  $CLICKTRACK_DIR"
print_info "  $CLICKTRACK_DIR/logs"
print_info "  $CLICKTRACK_DIR/backups"

# Create virtual environment
print_info "Creating Python virtual environment..."
VENV_DIR="$PWD/venv"

if [ -d "$VENV_DIR" ]; then
    print_warn "Virtual environment already exists at $VENV_DIR"
    read -p "Remove and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi
else
    python3 -m venv "$VENV_DIR"
fi

print_info "Virtual environment created ✓"

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Install the application
print_info "Installing Click Track Player..."
pip install -e .

print_info "Python dependencies installed ✓"

# Copy default configuration if it doesn't exist
if [ ! -f "$CLICKTRACK_DIR/config.yaml" ]; then
    if [ -f "config/config.yaml" ]; then
        print_info "Copying default configuration..."
        cp config/config.yaml "$CLICKTRACK_DIR/config.yaml"
        print_info "Configuration file created at $CLICKTRACK_DIR/config.yaml"
    fi
fi

# Test the installation
print_info "Testing installation..."
if python -c "import clicktrack" 2>/dev/null; then
    print_info "Installation test passed ✓"
else
    print_error "Installation test failed!"
    exit 1
fi

# Print success message
echo ""
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "✓ Click Track Player installed successfully!"
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "Next steps:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the application:"
echo "     clicktrack"
echo ""
echo "  3. Access the web interface at:"
echo "     http://localhost:3000"
echo ""
echo "  4. (Optional) Install as a systemd service:"
echo "     sudo ./install-service.sh"
echo ""
print_info "Configuration: $CLICKTRACK_DIR/config.yaml"
print_info "Data directory: $CLICKTRACK_DIR"
echo ""
