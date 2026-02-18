#!/bin/bash

# Click Track Player Diagnostic Script
# Run this on the Raspberry Pi to diagnose playback issues

echo "=== Click Track Player Diagnostics ==="
echo ""

# Check if service is running
echo "1. Service Status:"
systemctl is-active clicktrack@pi.service && echo "  ✓ Service is running" || echo "  ✗ Service is not running"
echo ""

# Check recent logs
echo "2. Recent Error Logs:"
sudo journalctl -u clicktrack@pi.service -n 20 | grep -i "error\|warning\|failed" || echo "  No errors found in recent logs"
echo ""

# Check if sound files exist
echo "3. Click Sound Files:"
SOUNDS_DIR="$HOME/clicktrack/assets/sounds"
if [ -d "$SOUNDS_DIR" ]; then
    echo "  ✓ Sounds directory exists: $SOUNDS_DIR"
    for sound in wood_block.wav beep.wav cowbell.wav; do
        if [ -f "$SOUNDS_DIR/$sound" ]; then
            echo "    ✓ $sound found"
        else
            echo "    ✗ $sound NOT FOUND"
        fi
    done
else
    echo "  ✗ Sounds directory NOT FOUND: $SOUNDS_DIR"
fi
echo ""

# Check Python packages
echo "4. Python Dependencies:"
source "$HOME/clicktrack/venv/bin/activate"
python3 -c "import pyaudio; print('  ✓ pyaudio installed (version: ' + pyaudio.__version__ + ')')" 2>/dev/null || echo "  ✗ pyaudio NOT installed"
python3 -c "import flask; print('  ✓ flask installed')" 2>/dev/null || echo "  ✗ flask NOT installed"
python3 -c "import flask_socketio; print('  ✓ flask-socketio installed')" 2>/dev/null || echo "  ✗ flask-socketio NOT installed"
deactivate
echo ""

# Check audio devices
echo "5. ALSA Audio Devices:"
if command -v aplay &> /dev/null; then
    aplay -l 2>/dev/null || echo "  No playback devices found"
else
    echo "  aplay command not found"
fi
echo ""

# Check PyAudio devices
echo "6. PyAudio Devices:"
source "$HOME/clicktrack/venv/bin/activate"
python3 << 'EOF'
try:
    import pyaudio
    p = pyaudio.PyAudio()
    
    print(f"  Found {p.get_device_count()} total devices")
    
    # List host APIs
    print("\n  Host APIs:")
    for i in range(p.get_host_api_count()):
        api_info = p.get_host_api_info_by_index(i)
        print(f"    {i}: {api_info['name']} ({api_info['deviceCount']} devices)")
    
    # List output devices
    print("\n  Output devices:")
    output_count = 0
    for i in range(p.get_device_count()):
        try:
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                print(f"    {i}: {info['name']} ({info['maxOutputChannels']} ch, {info['defaultSampleRate']} Hz)")
                output_count += 1
        except Exception as e:
            print(f"    {i}: Error - {e}")
    
    if output_count == 0:
        print("    ✗ No output devices found!")
    else:
        print(f"\n  ✓ Found {output_count} output device(s)")
    
    p.terminate()
except Exception as e:
    print(f"  ✗ Error: {e}")
EOF
deactivate
echo ""

# Check user groups
echo "7. User Groups:"
groups | grep -q audio && echo "  ✓ User is in audio group" || echo "  ✗ User is NOT in audio group (run: sudo usermod -a -G audio $USER)"
echo ""

# Check if port 3000 is listening
echo "8. Web Server:"
if netstat -tuln 2>/dev/null | grep -q ":3000 "; then
    echo "  ✓ Server is listening on port 3000"
elif ss -tuln 2>/dev/null | grep -q ":3000 "; then
    echo "  ✓ Server is listening on port 3000"
else
    echo "  ✗ Server is NOT listening on port 3000"
fi
echo ""

# Check ALSA configuration
echo "9. ALSA Configuration:"
if [ -f ~/.asoundrc ]; then
    echo "  ✓ User ALSA config exists (~/.asoundrc)"
else
    echo "  ! No user ALSA config (~/.asoundrc)"
fi
echo ""

# Show last 15 log lines
echo "10. Last 15 Log Lines:"
sudo journalctl -u clicktrack@pi.service -n 15 --no-pager
echo ""

echo "=== End of Diagnostics ==="
echo ""
echo "If audio is not working:"
echo "1. Run: ./fix-audio.sh"
echo "2. If added to audio group, logout and login"
echo "3. Restart service: sudo systemctl restart clicktrack@pi.service"
echo ""
