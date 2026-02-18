# Manual Bluetooth MIDI Pairing Guide

If the automated setup script has issues, follow these manual steps to pair your Bluetooth MIDI controller.

## Step 1: Prepare Bluetooth

```bash
# Restart Bluetooth service
sudo systemctl restart bluetooth

# Wait a few seconds
sleep 3

# Unblock Bluetooth if needed
sudo rfkill unblock bluetooth
```

## Step 2: Start bluetoothctl

```bash
bluetoothctl
```

You should see a prompt like: `[bluetooth]#`

## Step 3: Configure Bluetooth Adapter

At the bluetoothctl prompt, run these commands one at a time:

```bash
power on
agent on
default-agent
```

Wait for each command to complete before running the next one.

## Step 4: Scan for Devices

Put your MIDI controller in pairing mode (check your controller's manual), then:

```bash
scan on
```

Wait 10-15 seconds. You should see devices appear like:
```
[NEW] Device AA:BB:CC:DD:EE:FF YourMIDIController
```

When you see your device, run:
```bash
scan off
```

## Step 5: Pair and Connect

Replace `AA:BB:CC:DD:EE:FF` with your device's MAC address:

```bash
pair AA:BB:CC:DD:EE:FF
```

Wait for pairing to complete. If asked for a PIN, try `0000` or `1234`.

Then trust and connect:
```bash
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
```

## Step 6: Verify Connection

Check if connected:
```bash
info AA:BB:CC:DD:EE:FF
```

Look for `Connected: yes` in the output.

Exit bluetoothctl:
```bash
quit
```

## Step 7: Test MIDI Connection

```bash
cd ~/clicktrack
source venv/bin/activate
python3 test-midi.py
```

You should see your MIDI controller listed. Press buttons on it to see MIDI messages.

## Step 8: Configure Auto-Reconnect

Create a systemd service to reconnect on boot:

```bash
sudo nano /etc/systemd/system/bluetooth-midi-reconnect.service
```

Add this content (replace MAC address):
```ini
[Unit]
Description=Bluetooth MIDI Auto-Reconnect
After=bluetooth.service

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/bluetoothctl connect AA:BB:CC:DD:EE:FF
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, Y, Enter).

Enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bluetooth-midi-reconnect.service
```

## Step 9: Configure Click Track Player

Edit the configuration:
```bash
nano ~/.clicktrack/config.yaml
```

Add MIDI configuration:
```yaml
midi:
  enabled: true
  device_name: "YourMIDIController"  # Use exact name from test-midi.py
  mappings:
    play: 64      # CC number from your controller
    stop: 65
    next: 66
    previous: 67
```

Restart the service:
```bash
sudo systemctl restart clicktrack@pi.service
```

## Step 10: Test

Check logs to verify MIDI is working:
```bash
sudo journalctl -u clicktrack@pi.service -f
```

Press buttons on your MIDI controller and you should see log messages.

## Common Issues

### Device Won't Pair

1. Make sure device is in pairing mode
2. Try removing old pairing:
   ```bash
   bluetoothctl
   remove AA:BB:CC:DD:EE:FF
   scan on
   # Wait for device to appear
   pair AA:BB:CC:DD:EE:FF
   ```

### Device Pairs But Won't Connect

1. Check if device is already connected to another device (phone, computer)
2. Power cycle the MIDI controller
3. Try:
   ```bash
   bluetoothctl
   disconnect AA:BB:CC:DD:EE:FF
   connect AA:BB:CC:DD:EE:FF
   ```

### No MIDI Ports Showing

1. Verify Bluetooth connection:
   ```bash
   bluetoothctl info AA:BB:CC:DD:EE:FF
   ```
   Should show `Connected: yes`

2. Check if device supports MIDI over Bluetooth:
   - Some devices need to be in a specific MIDI mode
   - Check manufacturer documentation

3. Install additional packages:
   ```bash
   sudo apt-get install bluez-alsa-utils
   ```

### Device Disconnects After Reboot

1. Check auto-reconnect service:
   ```bash
   sudo systemctl status bluetooth-midi-reconnect.service
   ```

2. If failed, check logs:
   ```bash
   sudo journalctl -u bluetooth-midi-reconnect.service
   ```

3. Increase delay in service file:
   ```bash
   sudo nano /etc/systemd/system/bluetooth-midi-reconnect.service
   ```
   Change `ExecStartPre=/bin/sleep 5` to `ExecStartPre=/bin/sleep 10`

## Alternative: USB MIDI

If Bluetooth MIDI continues to have issues, consider using a USB MIDI adapter:

1. Connect USB MIDI device
2. Check if detected:
   ```bash
   cd ~/clicktrack
   source venv/bin/activate
   python3 test-midi.py
   ```

USB MIDI is more reliable and has lower latency than Bluetooth.

## Getting Help

If you're still having issues:

1. Check Bluetooth adapter status:
   ```bash
   bluetoothctl show
   hciconfig -a
   ```

2. Check system logs:
   ```bash
   sudo journalctl -u bluetooth -n 50
   ```

3. Verify Bluetooth hardware:
   ```bash
   lsusb | grep -i bluetooth
   ```

4. Test with another Bluetooth device (phone, speaker) to verify adapter works

For more help, see the main documentation at `docs/BLUETOOTH_MIDI_SETUP.md`.
