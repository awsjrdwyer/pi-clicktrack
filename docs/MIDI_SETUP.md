# MIDI Setup Guide

## Overview

The Click Track Player supports MIDI control for hands-free operation during live performances. This guide covers connecting MIDI devices, configuring MIDI mappings, and troubleshooting common issues.

## Supported MIDI Devices

The application supports any MIDI device that can send MIDI Note On messages, including:

- **MIDI Foot Controllers** (e.g., Behringer FCB1010, Roland FC-300)
- **MIDI Keyboards** (any keyboard with MIDI output)
- **MIDI Pad Controllers** (e.g., Akai MPD series, Novation Launchpad)
- **MIDI Drum Pads** (e.g., Roland SPD-SX, Alesis SamplePad)
- **Custom MIDI Controllers** (Arduino-based, etc.)

## Hardware Connection

### USB MIDI Devices

1. Connect your MIDI device to the Raspberry Pi via USB
2. The device should be automatically detected by the Linux kernel
3. Verify detection:
   ```bash
   lsusb
   ```
   You should see your MIDI device in the list

### 5-Pin DIN MIDI Devices

If your MIDI device uses traditional 5-pin DIN connectors:

1. Connect a USB MIDI interface to the Raspberry Pi
2. Connect your MIDI device to the MIDI interface using a MIDI cable
3. Verify detection:
   ```bash
   aconnect -l
   ```

## Software Setup

### Verify MIDI Device Detection

Check that ALSA recognizes your MIDI device:

```bash
# List MIDI devices
aconnect -l

# You should see output like:
# client 20: 'USB MIDI Device' [type=kernel]
#     0 'USB MIDI Device MIDI 1'
```

### Check User Permissions

Ensure your user has permission to access MIDI devices:

```bash
# Check group membership
groups $USER

# You should see 'audio' in the list
# If not, add yourself to the audio group:
sudo usermod -a -G audio $USER

# Log out and log back in for changes to take effect
```

### Enable MIDI in Configuration

Edit `~/.clicktrack/config.yaml`:

```yaml
midi:
  enabled: true
  mappings:
    play: 60      # Middle C
    stop: 61      # C#
    next: 62      # D
    previous: 63  # D#
```

Restart the application:
```bash
sudo systemctl restart clicktrack@$USER.service
```

## MIDI Mappings

### Default Mappings

| Command  | MIDI Note | Note Name | Octave |
|----------|-----------|-----------|--------|
| Play     | 60        | C         | 4      |
| Stop     | 61        | C#        | 4      |
| Next     | 62        | D         | 4      |
| Previous | 63        | D#        | 4      |

### Finding Your Device's MIDI Notes

To determine which MIDI notes your device sends:

1. Install a MIDI monitor tool:
   ```bash
   sudo apt-get install alsa-utils
   ```

2. Run the MIDI monitor:
   ```bash
   aseqdump -p <port>
   ```
   Replace `<port>` with your device's port number from `aconnect -l`

3. Press buttons/keys on your MIDI device and observe the output:
   ```
   Note on                0, note 60, velocity 127
   Note off               0, note 60, velocity 0
   ```

4. Note the MIDI note numbers for each button you want to use

### Custom Mappings

Edit `~/.clicktrack/config.yaml` with your custom note numbers:

```yaml
midi:
  enabled: true
  mappings:
    play: 36      # Kick drum pad
    stop: 38      # Snare drum pad
    next: 42      # Hi-hat pad
    previous: 46  # Open hi-hat pad
```

### Example Configurations

#### Behringer FCB1010 Foot Controller

```yaml
midi:
  enabled: true
  mappings:
    play: 0       # Pedal 1
    stop: 1       # Pedal 2
    next: 2       # Pedal 3
    previous: 3   # Pedal 4
```

#### Akai MPD218 Pad Controller

```yaml
midi:
  enabled: true
  mappings:
    play: 36      # Pad 1
    stop: 37      # Pad 2
    next: 38      # Pad 3
    previous: 39  # Pad 4
```

#### Roland SPD-SX Drum Pad

```yaml
midi:
  enabled: true
  mappings:
    play: 60      # Pad 1
    stop: 62      # Pad 2
    next: 64      # Pad 3
    previous: 65  # Pad 4
```

## Testing MIDI Control

### Test MIDI Input

1. Start the application:
   ```bash
   sudo systemctl start clicktrack@$USER.service
   ```

2. Monitor the logs:
   ```bash
   sudo journalctl -u clicktrack@$USER.service -f
   ```

3. Press buttons on your MIDI device

4. You should see log messages like:
   ```
   INFO: MIDI Note On: 60, velocity: 127
   INFO: Play command received
   ```

### Test Playback Control

1. Open the web interface: `http://localhost:3000/play`
2. Load a set
3. Press the "Play" button on your MIDI device
4. The click track should start playing
5. Press the "Stop" button on your MIDI device
6. The click track should stop

## Advanced Configuration

### MIDI Velocity Sensitivity

Currently, the application responds to any MIDI Note On message regardless of velocity. Future versions may support velocity-sensitive controls.

### MIDI Control Change (CC) Messages

The current version only supports MIDI Note On messages. MIDI CC support may be added in future versions.

### Multiple MIDI Devices

If you have multiple MIDI devices connected, the application will use the first available device. To specify a particular device, you can modify the MIDI handler code to select by device name.

## Troubleshooting

### MIDI Device Not Detected

**Problem:** Application logs show "No MIDI devices found"

**Solutions:**
1. Verify device is connected: `lsusb` or `aconnect -l`
2. Check USB cable and port
3. Try a different USB port
4. Restart the Raspberry Pi
5. Check device power (some devices require external power)

### MIDI Commands Not Working

**Problem:** MIDI device is detected but commands don't work

**Solutions:**
1. Verify MIDI note numbers using `aseqdump`
2. Check configuration file: `cat ~/.clicktrack/config.yaml`
3. Ensure MIDI is enabled in configuration
4. Restart the service after configuration changes
5. Check logs for MIDI-related errors

### Permission Denied Errors

**Problem:** Logs show "Permission denied" when accessing MIDI device

**Solutions:**
1. Add user to audio group: `sudo usermod -a -G audio $USER`
2. Log out and log back in
3. Verify group membership: `groups $USER`
4. Check device permissions: `ls -l /dev/snd/*`

### MIDI Device Disconnects

**Problem:** MIDI device stops working during performance

**Solutions:**
1. Use a high-quality USB cable
2. Connect directly to Raspberry Pi (avoid USB hubs if possible)
3. Check power supply (ensure Raspberry Pi has adequate power)
4. Check logs for USB errors: `dmesg | grep -i usb`
5. Consider using a powered USB hub

### Latency Issues

**Problem:** Noticeable delay between pressing MIDI button and action

**Solutions:**
1. This is typically not a MIDI issue but an audio latency issue
2. Adjust audio buffer settings in ALSA configuration
3. Use a dedicated audio interface with lower latency
4. Reduce system load (close unnecessary applications)

### Wrong Commands Triggered

**Problem:** Pressing one button triggers a different command

**Solutions:**
1. Verify MIDI note numbers with `aseqdump`
2. Update configuration file with correct note numbers
3. Some devices send multiple MIDI messages per button press - check logs
4. Ensure device is in the correct mode/bank

## Best Practices for Live Performance

1. **Test Before the Gig**
   - Test all MIDI controls before the performance
   - Verify each button triggers the correct action
   - Test with the actual songs/sets you'll use

2. **Label Your Controller**
   - Use tape or labels to mark which buttons do what
   - Use different colors for different functions
   - Make labels visible in low light

3. **Backup Control Method**
   - Always have the web interface available as backup
   - Keep a tablet or phone with the web interface open
   - Know how to control playback without MIDI

4. **Cable Management**
   - Secure MIDI cables with tape or cable ties
   - Use cable strain relief to prevent disconnection
   - Keep cables away from foot traffic

5. **Power Management**
   - Use a reliable power supply for the Raspberry Pi
   - Consider a UPS (uninterruptible power supply)
   - Ensure MIDI device has adequate power

6. **Positioning**
   - Place MIDI controller within easy reach
   - Ensure you can see the web interface screen
   - Position so you can operate without looking down

## Example Setups

### Setup 1: Drummer with Foot Controller

**Hardware:**
- Behringer FCB1010 foot controller
- Raspberry Pi 4
- USB audio interface

**Configuration:**
```yaml
midi:
  enabled: true
  mappings:
    play: 0       # Left foot, front pedal
    stop: 1       # Left foot, back pedal
    next: 2       # Right foot, front pedal
    previous: 3   # Right foot, back pedal
```

**Usage:**
- Drummer controls click track with feet while playing
- Web interface on tablet for song/set management
- Audio output to drummer's in-ear monitors

### Setup 2: Guitarist with Pad Controller

**Hardware:**
- Akai MPD218 pad controller
- Raspberry Pi 3B+
- Built-in audio output

**Configuration:**
```yaml
midi:
  enabled: true
  mappings:
    play: 36      # Large pad, top-left
    stop: 37      # Large pad, top-right
    next: 38      # Large pad, bottom-left
    previous: 39  # Large pad, bottom-right
```

**Usage:**
- Guitarist controls click track between songs
- Pads are large and easy to hit
- Audio output to PA system for entire band

### Setup 3: Keyboard Player with MIDI Keyboard

**Hardware:**
- Any MIDI keyboard
- Raspberry Pi 4
- USB audio interface

**Configuration:**
```yaml
midi:
  enabled: true
  mappings:
    play: 48      # C3 (low C)
    stop: 50      # D3
    next: 52      # E3
    previous: 53  # F3
```

**Usage:**
- Keyboard player uses low keys for control
- Keys are outside normal playing range
- Can control with left hand while playing with right

## Firmware Updates

Some MIDI devices may require firmware updates for optimal compatibility. Check your device manufacturer's website for updates.

## Additional Resources

- [ALSA MIDI Documentation](https://www.alsa-project.org/wiki/MIDI)
- [Linux Audio Wiki](https://wiki.linuxaudio.org/)
- [MIDI Association](https://www.midi.org/)

## Support

If you encounter issues not covered in this guide, please:
1. Check the application logs: `sudo journalctl -u clicktrack@$USER.service`
2. Test with `aseqdump` to verify MIDI messages
3. Report issues with detailed logs and device information
