"""
Unit tests for the MIDI Handler.

These tests verify MIDI device detection, message parsing, and callback execution.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from clicktrack.midi_handler import MIDIHandler


class TestMIDIHandler:
    """Test suite for MIDIHandler class."""
    
    def test_initialization_with_default_mappings(self):
        """Test that MIDIHandler initializes with default mappings."""
        handler = MIDIHandler()
        
        assert handler.mappings == {
            'play': 60,
            'stop': 61,
            'next': 62,
            'previous': 63
        }
        assert handler.midi_in is None
        assert handler.midi_port is None
    
    def test_initialization_with_custom_mappings(self):
        """Test that MIDIHandler accepts custom mappings."""
        custom_mappings = {
            'play': 36,
            'stop': 37,
            'next': 38,
            'previous': 39
        }
        handler = MIDIHandler(mappings=custom_mappings)
        
        assert handler.mappings == custom_mappings
    
    @patch('clicktrack.midi_handler.rtmidi.MidiIn')
    def test_initialize_with_available_device(self, mock_midi_in_class):
        """Test successful MIDI device initialization."""
        # Mock MIDI device
        mock_midi_in = MagicMock()
        mock_midi_in.get_ports.return_value = ['USB MIDI Device']
        mock_midi_in_class.return_value = mock_midi_in
        
        handler = MIDIHandler()
        result = handler.initialize()
        
        assert result is True
        assert handler.is_connected()
        mock_midi_in.open_port.assert_called_once_with(0)
        mock_midi_in.set_callback.assert_called_once()
    
    @patch('clicktrack.midi_handler.rtmidi.MidiIn')
    def test_initialize_with_no_devices(self, mock_midi_in_class):
        """Test initialization when no MIDI devices are available."""
        # Mock no MIDI devices
        mock_midi_in = MagicMock()
        mock_midi_in.get_ports.return_value = []
        mock_midi_in_class.return_value = mock_midi_in
        
        handler = MIDIHandler()
        result = handler.initialize()
        
        assert result is False
        assert not handler.is_connected()
        mock_midi_in.open_port.assert_not_called()
    
    @patch('clicktrack.midi_handler.rtmidi.MidiIn')
    def test_initialize_with_error(self, mock_midi_in_class):
        """Test initialization handles errors gracefully."""
        # Mock MIDI error
        mock_midi_in_class.side_effect = Exception("MIDI error")
        
        handler = MIDIHandler()
        result = handler.initialize()
        
        assert result is False
        assert not handler.is_connected()
    
    def test_callback_registration(self):
        """Test that callbacks can be registered."""
        handler = MIDIHandler()
        
        play_callback = Mock()
        stop_callback = Mock()
        next_callback = Mock()
        previous_callback = Mock()
        
        handler.on_play_command(play_callback)
        handler.on_stop_command(stop_callback)
        handler.on_next_command(next_callback)
        handler.on_previous_command(previous_callback)
        
        assert handler._play_callback == play_callback
        assert handler._stop_callback == stop_callback
        assert handler._next_callback == next_callback
        assert handler._previous_callback == previous_callback
    
    def test_process_note_triggers_play_callback(self):
        """Test that play note triggers play callback."""
        handler = MIDIHandler()
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Simulate MIDI note 60 (play)
        handler._process_note(60)
        
        play_callback.assert_called_once()
    
    def test_process_note_triggers_stop_callback(self):
        """Test that stop note triggers stop callback."""
        handler = MIDIHandler()
        stop_callback = Mock()
        handler.on_stop_command(stop_callback)
        
        # Simulate MIDI note 61 (stop)
        handler._process_note(61)
        
        stop_callback.assert_called_once()
    
    def test_process_note_triggers_next_callback(self):
        """Test that next note triggers next callback."""
        handler = MIDIHandler()
        next_callback = Mock()
        handler.on_next_command(next_callback)
        
        # Simulate MIDI note 62 (next)
        handler._process_note(62)
        
        next_callback.assert_called_once()
    
    def test_process_note_triggers_previous_callback(self):
        """Test that previous note triggers previous callback."""
        handler = MIDIHandler()
        previous_callback = Mock()
        handler.on_previous_command(previous_callback)
        
        # Simulate MIDI note 63 (previous)
        handler._process_note(63)
        
        previous_callback.assert_called_once()
    
    def test_process_note_ignores_unmapped_notes(self):
        """Test that unmapped notes don't trigger callbacks."""
        handler = MIDIHandler()
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Simulate unmapped MIDI note
        handler._process_note(99)
        
        play_callback.assert_not_called()
    
    def test_process_note_with_no_callback_registered(self):
        """Test that processing note without callback doesn't crash."""
        handler = MIDIHandler()
        
        # Should not raise exception
        handler._process_note(60)
    
    def test_midi_callback_note_on(self):
        """Test MIDI callback processes Note On messages."""
        handler = MIDIHandler()
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Simulate MIDI Note On message: [status, note, velocity]
        # Status 144 = Note On channel 1, note 60, velocity 100
        message = [144, 60, 100]
        event = (message, 0.0)
        
        handler._midi_callback(event)
        
        play_callback.assert_called_once()
    
    def test_midi_callback_note_off_ignored(self):
        """Test MIDI callback ignores Note Off messages (velocity = 0)."""
        handler = MIDIHandler()
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Simulate MIDI Note On with velocity 0 (Note Off)
        message = [144, 60, 0]
        event = (message, 0.0)
        
        handler._midi_callback(event)
        
        play_callback.assert_not_called()
    
    def test_midi_callback_control_change(self):
        """Test MIDI callback processes Control Change messages."""
        handler = MIDIHandler()
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Simulate MIDI CC message: [status, controller, value]
        # Status 176 = CC channel 1, controller 60, value 127
        message = [176, 60, 127]
        event = (message, 0.0)
        
        handler._midi_callback(event)
        
        play_callback.assert_called_once()
    
    def test_midi_callback_control_change_zero_value_ignored(self):
        """Test MIDI callback ignores CC messages with value 0."""
        handler = MIDIHandler()
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Simulate MIDI CC with value 0
        message = [176, 60, 0]
        event = (message, 0.0)
        
        handler._midi_callback(event)
        
        play_callback.assert_not_called()
    
    def test_midi_callback_invalid_message(self):
        """Test MIDI callback handles invalid messages gracefully."""
        handler = MIDIHandler()
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Simulate invalid message (too short)
        message = [144]
        event = (message, 0.0)
        
        # Should not raise exception
        handler._midi_callback(event)
        play_callback.assert_not_called()
    
    def test_callback_error_handling(self):
        """Test that callback errors are caught and logged."""
        handler = MIDIHandler()
        
        # Create callback that raises exception
        def failing_callback():
            raise Exception("Callback error")
        
        handler.on_play_command(failing_callback)
        
        # Should not raise exception
        handler._process_note(60)
    
    @patch('clicktrack.midi_handler.rtmidi.MidiIn')
    def test_close_connection(self, mock_midi_in_class):
        """Test closing MIDI connection."""
        mock_midi_in = MagicMock()
        mock_midi_in.get_ports.return_value = ['USB MIDI Device']
        mock_midi_in_class.return_value = mock_midi_in
        
        handler = MIDIHandler()
        handler.initialize()
        handler.close()
        
        mock_midi_in.close_port.assert_called_once()
        assert not handler.is_connected()
    
    def test_close_without_connection(self):
        """Test closing when no connection exists."""
        handler = MIDIHandler()
        
        # Should not raise exception
        handler.close()
        assert not handler.is_connected()
    
    def test_custom_mappings_work_correctly(self):
        """Test that custom MIDI mappings are respected."""
        custom_mappings = {
            'play': 36,
            'stop': 37,
            'next': 38,
            'previous': 39
        }
        handler = MIDIHandler(mappings=custom_mappings)
        
        play_callback = Mock()
        handler.on_play_command(play_callback)
        
        # Test custom play note (36)
        handler._process_note(36)
        play_callback.assert_called_once()
        
        # Test default play note (60) should not trigger
        play_callback.reset_mock()
        handler._process_note(60)
        play_callback.assert_not_called()
