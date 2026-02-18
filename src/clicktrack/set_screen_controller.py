"""
Set Screen Controller for the Click Track Player.

This module provides the controller for the Set Screen, coordinating between
the Set Manager and Playback Engine to manage navigation and playback control
during live performances.
"""

import logging
from typing import Optional

from clicktrack.models import Song, PlaybackState
from clicktrack.set_manager import SetManager
from clicktrack.song_manager import SongManager
from clicktrack.playback_engine import PlaybackEngine
from clicktrack.midi_handler import MIDIHandler

logger = logging.getLogger(__name__)


class SetScreenController:
    """
    Controller for the Set Screen that coordinates set navigation and playback.
    
    This controller acts as a facade between the Set Manager and Playback Engine,
    implementing navigation boundary logic and ensuring playback state consistency.
    It manages the current set, current song position, and playback controls.
    """
    
    def __init__(
        self,
        set_manager: SetManager,
        song_manager: SongManager,
        playback_engine: PlaybackEngine,
        midi_handler: Optional[MIDIHandler] = None
    ):
        """
        Initialize the Set Screen Controller.
        
        Args:
            set_manager: SetManager instance for set operations
            song_manager: SongManager instance for retrieving song data
            playback_engine: PlaybackEngine instance for audio playback
            midi_handler: Optional MIDIHandler instance for sending display info
        """
        self.set_manager = set_manager
        self.song_manager = song_manager
        self.playback_engine = playback_engine
        self.midi_handler = midi_handler
        
        # Initialize playback state
        self._playback_state = PlaybackState()
        
        logger.info("SetScreenController initialized")
    
    def set_midi_handler(self, midi_handler: Optional[MIDIHandler]):
        """Set or update the MIDI handler for display output."""
        self.midi_handler = midi_handler
    
    def _send_track_info_to_midi(self):
        """Send current track information to MIDI controller display."""
        if not self.midi_handler or not self._playback_state.current_set_id:
            return
        
        try:
            current_set = self.set_manager.get_set(self._playback_state.current_set_id)
            if current_set:
                track_number = self._playback_state.current_song_index + 1
                total_tracks = len(current_set.songs)
                
                # Get song title if available
                song_title = ""
                if 0 <= self._playback_state.current_song_index < len(current_set.songs):
                    song_id = current_set.songs[self._playback_state.current_song_index]
                    song = self.song_manager.get_song(song_id)
                    if song:
                        song_title = song.title
                
                self.midi_handler.send_track_info(track_number, total_tracks, song_title)
        except Exception as e:
            logger.warning(f"Error sending track info to MIDI: {e}")
    
    def load_set(self, set_id: str):
        """
        Load a set for playback.
        
        Args:
            set_id: ID of the set to load
            
        Raises:
            ValueError: If set not found
        """
        # Verify set exists
        current_set = self.set_manager.get_set(set_id)
        if not current_set:
            logger.error(f"Attempted to load non-existent set: {set_id}")
            raise ValueError(f"Set with ID {set_id} not found")
        
        # Stop any current playback
        if self._playback_state.is_playing:
            logger.info("Stopping current playback before loading new set")
            self.stop()
        
        # Update playback state
        self._playback_state.current_set_id = set_id
        self._playback_state.current_song_index = 0
        self._playback_state.is_playing = False
        self._playback_state.current_bpm = None
        
        logger.info(f"Loaded set: {current_set.name} (ID: {set_id}, {len(current_set.songs)} songs)")
        
        # Send track info to MIDI display
        self._send_track_info_to_midi()
    
    def next_song(self):
        """
        Navigate to the next song in the current set.
        
        If currently on the last song, remains on the last song.
        If playback is active, stops current song and starts playing the next song.
        If playback is stopped, just navigates without starting playback.
        
        Raises:
            RuntimeError: If no set is currently loaded
        """
        if self._playback_state.current_set_id is None:
            raise RuntimeError("No set is currently loaded")
        
        # Get current set
        current_set = self.set_manager.get_set(self._playback_state.current_set_id)
        if not current_set:
            raise RuntimeError("Current set not found")
        
        logger.info(
            f"next_song() called - Current index: {self._playback_state.current_song_index}, "
            f"Set has {len(current_set.songs)} songs, Playing: {self._playback_state.is_playing}"
        )
        
        # Remember if we were playing
        was_playing = self._playback_state.is_playing
        
        # Stop playback if active
        if was_playing:
            self.stop()
        
        # Check if we can advance
        if self._playback_state.current_song_index < len(current_set.songs) - 1:
            old_index = self._playback_state.current_song_index
            self._playback_state.current_song_index += 1
            logger.info(
                f"Advanced to next song: index {old_index} -> {self._playback_state.current_song_index}"
            )
            
            # If we were playing, start playing the new song
            if was_playing:
                logger.info("Auto-starting playback of next song")
                self.play()
            
            # Send track info to MIDI display
            self._send_track_info_to_midi()
        else:
            logger.debug("Already on last song, staying on current song")
    
    def previous_song(self):
        """
        Navigate to the previous song in the current set.
        
        If currently on the first song, remains on the first song.
        If playback is active, stops current song and starts playing the previous song.
        If playback is stopped, just navigates without starting playback.
        
        Raises:
            RuntimeError: If no set is currently loaded
        """
        if self._playback_state.current_set_id is None:
            raise RuntimeError("No set is currently loaded")
        
        # Get current set
        current_set = self.set_manager.get_set(self._playback_state.current_set_id)
        if not current_set:
            raise RuntimeError("Current set not found")
        
        logger.info(
            f"previous_song() called - Current index: {self._playback_state.current_song_index}, "
            f"Set has {len(current_set.songs)} songs, Playing: {self._playback_state.is_playing}"
        )
        
        # Remember if we were playing
        was_playing = self._playback_state.is_playing
        
        # Stop playback if active
        if was_playing:
            self.stop()
        
        # Check if we can go back
        if self._playback_state.current_song_index > 0:
            old_index = self._playback_state.current_song_index
            self._playback_state.current_song_index -= 1
            logger.info(
                f"Moved to previous song: index {old_index} -> {self._playback_state.current_song_index}"
            )
            
            # If we were playing, start playing the new song
            if was_playing:
                logger.info("Auto-starting playback of previous song")
                self.play()
            
            # Send track info to MIDI display
            self._send_track_info_to_midi()
        else:
            logger.debug("Already on first song, staying on current song")
    
    def jump_to_song(self, song_index: int):
        """
        Jump to a specific song in the current set by index.
        
        If playback is active, stops the current playback.
        User must press Play to start the new song.
        
        Args:
            song_index: Zero-based index of the song to jump to
            
        Raises:
            RuntimeError: If no set is currently loaded
            ValueError: If song_index is out of bounds
        """
        if self._playback_state.current_set_id is None:
            raise RuntimeError("No set is currently loaded")
        
        # Get current set
        current_set = self.set_manager.get_set(self._playback_state.current_set_id)
        if not current_set:
            raise RuntimeError("Current set not found")
        
        # Validate index
        if song_index < 0 or song_index >= len(current_set.songs):
            raise ValueError(
                f"Song index {song_index} out of bounds (set has {len(current_set.songs)} songs)"
            )
        
        logger.info(
            f"jump_to_song() called - Current index: {self._playback_state.current_song_index}, "
            f"Target index: {song_index}, Playing: {self._playback_state.is_playing}"
        )
        
        # Stop playback if active
        if self._playback_state.is_playing:
            self.stop()
        
        # Jump to the song
        old_index = self._playback_state.current_song_index
        self._playback_state.current_song_index = song_index
        logger.info(f"Jumped to song: index {old_index} -> {song_index}")
        
        # Send track info to MIDI display
        self._send_track_info_to_midi()
    
    def play(self):
        """
        Start playback of the currently selected song.
        
        Raises:
            RuntimeError: If no set is loaded or set is empty
            ValueError: If current song not found
        """
        if self._playback_state.current_set_id is None:
            logger.warning("Attempted to play without a loaded set")
            raise RuntimeError("No set is currently loaded")
        
        # Get current set
        current_set = self.set_manager.get_set(self._playback_state.current_set_id)
        if not current_set:
            logger.error(f"Current set not found: {self._playback_state.current_set_id}")
            raise RuntimeError("Current set not found")
        
        # Check if set has songs
        if not current_set.songs:
            logger.warning(f"Attempted to play empty set: {current_set.name}")
            raise RuntimeError("Current set is empty")
        
        # Check if index is valid
        if self._playback_state.current_song_index >= len(current_set.songs):
            logger.error(
                f"Song index out of bounds: {self._playback_state.current_song_index} "
                f"(set has {len(current_set.songs)} songs)"
            )
            raise RuntimeError("Current song index is out of bounds")
        
        # Get current song
        song_id = current_set.songs[self._playback_state.current_song_index]
        song = self.song_manager.get_song(song_id)
        
        if not song:
            logger.error(f"Song not found: {song_id}")
            raise ValueError(f"Song with ID {song_id} not found")
        
        # Start playback
        try:
            self.playback_engine.start_playback(song)
            
            # Update playback state
            self._playback_state.is_playing = True
            self._playback_state.current_bpm = song.bpm
            
            logger.info(
                f"Started playback: {song.title} at {song.bpm} BPM "
                f"(song {self._playback_state.current_song_index + 1}/{len(current_set.songs)})"
            )
        except Exception as e:
            logger.error(f"Failed to start playback: {e}", exc_info=True)
            raise
    
    def stop(self):
        """
        Stop the currently playing click track.
        
        This method is safe to call even if nothing is playing.
        """
        try:
            if self._playback_state.is_playing:
                self.playback_engine.stop_playback()
                
                # Update playback state
                self._playback_state.is_playing = False
                self._playback_state.current_bpm = None
                
                logger.info("Stopped playback")
        except Exception as e:
            # Always update state even if stop fails
            self._playback_state.is_playing = False
            self._playback_state.current_bpm = None
            logger.error(f"Error stopping playback: {e}", exc_info=True)
    
    def get_current_song(self) -> Optional[Song]:
        """
        Get the currently selected song.
        
        Returns:
            Song object if a set is loaded and has songs, None otherwise
        """
        if self._playback_state.current_set_id is None:
            return None
        
        # Get current set
        current_set = self.set_manager.get_set(self._playback_state.current_set_id)
        if not current_set or not current_set.songs:
            return None
        
        # Check if index is valid
        if self._playback_state.current_song_index >= len(current_set.songs):
            return None
        
        # Get current song
        song_id = current_set.songs[self._playback_state.current_song_index]
        return self.song_manager.get_song(song_id)
    
    def get_playback_state(self) -> PlaybackState:
        """
        Get the current playback state.
        
        Returns:
            PlaybackState object with current state information
        """
        return self._playback_state
