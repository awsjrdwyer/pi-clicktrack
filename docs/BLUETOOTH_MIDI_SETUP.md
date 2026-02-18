# Bluetooth MIDI Setup Guide

This guide will help you connect a Bluetooth MIDI controller to your Raspberry Pi for use with the Click Track Player.

## Prerequisites

The Click Track Player already has MIDI support built-in via the `python-rtmidi` library. You just need to set up Bluetooth MIDI connectivity on your Raspberry Pi.

## Installation Steps

### 1. Install Required Packages

```bash
sudo apt-get update
sudo apt-get install -y bluez bluez-tools pulseaudio-module-bluetooth
```

### 2. Enable Bluetooth Service

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 3. Pair Your Bluetooth MIDI Controller

#### Option A: Using bluetoothctl (Command Line)

1. Start the Bluetooth control utility:
```bash
bluetoothctl
```

2. Inside bluetoothctl, run these commands:
```bash
power on
agent on
default-agent
scan on
```

3. Wait for your MIDI controller to appear in the scan results. It will show something like:
```
[NEW] Device AA:BB:CC:DD:EE:FF YourMIDIController
```

4. Note the MAC address (AA:BB:CC:DD:EE:FF) and pair with it:
```bash
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
```

5. Exit bluetoothctl:
```bash
quit
```

#### Option B: Using Raspberry Pi Desktop (GUI)

1. Click the Bluetooth icon in the system tray
2. Click "Add Device"
3. Select your MIDI controller from the list
4. Click "Pair"

### 4. Install and Configure bluez-alsa-utils (for MIDI over Bluetooth)

```bash
sudo apt-get install -y bluez-alsa-utils
```

### 5. Verify MIDI Connection

After pairing, check if your MIDI device is visible:

```bash
# List all MIDI ports
python3 -c "import rtmidi; midi_in = rtmidi.MidiIn(); print('Available MIDI inputs:'); [print(f'  {i}: {port}') for i, port in enumerate(midi_in.get_ports())]"
```

You should see your Bluetooth MIDI controller listed.

## Configuring Click Track Player for MIDI

### 1. Find Your MIDI Device Name

Run the helper script to list available MIDI devices:

```bash
cd ~/clicktrack
source venv/bin/activate
python3 -c "import rtmidi; midi_in = rtmidi.MidiIn(); [print(port) for port in midi_in.get_ports()]"
```

### 2. Update Configuration

Edit the configuration file:

```bash
nano ~/.clicktrack/config.yaml
```

Add or update the MIDI section:

```yaml
midi:
  enabled: true
  device_name: "YourMIDIController"  # Use the exact name from step 1
  
  # MIDI CC mappings (Control Change messages)
  mappings:
    play: 64      # CC 64 (Sustain pedal) triggers Play
    stop: 65      # CC 65 triggers Stop
    next: 66      # CC 66 triggers Next Song
    previous: 67  # CC 67 triggers Previous Song
```

### 3. Restart the Service

```bash
sudo systemctl restart clicktrack@pi.service
```

### 4. Test MIDI Control

Check the logs to see if MIDI is working:

```bash
sudo journalctl -u clicktrack@pi.service -f
```

Press buttons on your MIDI controller and you should see log messages indicating MIDI commands are being received.

## Common MIDI Controllers and Their Settings

### Foot Pedals (e.g., Behringer FCB1010, Line 6 FBV)
- Usually send CC messages or Program Change messages
- Configure each pedal to send a specific CC number
- Map those CC numbers in the config.yaml file

### MIDI Keyboards
- Can use sustain pedal (CC 64) for Play/Stop
- Can use modulation wheel (CC 1) or other controllers
- Can use specific keys (Note On messages)

### Bluetooth MIDI Pedals (e.g., AirTurn, PageFlip)
- Often appear as "AirTurn" or "PageFlip" in Bluetooth devices
- May send keyboard commands by default - need to configure for MIDI mode
- Check manufacturer documentation for MIDI mode setup

## Troubleshooting

## Troubleshooting

### "SetDiscoveryFilter failed: org.bluez.Error.NotReady"

This error means the Bluetooth adapter isn't ready. Try these steps:

1. Restart Bluetooth service:
```bash
sudo systemctl restart bluetooth
sleep 3
```

2. Unblock Bluetooth (if blocked):
```bash
sudo rfkill unblock bluetooth
```

3. Power on the adapter manually:
```bash
bluetoothctl
power on
agent on
default-agent
scan on
# Wait 15 seconds
scan off
devices
quit
```

4. Check adapter status:
```bash
bluetoothctl show
```

You should see "Powered: yes" in the output.

### MIDI Device Not Showing Up

1. Check Bluetooth connection:
```bash
bluetoothctl
devices
info AA:BB:CC:DD:EE:FF
```

2. Reconnect if needed:
```bash
bluetoothctl
connect AA:BB:CC:DD:EE:FF
```

### MIDI Commands Not Working

1. Check if MIDI is enabled in config:
```bash
cat ~/.clicktrack/config.yaml | grep -A 5 "midi:"
```

2. Check service logs for errors:
```bash
sudo journalctl -u clicktrack@pi.service -n 50
```

3. Test MIDI input directly:
```bash
cd ~/clicktrack
source venv/bin/activate
python3 << 'EOF'
import rtmidi
import time

midi_in = rtmidi.MidiIn()
ports = midi_in.get_ports()

if not ports:
    print("No MIDI ports available")
else:
    print("Available MIDI ports:")
    for i, port in enumerate(ports):
        print(f"  {i}: {port}")
    
    print("\nOpening first port...")
    midi_in.open_port(0)
    
    print("Listening for MIDI messages (press Ctrl+C to stop)...")
    print("Press buttons on your MIDI controller...")
    
    try:
        while True:
            msg = midi_in.get_message()
            if msg:
                message, deltatime = msg
                print(f"MIDI message: {message}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped")
EOF
```

### Auto-Reconnect on Boot

To ensure your Bluetooth MIDI device reconnects automatically after reboot:

1. Create a systemd service:
```bash
sudo nano /etc/systemd/system/bluetooth-midi-reconnect.service
```

2. Add this content (replace MAC address with your device):
```ini
[Unit]
Description=Bluetooth MIDI Auto-Reconnect
After=bluetooth.service

[Service]
Type=oneshot
ExecStart=/usr/bin/bluetoothctl connect AA:BB:CC:DD:EE:FF
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

3. Enable the service:
```bash
sudo systemctl enable bluetooth-midi-reconnect.service
```

## Alternative: USB MIDI

If Bluetooth MIDI is unreliable, consider using a USB MIDI interface:

1. Connect USB MIDI device to Raspberry Pi
2. It should appear automatically in MIDI port list
3. No additional configuration needed
4. More reliable and lower latency than Bluetooth

## Next Steps

Once MIDI is working:
- Test each MIDI command (Play, Stop, Next, Previous)
- Adjust CC mappings to match your controller
- Consider adding more MIDI mappings for additional features
- Set up auto-reconnect for seamless operation

For more information, see the main documentation at `docs/EXAMPLES.md`.
