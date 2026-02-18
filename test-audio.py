#!/usr/bin/env python3
"""
Test script to check PyAudio device detection.
Run this on the Raspberry Pi to see what audio devices are available.
"""

import sys

try:
    import pyaudio
except ImportError:
    print("ERROR: PyAudio not installed")
    print("Install with: pip install pyaudio")
    sys.exit(1)

print("=== PyAudio Audio Device Test ===\n")

p = pyaudio.PyAudio()

print(f"PyAudio version: {pyaudio.__version__}")
print(f"Total devices found: {p.get_device_count()}\n")

# List host APIs
print("Host APIs:")
for i in range(p.get_host_api_count()):
    try:
        api_info = p.get_host_api_info_by_index(i)
        print(f"  {i}: {api_info['name']} ({api_info['deviceCount']} devices)")
    except Exception as e:
        print(f"  {i}: Error - {e}")

print("\nAll Devices:")
output_devices = []
for i in range(p.get_device_count()):
    try:
        info = p.get_device_info_by_index(i)
        device_type = []
        if info['maxInputChannels'] > 0:
            device_type.append(f"IN:{info['maxInputChannels']}")
        if info['maxOutputChannels'] > 0:
            device_type.append(f"OUT:{info['maxOutputChannels']}")
            output_devices.append((i, info))
        
        type_str = ", ".join(device_type) if device_type else "NO I/O"
        print(f"  [{i:2d}] {info['name']}")
        print(f"       {type_str}, Rate: {info['defaultSampleRate']:.0f} Hz, Host API: {info['hostApi']}")
        
    except Exception as e:
        print(f"  [{i:2d}] Error getting device info: {e}")

print(f"\n=== Summary ===")
print(f"Found {len(output_devices)} output device(s)")

if output_devices:
    print("\nOutput devices:")
    for idx, info in output_devices:
        print(f"  [{idx}] {info['name']} ({info['maxOutputChannels']} channels)")
    
    # Try to open the first output device
    print(f"\nTrying to open device {output_devices[0][0]}...")
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            output=True,
            output_device_index=output_devices[0][0],
            frames_per_buffer=1024
        )
        print("✓ Successfully opened audio stream!")
        stream.close()
    except Exception as e:
        print(f"✗ Failed to open audio stream: {e}")
else:
    print("\n✗ No output devices found!")

p.terminate()
print("\n=== Test Complete ===")
