#!/bin/bash
#
# Bluetooth MIDI Setup Script for Click Track Player
# This script helps set up Bluetooth MIDI connectivity on Raspberry Pi
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    warn "This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Bluetooth MIDI Setup for Click Track Player"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Install required packages
info "Installing required Bluetooth packages..."
sudo apt-get update -qq
sudo apt-get install -y bluez bluez-tools pulseaudio-module-bluetooth bluez-alsa-utils

success "Bluetooth packages installed"

# Step 2: Enable Bluetooth service
info "Enabling Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

success "Bluetooth service enabled and started"

# Step 3: Check Bluetooth status
info "Checking Bluetooth status..."
if systemctl is-active --quiet bluetooth; then
    success "Bluetooth service is running"
else
    error "Bluetooth service is not running"
    exit 1
fi

# Step 4: Ensure Bluetooth adapter is ready
echo ""
info "Preparing Bluetooth adapter..."

# Unblock Bluetooth if blocked
sudo rfkill unblock bluetooth 2>/dev/null || true
sleep 1

# Power on and configure Bluetooth adapter
{
    echo "power on"
    sleep 2
    echo "agent on"
    sleep 1
    echo "default-agent"
    sleep 1
} | bluetoothctl > /dev/null 2>&1

# Wait for adapter to be ready
info "Waiting for Bluetooth adapter to be ready..."
for i in {1..10}; do
    if bluetoothctl show | grep -q "Powered: yes"; then
        success "Bluetooth adapter is ready"
        break
    fi
    if [ $i -eq 10 ]; then
        error "Bluetooth adapter failed to power on"
        error "Try running: sudo systemctl restart bluetooth"
        exit 1
    fi
    sleep 1
done

# Step 5: Scan for Bluetooth devices
echo ""
info "Scanning for Bluetooth devices..."
info "Please put your MIDI controller in pairing mode now"
echo ""

# Start scanning with proper error handling
info "Starting scan..."
{
    echo "scan on"
    sleep 15
    echo "scan off"
} | bluetoothctl 2>&1 | grep -v "SetDiscoveryFilter" | grep -v "Failed to start discovery" &
SCAN_PID=$!

# Wait for scan to complete
sleep 16

# Ensure scan is stopped
echo "scan off" | bluetoothctl > /dev/null 2>&1
wait $SCAN_PID 2>/dev/null || true

# Step 6: List discovered devices
echo ""
info "Discovered Bluetooth devices:"
echo ""
bluetoothctl devices | while read -r line; do
    echo "  $line"
done
echo ""

# Ask user to select device
read -p "Enter the MAC address of your MIDI controller (e.g., AA:BB:CC:DD:EE:FF): " MAC_ADDRESS

if [[ ! $MAC_ADDRESS =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
    error "Invalid MAC address format"
    exit 1
fi

# Step 7: Pair and connect
info "Pairing with device $MAC_ADDRESS..."

# Use expect-like approach with bluetoothctl
{
    echo "agent on"
    echo "default-agent"
    sleep 1
    echo "pair $MAC_ADDRESS"
    sleep 3
    echo "trust $MAC_ADDRESS"
    sleep 1
    echo "connect $MAC_ADDRESS"
    sleep 2
    echo "quit"
} | bluetoothctl

# Check if connected
if bluetoothctl info "$MAC_ADDRESS" | grep -q "Connected: yes"; then
    success "Successfully connected to $MAC_ADDRESS"
else
    warn "Device paired but not connected. Trying to connect..."
    echo "connect $MAC_ADDRESS" | bluetoothctl
    sleep 2
    
    if bluetoothctl info "$MAC_ADDRESS" | grep -q "Connected: yes"; then
        success "Successfully connected to $MAC_ADDRESS"
    else
        error "Failed to connect. You may need to manually connect using: bluetoothctl connect $MAC_ADDRESS"
    fi
fi

# Step 8: Check MIDI ports
echo ""
info "Checking for MIDI ports..."
sleep 2

if [ -d "$HOME/clicktrack/venv" ]; then
    source "$HOME/clicktrack/venv/bin/activate"
    
    MIDI_PORTS=$(python3 << 'EOF'
import rtmidi
try:
    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()
    if ports:
        print("\n  Available MIDI ports:")
        for i, port in enumerate(ports):
            print(f"    {i}: {port}")
    else:
        print("\n  No MIDI ports found")
except Exception as e:
    print(f"\n  Error checking MIDI ports: {e}")
EOF
)
    echo "$MIDI_PORTS"
else
    warn "Click Track Player not installed. Install it first with ./install.sh"
fi

# Step 9: Create auto-reconnect service
echo ""
read -p "Create auto-reconnect service for this device? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    info "Creating auto-reconnect service..."
    
    sudo tee /etc/systemd/system/bluetooth-midi-reconnect.service > /dev/null << EOF
[Unit]
Description=Bluetooth MIDI Auto-Reconnect
After=bluetooth.service

[Service]
Type=oneshot
ExecStart=/usr/bin/bluetoothctl connect $MAC_ADDRESS
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable bluetooth-midi-reconnect.service
    
    success "Auto-reconnect service created and enabled"
fi

# Step 10: Configuration instructions
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "Bluetooth MIDI setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
info "Next steps:"
echo ""
echo "  1. Configure MIDI in Click Track Player:"
echo "     nano ~/.clicktrack/config.yaml"
echo ""
echo "  2. Add MIDI configuration:"
echo "     midi:"
echo "       enabled: true"
echo "       device_name: \"YourMIDIController\"  # Use name from MIDI ports list above"
echo "       mappings:"
echo "         play: 64      # CC 64 for Play"
echo "         stop: 65      # CC 65 for Stop"
echo "         next: 66      # CC 66 for Next"
echo "         previous: 67  # CC 67 for Previous"
echo ""
echo "  3. Restart the Click Track Player service:"
echo "     sudo systemctl restart clicktrack@pi.service"
echo ""
echo "  4. Test MIDI control and check logs:"
echo "     sudo journalctl -u clicktrack@pi.service -f"
echo ""
info "For detailed documentation, see: docs/BLUETOOTH_MIDI_SETUP.md"
echo ""
