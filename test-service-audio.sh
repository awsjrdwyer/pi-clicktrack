#!/bin/bash

# Test audio detection in the same environment as the systemd service
# This helps diagnose why the service can't find audio devices

echo "=== Testing Audio in Service Environment ==="
echo ""

echo "1. Testing as current user (should work):"
cd ~/clicktrack
source venv/bin/activate
python3 test-audio.py 2>&1 | grep -E "(Total devices|Found.*output|Successfully opened|Failed to open)"
deactivate
echo ""

echo "2. Testing with service environment variables:"
cd ~/clicktrack
source venv/bin/activate
AUDIODEV=hw:0,0 AUDIODRIVER=alsa PULSE_SERVER= python3 test-audio.py 2>&1 | grep -E "(Total devices|Found.*output|Successfully opened|Failed to open)"
deactivate
echo ""

echo "3. Checking if service can access audio devices:"
if [ -c /dev/snd/pcmC2D0p ]; then
    echo "  ✓ Audio device /dev/snd/pcmC2D0p exists"
    ls -l /dev/snd/pcmC2D0p
else
    echo "  ! Audio device /dev/snd/pcmC2D0p not found"
    echo "  Available audio devices:"
    ls -l /dev/snd/pcm* 2>/dev/null || echo "  No PCM devices found"
fi
echo ""

echo "4. Checking audio group membership:"
groups | grep -q audio && echo "  ✓ User is in audio group" || echo "  ✗ User NOT in audio group"
echo ""

echo "=== Test Complete ==="
