"""
MIDI Handler for the Click Track Player.

This module provides MIDI device detection, connection, and message parsing
to enable hands-free control of the click track player during live performances.
"""

import logging
import threading
from typing import Optional, Callable, Dict
import rtmidi

logger = logging.getLogger(__name__)


class MIDIHandler:
    """
    MIDI device handler for receiving and processing MIDI commands.
    
    This handler detects and connects to MIDI devices, parses incoming MIDI messages,
    and translates them into application commands using configurable note/CC mappings.
    It provides a callback-based interface for decoupling MIDI-specific logic from
    the rest of the application.
    """
    
    # Default MIDI note mappings
    DEFAULT_MAPPINGS = {
        'play': 60,      # Middle C
        'stop': 61,      # C#
        'next': 62,      # D
        'previous': 63   # D#
    }
    
    def __init__(self, mappings: Optional[Dict[str, int]] = None, device_name: Optional[str] = None, enable_display_output: bool = False):
        """
        Initialize the MIDI handler.
        
        Args:
            mappings: Optional dictionary of command-to-MIDI-note mappings.
                     If not provided, uses default mappings.
                     Format: {'play': 60, 'stop': 61, 'next': 62, 'previous': 63}
            device_name: Optional device name or substring to match. If provided,
                        will connect to the first device containing this string.
                        If not provided, connects to the first available device.
            enable_display_output: If True, sends track information to MIDI controller display
        """
        self.mappings = mappings if mappings is not None else self.DEFAULT_MAPPINGS.copy()
        self.device_name = device_name
        self.enable_display_output = enable_display_output
        
        # MIDI input
        self.midi_in: Optional[rtmidi.MidiIn] = None
        self.midi_port: Optional[int] = None
        
        # MIDI output (for sending display info to controller)
        self.midi_out: Optional[rtmidi.MidiOut] = None
        self.midi_out_port: Optional[int] = None
        
        # Callback functions
        self._play_callback: Optional[Callable[[], None]] = None
        self._stop_callback: Optional[Callable[[], None]] = None
        self._next_callback: Optional[Callable[[], None]] = None
        self._previous_callback: Optional[Callable[[], None]] = None
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Reconnection thread
        self._reconnect_thread: Optional[threading.Thread] = None
        self._stop_reconnect = threading.Event()
        self._reconnect_interval = 5  # seconds
        
        logger.info(f"MIDIHandler initialized with mappings: {self.mappings}")
        if device_name:
            logger.info(f"Will attempt to connect to device matching: {device_name}")
        if enable_display_output:
            logger.info("MIDI display output enabled")
    
    def initialize(self) -> bool:
        """
        Initialize MIDI device detection and connection.
        
        Attempts to detect and connect to a MIDI input device. If device_name
        is specified, connects to the first device containing that string.
        Otherwise, connects to the first available device (excluding "Midi Through").
        
        Also starts a background thread to monitor and reconnect if connection is lost.
        Even if no device is found initially, the thread will keep trying to connect.
        
        Returns:
            True if a MIDI device was successfully connected, False otherwise
        """
        success = self._connect_to_device()
        
        # Always start reconnection monitoring thread, even if initial connection fails
        # This allows the system to connect when the device becomes available later
        self._start_reconnect_thread()
        
        return success
    
    def _connect_to_device(self) -> bool:
        """
        Internal method to connect to MIDI device.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Close existing connection if any
            if self.midi_in:
                try:
                    self.midi_in.close_port()
                except:
                    pass
                self.midi_in = None
                self.midi_port = None
            
            # Create MIDI input
            self.midi_in = rtmidi.MidiIn()
            
            # Get available ports
            available_ports = self.midi_in.get_ports()
            
            if not available_ports:
                logger.debug("No MIDI input devices found")
                self.midi_in = None
                return False
            
            # Log available ports
            logger.debug(f"Available MIDI ports: {available_ports}")
            
            # Find the appropriate port
            selected_port = None
            
            if self.device_name:
                # Look for device matching the specified name
                for i, port in enumerate(available_ports):
                    if self.device_name.lower() in port.lower():
                        selected_port = i
                        logger.debug(f"Found matching device: {port}")
                        break
                
                if selected_port is None:
                    logger.debug(f"No device found matching '{self.device_name}'")
                    self.midi_in = None
                    return False
            
            # If no device name specified, use first non-"Midi Through" device
            if selected_port is None:
                for i, port in enumerate(available_ports):
                    if "Midi Through" not in port:
                        selected_port = i
                        logger.debug(f"Selected first non-'Midi Through' device: {port}")
                        break
            
            # If still no device (all are "Midi Through"), use first one
            if selected_port is None:
                selected_port = 0
                logger.debug(f"Using first available device: {available_ports[0]}")
            
            # Connect to the selected port
            self.midi_port = selected_port
            self.midi_in.open_port(self.midi_port)
            
            # Set callback for incoming MIDI messages
            self.midi_in.set_callback(self._midi_callback)
            
            logger.info(f"Connected to MIDI input device: {available_ports[self.midi_port]}")
            
            # If display output is enabled, also connect MIDI output
            if self.enable_display_output:
                self._connect_output_device()
            
            return True
        
        except ImportError as e:
            logger.error(f"MIDI library (python-rtmidi) not available: {e}")
            return False
        except rtmidi.SystemError as e:
            logger.debug(f"MIDI system error during connection: {e}")
            return False
        except Exception as e:
            logger.debug(f"Error connecting to MIDI device: {e}")
            return False
    
    def _connect_output_device(self):
        """
        Connect to MIDI output device for sending display information.
        Uses the same device as input.
        """
        try:
            # Close existing output connection if any
            if self.midi_out:
                try:
                    self.midi_out.close_port()
                except:
                    pass
                self.midi_out = None
                self.midi_out_port = None
            
            # Create MIDI output
            self.midi_out = rtmidi.MidiOut()
            
            # Get available output ports
            available_ports = self.midi_out.get_ports()
            
            if not available_ports:
                logger.debug("No MIDI output devices found")
                self.midi_out = None
                return
            
            # Find the same device we're using for input
            selected_port = None
            
            if self.device_name:
                for i, port in enumerate(available_ports):
                    if self.device_name.lower() in port.lower():
                        selected_port = i
                        break
            
            if selected_port is None:
                # Use first non-"Midi Through" device
                for i, port in enumerate(available_ports):
                    if "Midi Through" not in port:
                        selected_port = i
                        break
            
            if selected_port is None:
                selected_port = 0
            
            # Connect to the selected output port
            self.midi_out_port = selected_port
            self.midi_out.open_port(self.midi_out_port)
            
            logger.info(f"Connected to MIDI output device: {available_ports[self.midi_out_port]}")
        
        except Exception as e:
            logger.warning(f"Could not connect MIDI output device: {e}")
            self.midi_out = None
            self.midi_out_port = None
    
    def send_track_info(self, track_number: int, total_tracks: int, song_name: str = ""):
        """
        Send track information to MIDI controller display.
        
        Tries multiple MIDI message types to maximize compatibility:
        1. Program Change (most common for displays)
        2. Control Change CC#0 (Bank Select MSB)
        3. Control Change CC#32 (Bank Select LSB)
        
        Args:
            track_number: Current track number (1-based)
            total_tracks: Total number of tracks in set
            song_name: Optional song name (not all controllers can display this)
        """
        if not self.enable_display_output or not self.midi_out:
            return
        
        try:
            # Convert to 0-based for MIDI (0-127)
            program_number = min(track_number - 1, 127)
            
            # Try Program Change message (0xC0 + channel)
            # Most MIDI controllers display the program number
            message = [0xC0, program_number]
            self.midi_out.send_message(message)
            logger.debug(f"Sent Program Change: {program_number}")
            
            # Also try Control Change CC#0 (Bank Select MSB)
            # Some controllers use this for display
            message = [0xB0, 0, program_number]
            self.midi_out.send_message(message)
            logger.debug(f"Sent CC#0 (Bank MSB): {program_number}")
            
            # Also try Control Change CC#32 (Bank Select LSB)
            message = [0xB0, 32, program_number]
            self.midi_out.send_message(message)
            logger.debug(f"Sent CC#32 (Bank LSB): {program_number}")
            
            logger.info(f"Sent track info to MIDI display: Track {track_number}/{total_tracks}")
        
        except Exception as e:
            logger.warning(f"Error sending track info to MIDI display: {e}")
    
    def _start_reconnect_thread(self):
        """Start the background reconnection monitoring thread."""
        if self._reconnect_thread is None or not self._reconnect_thread.is_alive():
            self._stop_reconnect.clear()
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True,
                name="MIDI-Reconnect"
            )
            self._reconnect_thread.start()
            logger.info("MIDI reconnection monitoring thread started")
    
    def _reconnect_loop(self):
        """
        Background thread that monitors MIDI connection and attempts reconnection.
        
        This thread runs continuously, checking if the MIDI connection is still alive
        and attempting to reconnect if it's lost.
        """
        consecutive_failures = 0
        max_log_failures = 3  # Only log first few failures to avoid spam
        
        while not self._stop_reconnect.is_set():
            try:
                # Wait for the reconnect interval
                if self._stop_reconnect.wait(self._reconnect_interval):
                    # Stop event was set
                    break
                
                # Check if connection is still alive
                if not self.is_connected():
                    consecutive_failures += 1
                    
                    if consecutive_failures <= max_log_failures:
                        logger.warning("MIDI device disconnected, attempting to reconnect...")
                    elif consecutive_failures == max_log_failures + 1:
                        logger.info("MIDI reconnection attempts continuing in background (suppressing further logs)")
                    
                    # Attempt to reconnect
                    if self._connect_to_device():
                        logger.info("MIDI device reconnected successfully")
                        consecutive_failures = 0
                else:
                    # Connection is alive, reset failure counter
                    if consecutive_failures > 0:
                        consecutive_failures = 0
            
            except Exception as e:
                logger.error(f"Error in MIDI reconnection thread: {e}", exc_info=True)
        
        logger.debug("MIDI reconnection monitoring thread stopped")
    
    def _midi_callback(self, event, data=None):
        """
        Internal callback for processing incoming MIDI messages.
        
        This method is called by python-rtmidi when a MIDI message is received.
        It parses the message and triggers the appropriate command callback.
        
        Args:
            event: Tuple containing (message, delta_time)
            data: Optional user data (not used)
        """
        try:
            message, delta_time = event
            
            # Parse MIDI message
            # MIDI Note On: [144-159, note, velocity] (status byte 0x90-0x9F)
            # MIDI Note Off: [128-143, note, velocity] (status byte 0x80-0x8F)
            # MIDI CC: [176-191, controller, value] (status byte 0xB0-0xBF)
            
            if len(message) < 2:
                return
            
            status_byte = message[0]
            
            # Check for Note On message (velocity > 0)
            if 144 <= status_byte <= 159 and len(message) >= 3:
                note = message[1]
                velocity = message[2]
                
                # Only process Note On (velocity > 0), ignore Note Off (velocity = 0)
                if velocity > 0:
                    self._process_note(note)
            
            # Check for Control Change (CC) message
            elif 176 <= status_byte <= 191 and len(message) >= 3:
                controller = message[1]
                value = message[2]
                
                # Process CC as if it were a note (value > 0 triggers command)
                if value > 0:
                    self._process_note(controller)
        
        except Exception as e:
            # Log but don't crash - MIDI errors shouldn't stop the application
            logger.error(f"Error processing MIDI message: {e}", exc_info=True)
    
    def _process_note(self, note: int):
        """
        Process a MIDI note or CC and trigger the appropriate callback.
        
        Args:
            note: MIDI note number or CC number
        """
        with self._lock:
            # Check which command this note maps to
            if note == self.mappings.get('play') and self._play_callback:
                logger.info(f"MIDI command received: Play (note {note})")
                try:
                    self._play_callback()
                except Exception as e:
                    logger.error(f"Error executing play callback: {e}")
            
            elif note == self.mappings.get('stop') and self._stop_callback:
                logger.info(f"MIDI command received: Stop (note {note})")
                try:
                    self._stop_callback()
                except Exception as e:
                    logger.error(f"Error executing stop callback: {e}")
            
            elif note == self.mappings.get('next') and self._next_callback:
                logger.info(f"MIDI command received: Next (note {note})")
                try:
                    self._next_callback()
                except Exception as e:
                    logger.error(f"Error executing next callback: {e}")
            
            elif note == self.mappings.get('previous') and self._previous_callback:
                logger.info(f"MIDI command received: Previous (note {note})")
                try:
                    self._previous_callback()
                except Exception as e:
                    logger.error(f"Error executing previous callback: {e}")
    
    def on_play_command(self, callback: Callable[[], None]):
        """
        Register a callback for the play command.
        
        Args:
            callback: Function to call when play command is received
        """
        with self._lock:
            self._play_callback = callback
            logger.debug("Play callback registered")
    
    def on_stop_command(self, callback: Callable[[], None]):
        """
        Register a callback for the stop command.
        
        Args:
            callback: Function to call when stop command is received
        """
        with self._lock:
            self._stop_callback = callback
            logger.debug("Stop callback registered")
    
    def on_next_command(self, callback: Callable[[], None]):
        """
        Register a callback for the next song command.
        
        Args:
            callback: Function to call when next command is received
        """
        with self._lock:
            self._next_callback = callback
            logger.debug("Next callback registered")
    
    def on_previous_command(self, callback: Callable[[], None]):
        """
        Register a callback for the previous song command.
        
        Args:
            callback: Function to call when previous command is received
        """
        with self._lock:
            self._previous_callback = callback
            logger.debug("Previous callback registered")
    
    def close(self):
        """
        Close the MIDI connection and clean up resources.
        
        This method should be called when shutting down the application
        to properly release MIDI device resources.
        """
        # Stop the reconnection thread
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            logger.debug("Stopping MIDI reconnection thread...")
            self._stop_reconnect.set()
            self._reconnect_thread.join(timeout=10)
            if self._reconnect_thread.is_alive():
                logger.warning("MIDI reconnection thread did not stop gracefully")
        
        # Close MIDI input connection
        if self.midi_in:
            try:
                self.midi_in.close_port()
                logger.info("MIDI input connection closed")
            except rtmidi.SystemError as e:
                logger.warning(f"MIDI system error during close (device may be disconnected): {e}")
            except Exception as e:
                logger.error(f"Error closing MIDI input connection: {e}", exc_info=True)
            finally:
                self.midi_in = None
                self.midi_port = None
        
        # Close MIDI output connection
        if self.midi_out:
            try:
                self.midi_out.close_port()
                logger.info("MIDI output connection closed")
            except rtmidi.SystemError as e:
                logger.warning(f"MIDI system error during output close (device may be disconnected): {e}")
            except Exception as e:
                logger.error(f"Error closing MIDI output connection: {e}", exc_info=True)
            finally:
                self.midi_out = None
                self.midi_out_port = None
    
    def is_connected(self) -> bool:
        """
        Check if a MIDI device is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        if self.midi_in is None or self.midi_port is None:
            return False
        
        try:
            # Try to get the list of available ports to verify connection is alive
            available_ports = self.midi_in.get_ports()
            
            # Check if our device is still in the list
            if self.device_name:
                # Look for our specific device
                for port in available_ports:
                    if self.device_name.lower() in port.lower():
                        return True
                return False
            else:
                # Just check if there are any ports available
                return len(available_ports) > 0
        except:
            # Any error means we're not connected
            return False
