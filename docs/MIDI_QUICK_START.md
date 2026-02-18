# MIDI Quick Start Guide

Quick reference for setting up MIDI control with Click Track Player.

## Quick Setup (3 Steps)

### 1. Connect Your MIDI Device

**For USB MIDI:**
- Plug in your USB MIDI controller
- It should be detected automatically

**For Bluetooth MIDI:**
```bash
cd ~/clicktrack
./setup-bluetooth-midi.sh
```

### 2. Test MIDI Connection

```bash
cd ~/clicktrack
source venv/bin/activate
python3 test-midi.py
```

Press buttons on your controller and note the CC numbers or note numbers displayed.

### 3. Configure MIDI Mappings

Edit the configuration file:
```bash
nano ~/.clicktrack/config.yaml
```

Add your MIDI mappings:
```yaml
midi:
  enabled: true
  device_name: "YourMIDIController"  # Optional - auto-detects if not specified
  
  mappings:
    play: 64      # Replace with CC number from test
    stop: 65      # Replace with CC number from test
    next: 66      # Replace with CC number from test
    previous: 67  # Replace with CC number from test
```

Restart the service:
```bash
sudo systemctl restart clicktrack@pi.service
```

## Common MIDI Controllers

### Foot Pedals

**Behringer FCB1010:**
- Configure each pedal to send CC messages
- Typical setup: CC 64-67 for the four main controls

**Line 6 FBV:**
- Use expression pedal mode
- Map pedals to CC numbers

**AirTurn / PageFlip (Bluetooth):**
- Put device in MIDI mode (check manual)
- Usually sends CC or Note messages
- Pair via Bluetooth before configuring

### MIDI Keyboards

**Using Sustain Pedal:**
```yaml
midi:
  mappings:
    play: 64   # Sustain pedal (CC 64)
    stop: 65   # Sostenuto pedal (CC 66)
    next: 1    # Modulation wheel (CC 1)
    previous: 2  # Breath controller (CC 2)
```

**Using Keys:**
```yaml
midi:
  mappings:
    play: 60   # Middle C
    stop: 61   # C#
    next: 62   # D
    previous: 63  # D#
```

## Troubleshooting

### MIDI Device Not Found

```bash
# Check if device is connected
python3 -c "import rtmidi; midi_in = rtmidi.MidiIn(); print(midi_in.get_ports())"

# For Bluetooth, check connection
bluetoothctl devices
bluetoothctl info AA:BB:CC:DD:EE:FF
```

### MIDI Commands Not Working

1. Check service logs:
```bash
sudo journalctl -u clicktrack@pi.service -f
```

2. Verify MIDI is enabled in config:
```bash
cat ~/.clicktrack/config.yaml | grep -A 10 "midi:"
```

3. Test MIDI messages are being received:
```bash
cd ~/clicktrack
source venv/bin/activate
python3 test-midi.py
```

### Bluetooth MIDI Disconnects

Create auto-reconnect service (done automatically by setup script):
```bash
sudo systemctl status bluetooth-midi-reconnect.service
```

If not created, run:
```bash
./setup-bluetooth-midi.sh
```

## Advanced Configuration

### Multiple MIDI Devices

Specify which device to use:
```yaml
midi:
  enabled: true
  device_name: "Specific Controller Name"  # Exact name from MIDI port list
```

### Custom CC Mappings

You can use any CC number (0-127):
```yaml
midi:
  mappings:
    play: 20
    stop: 21
    next: 22
    previous: 23
```

### Using Note Messages Instead of CC

The MIDI handler supports both CC and Note messages. If your controller sends notes:
```yaml
midi:
  mappings:
    play: 60   # Note 60 (Middle C)
    stop: 61   # Note 61 (C#)
    next: 62   # Note 62 (D)
    previous: 63  # Note 63 (D#)
```

## Files and Scripts

- `setup-bluetooth-midi.sh` - Bluetooth MIDI setup wizard
- `test-midi.py` - MIDI testing and debugging tool
- `docs/BLUETOOTH_MIDI_SETUP.md` - Detailed Bluetooth MIDI guide
- `~/.clicktrack/config.yaml` - Configuration file

## Getting Help

1. Check logs: `sudo journalctl -u clicktrack@pi.service -f`
2. Test MIDI: `python3 test-midi.py`
3. Review detailed guide: `docs/BLUETOOTH_MIDI_SETUP.md`
4. Check Bluetooth: `bluetoothctl devices`

## Next Steps

Once MIDI is working:
- Test all four commands (Play, Stop, Next, Previous)
- Practice using MIDI control during a performance
- Consider adding more MIDI mappings for future features
- Set up auto-reconnect for Bluetooth devices
