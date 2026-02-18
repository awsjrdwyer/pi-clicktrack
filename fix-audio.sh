#!/bin/bash

# Audio Fix Script for Click Track Player
# This script reinstalls PyAudio with proper PortAudio support and configures ALSA

set -e

echo "=== Click Track Player Audio Fix ==="
echo ""

# Check if user is in audio group
echo "1. Checking audio group membership..."
if groups | grep -q audio; then
    echo "  ✓ User is in audio group"
else
    echo "  ! Adding user to audio group..."
    sudo usermod -a -G audio $USER
    echo "  ✓ User added to audio group (logout/login required for this to take effect)"
fi

# Install/update PortAudio and ALSA
echo ""
echo "2. Installing audio dependencies..."
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio libasound2-dev alsa-utils

# Check ALSA devices
echo ""
echo "3. Checking ALSA devices..."
aplay -l || echo "  ! No playback devices found"

# Test ALSA directly
echo ""
echo "4. Testing ALSA output..."
if speaker-test -t sine -f 1000 -l 1 -c 2 2>/dev/null; then
    echo "  ✓ ALSA output working"
else
    echo "  ! ALSA test failed - checking configuration..."
    
    # Create/update ALSA config for the user
    echo "  Creating ALSA configuration..."
    cat > ~/.asoundrc << 'ALSA_EOF'
pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
ALSA_EOF
    echo "  ✓ ALSA configuration created"
fi

# Reinstall PyAudio in the virtual environment
echo ""
echo "5. Reinstalling PyAudio..."
source venv/bin/activate
pip uninstall -y pyaudio
pip install --no-cache-dir pyaudio
deactivate

echo ""
echo "6. Testing PyAudio..."
source venv/bin/activate
python3 << 'EOF'
import pyaudio
import sys

p = pyaudio.PyAudio()
print(f"PyAudio version: {pyaudio.__version__}")
print(f"Found {p.get_device_count()} audio devices")

# List host APIs
print("\nHost APIs:")
for i in range(p.get_host_api_count()):
    api_info = p.get_host_api_info_by_index(i)
    print(f"  {i}: {api_info['name']} ({api_info['deviceCount']} devices)")

# List output devices
print("\nOutput devices:")
output_found = False
for i in range(p.get_device_count()):
    try:
        info = p.get_device_info_by_index(i)
        if info['maxOutputChannels'] > 0:
            print(f"  {i}: {info['name']} ({info['maxOutputChannels']} channels)")
            output_found = True
    except Exception as e:
        print(f"  {i}: Error - {e}")

if not output_found:
    print("\n✗ No output devices found!")
    sys.exit(1)

p.terminate()
print("\n✓ PyAudio test passed!")
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ PyAudio test failed!"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check audio hardware: aplay -l"
    echo "2. Test ALSA: speaker-test -t sine -f 1000 -l 1"
    echo "3. Check permissions: groups (should include 'audio')"
    echo "4. If you added to audio group, logout and login again"
    deactivate
    exit 1
fi

deactivate

echo ""
echo "=== Audio fix complete! ==="
echo ""
echo "Next steps:"
echo "1. If you were added to the audio group, logout and login"
echo "2. Restart the service: sudo systemctl restart clicktrack@pi.service"
echo "3. Check logs: sudo journalctl -u clicktrack@pi.service -f"
echo ""
