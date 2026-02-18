#!/usr/bin/env python3
"""
MIDI Testing Script for Click Track Player

This script helps test MIDI connectivity and see what messages
your MIDI controller is sending.
"""

import rtmidi
import time
import sys

def list_midi_ports():
    """List all available MIDI input ports."""
    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()
    
    if not ports:
        print("❌ No MIDI ports available")
        print("\nTroubleshooting:")
        print("  1. Check if your MIDI device is connected")
        print("  2. For Bluetooth MIDI, ensure device is paired and connected")
        print("  3. Run: bluetoothctl devices")
        return None
    
    print("✓ Available MIDI input ports:")
    for i, port in enumerate(ports):
        print(f"  {i}: {port}")
    
    return ports

def test_midi_input(port_index=0):
    """Listen for MIDI messages on the specified port."""
    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()
    
    if not ports:
        print("❌ No MIDI ports available")
        return
    
    if port_index >= len(ports):
        print(f"❌ Port index {port_index} out of range (0-{len(ports)-1})")
        return
    
    print(f"\n✓ Opening MIDI port: {ports[port_index]}")
    midi_in.open_port(port_index)
    
    print("\n" + "="*60)
    print("  Listening for MIDI messages...")
    print("  Press buttons/keys on your MIDI controller")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    try:
        while True:
            msg = midi_in.get_message()
            if msg:
                message, deltatime = msg
                
                # Parse MIDI message
                if len(message) >= 1:
                    status = message[0]
                    msg_type = status & 0xF0
                    channel = (status & 0x0F) + 1
                    
                    # Control Change (CC)
                    if msg_type == 0xB0 and len(message) >= 3:
                        cc_num = message[1]
                        cc_val = message[2]
                        print(f"📨 Control Change: CC {cc_num:3d} = {cc_val:3d} (Channel {channel})")
                    
                    # Note On
                    elif msg_type == 0x90 and len(message) >= 3:
                        note = message[1]
                        velocity = message[2]
                        if velocity > 0:
                            print(f"🎵 Note On:  Note {note:3d}, Velocity {velocity:3d} (Channel {channel})")
                        else:
                            print(f"🎵 Note Off: Note {note:3d} (Channel {channel})")
                    
                    # Note Off
                    elif msg_type == 0x80 and len(message) >= 3:
                        note = message[1]
                        print(f"🎵 Note Off: Note {note:3d} (Channel {channel})")
                    
                    # Program Change
                    elif msg_type == 0xC0 and len(message) >= 2:
                        program = message[1]
                        print(f"🎛️  Program Change: {program:3d} (Channel {channel})")
                    
                    # Other messages
                    else:
                        print(f"📨 MIDI: {message} (Raw)")
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\n✓ Stopped listening")
    finally:
        midi_in.close_port()

def main():
    """Main function."""
    print("\n" + "="*60)
    print("  MIDI Testing Tool for Click Track Player")
    print("="*60 + "\n")
    
    # List available ports
    ports = list_midi_ports()
    
    if not ports:
        sys.exit(1)
    
    # Ask user which port to test
    print("\n")
    if len(ports) == 1:
        port_index = 0
        print(f"Using port 0: {ports[0]}")
    else:
        try:
            port_index = int(input(f"Enter port number to test (0-{len(ports)-1}): "))
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input")
            sys.exit(1)
    
    # Test the selected port
    test_midi_input(port_index)
    
    print("\n" + "="*60)
    print("  Configuration Tips")
    print("="*60)
    print("\nTo use these MIDI messages in Click Track Player:")
    print("  1. Edit: ~/.clicktrack/config.yaml")
    print("  2. Add MIDI mappings using the CC numbers you see above")
    print("  3. Example:")
    print("     midi:")
    print("       enabled: true")
    print("       device_name: \"YourMIDIController\"")
    print("       mappings:")
    print("         play: 64      # Use CC number from above")
    print("         stop: 65")
    print("         next: 66")
    print("         previous: 67")
    print("\n")

if __name__ == "__main__":
    main()
