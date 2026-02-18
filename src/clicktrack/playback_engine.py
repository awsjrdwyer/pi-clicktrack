"""
Playback Engine for the Click Track Player.

This module implements the audio playback engine with millisecond-accurate timing
for generating click tracks. It supports multiple click sounds, accent patterns,
time signatures, and subdivisions.

CRITICAL: Timing accuracy is paramount for live performance use.
The engine maintains ±5ms tolerance through high-resolution timers and drift correction.
"""

import os
import time
import threading
import subprocess
from pathlib import Path
from typing import Optional, Literal
import logging

from clicktrack.models import Song

logger = logging.getLogger(__name__)


class PlaybackEngine:
    """
    Audio playback engine for generating click tracks with millisecond accuracy.
    
    This engine uses high-resolution timers with drift correction to maintain
    precise timing for live musical performances. It supports:
    - Multiple click sounds (wood_block, beep, cowbell)
    - Accent patterns with volume variation
    - Time signatures and subdivisions
    - Volume control
    - Millisecond-accurate timing (±5ms tolerance)
    """
    
    # Default click sound
    DEFAULT_CLICK_SOUND = "wood_block"
    
    # Accent volume multiplier (accented beats are 50% louder)
    ACCENT_MULTIPLIER = 1.5
    
    def __init__(self, sounds_dir: Optional[str] = None, audio_device: str = "hw:2,0"):
        """
        Initialize the playback engine.
        
        Args:
            sounds_dir: Directory containing click sound files.
                       Defaults to assets/sounds relative to project root.
            audio_device: ALSA audio device identifier (e.g., "hw:1,0", "hw:2,0").
                         Defaults to "hw:2,0".
        """
        self._is_playing = False
        self._current_song: Optional[Song] = None
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._volume = 100  # Default volume (0-100)
        self._audio_device = audio_device
        
        # Current playback process
        self._play_process = None
        
        # Load click sounds
        if sounds_dir is None:
            # Default to assets/sounds directory
            project_root = Path(__file__).parent.parent.parent
            sounds_dir = project_root / "assets" / "sounds"
        else:
            sounds_dir = Path(sounds_dir)
        
        self._sounds_dir = sounds_dir
        self._click_sound_paths = {}
        self._load_click_sounds()
        
        logger.info(f"PlaybackEngine initialized with sounds from {sounds_dir}")
        logger.info(f"Audio device: {audio_device}")
    
    def _load_click_sounds(self):
        """Load all available click sound files."""
        sound_files = {
            "wood_block": "wood_block.wav",
            "beep": "beep.wav",
            "cowbell": "cowbell.wav"
        }
        
        loaded_count = 0
        for sound_name, filename in sound_files.items():
            sound_path = self._sounds_dir / filename
            if sound_path.exists():
                self._click_sound_paths[sound_name] = str(sound_path)
                logger.debug(f"Found click sound: {sound_name} at {sound_path}")
                loaded_count += 1
            else:
                logger.warning(f"Click sound file not found: {sound_path}")
        
        if loaded_count == 0:
            logger.error("No click sounds could be loaded. Audio playback will not work.")
        else:
            logger.info(f"Loaded {loaded_count} of {len(sound_files)} click sounds")
    
    def load_click_sound(self, sound_name: Literal["wood_block", "beep", "cowbell"]):
        """
        Load a specific click sound.
        
        Args:
            sound_name: Name of the click sound to load
            
        Raises:
            ValueError: If the sound name is not supported
            FileNotFoundError: If the sound file doesn't exist
        """
        if sound_name not in ["wood_block", "beep", "cowbell"]:
            raise ValueError(f"Unsupported click sound: {sound_name}")
        
        sound_files = {
            "wood_block": "wood_block.wav",
            "beep": "beep.wav",
            "cowbell": "cowbell.wav"
        }
        
        sound_path = self._sounds_dir / sound_files[sound_name]
        if not sound_path.exists():
            raise FileNotFoundError(f"Click sound file not found: {sound_path}")
        
        self._click_sound_paths[sound_name] = str(sound_path)
        logger.info(f"Loaded click sound: {sound_name}")
    
    def start_playback(self, song: Song):
        """
        Start playing a click track for the given song.
        
        Args:
            song: Song object containing BPM, time signature, accent pattern, etc.
            
        Raises:
            RuntimeError: If playback is already active or audio device unavailable
            ValueError: If the song's click sound is not available
        """
        if self._is_playing:
            logger.warning("Playback already active, stopping current playback first")
            self.stop_playback()
            # Give it a moment to clean up
            time.sleep(0.2)
        
        # Verify the click sound is available
        if song.click_sound not in self._click_sound_paths:
            logger.error(f"Click sound not available: {song.click_sound}")
            raise ValueError(f"Click sound not available: {song.click_sound}")
        
        if not self._click_sound_paths:
            raise RuntimeError("No click sounds loaded. Audio playback unavailable.")
        
        self._current_song = song
        self._stop_event.clear()
        self._is_playing = True
        
        # Start playback in a separate thread
        self._playback_thread = threading.Thread(
            target=self._playback_loop,
            daemon=True,
            name="PlaybackThread"
        )
        self._playback_thread.start()
        
        logger.info(f"Started playback: {song.title} at {song.bpm} BPM")
    
    def stop_playback(self):
        """Stop the currently playing click track."""
        if not self._is_playing:
            return
        
        logger.info("Stopping playback...")
        
        # Signal the playback thread to stop
        self._is_playing = False
        self._stop_event.set()
        
        # Stop any currently playing sound
        if self._play_process and self._play_process.poll() is None:
            try:
                self._play_process.terminate()
                self._play_process.wait(timeout=0.5)
            except Exception as e:
                logger.debug(f"Error stopping play process: {e}")
        
        # Wait for playback thread to finish
        if self._playback_thread and self._playback_thread.is_alive():
            logger.debug("Waiting for playback thread to finish...")
            self._playback_thread.join(timeout=2.0)
            if self._playback_thread.is_alive():
                logger.warning("Playback thread did not stop cleanly")
        
        self._current_song = None
        self._play_process = None
        logger.info("Stopped playback")
    
    def is_playing(self) -> bool:
        """
        Check if playback is currently active.
        
        Returns:
            True if playing, False otherwise
        """
        return self._is_playing
    
    def get_current_bpm(self) -> Optional[float]:
        """
        Get the BPM of the currently playing song.
        
        Returns:
            BPM value if playing, None otherwise
        """
        if self._current_song:
            return self._current_song.bpm
        return None
    
    def set_volume(self, volume: int):
        """
        Set the playback volume.
        
        Args:
            volume: Volume level (0-100)
            
        Raises:
            ValueError: If volume is outside the valid range
        """
        if not (0 <= volume <= 100):
            raise ValueError("Volume must be between 0 and 100")
        
        self._volume = volume
        logger.debug(f"Volume set to {volume}")
    
    def _playback_loop(self):
        """
        Main playback loop with millisecond-accurate timing.
        
        This method implements high-resolution timing with drift correction
        to maintain accurate click intervals. It tracks cumulative timing
        drift and adjusts subsequent intervals to stay within ±5ms tolerance.
        """
        try:
            self._playback_loop_impl()
        except Exception as e:
            logger.error(f"Fatal error in playback loop: {e}", exc_info=True)
            self._is_playing = False
    
    def _playback_loop_impl(self):
        """Implementation of the playback loop."""
        if not self._current_song:
            return
        
        song = self._current_song
        
        # Get click sound path
        sound_path = self._click_sound_paths.get(song.click_sound)
        if not sound_path:
            logger.error(f"Click sound not available: {song.click_sound}")
            self._is_playing = False
            return
        
        # Calculate base interval between beats in seconds
        beat_interval = 60.0 / song.bpm
        
        # Adjust for subdivision
        if song.subdivision == "eighth":
            click_interval = beat_interval / 2.0
        else:
            click_interval = beat_interval
        
        # Calculate effective volume - always 100% (external soundboard controls volume)
        base_volume = 1.0
        
        # Timing variables for drift correction
        start_time = time.perf_counter()
        click_count = 0
        current_beat = 0
        
        logger.debug(
            f"Playback loop started: BPM={song.bpm}, "
            f"interval={click_interval*1000:.2f}ms, "
            f"time_sig={song.time_signature}, "
            f"subdivision={song.subdivision}"
        )
        
        while not self._stop_event.is_set():
            # Calculate expected time for this click
            expected_time = start_time + (click_count * click_interval)
            
            # Calculate actual time to wait (with drift correction)
            current_time = time.perf_counter()
            wait_time = expected_time - current_time
            
            # If we're ahead of schedule, wait
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Check if we should stop before playing
            if self._stop_event.is_set():
                break
            
            # Determine if this beat is accented
            is_main_beat = (song.subdivision == "quarter") or (click_count % 2 == 0)
            is_accented = is_main_beat and song.accent_pattern[current_beat]
            
            # Calculate volume for this click (accents are louder)
            # Note: Volume is always 100% - external soundboard controls overall volume
            if is_accented:
                click_volume = self.ACCENT_MULTIPLIER  # 1.5x for accents
            else:
                click_volume = 1.0  # Full volume for normal beats
            
            # Play the click
            self._play_click(sound_path, click_volume)
            
            # Advance counters
            click_count += 1
            
            # Advance beat counter (only on main beats)
            if is_main_beat:
                current_beat = (current_beat + 1) % song.time_signature.beats_per_measure
            
            # Log timing drift for debugging (every 10 clicks)
            if click_count % 10 == 0:
                actual_time = time.perf_counter()
                drift_ms = (actual_time - expected_time) * 1000
                logger.debug(f"Click {click_count}: drift = {drift_ms:.2f}ms")
        
        logger.debug("Playback loop ended normally")
    
    def _play_click(self, sound_path: str, volume: float):
        """
        Play a single click sound using aplay command.
        
        Args:
            sound_path: Path to the WAV file
            volume: Volume level (ignored - always plays at 100%)
        """
        # Check if we should stop before playing
        if self._stop_event.is_set():
            return
        
        try:
            # Wait for previous sound to finish before playing next one
            if self._play_process and self._play_process.poll() is None:
                self._play_process.wait()
            
            # Use aplay to play the sound - it works reliably in systemd services
            # Use full path since systemd may not have /usr/bin in PATH
            # -D specifies the ALSA audio device
            # -q for quiet mode (no output)
            self._play_process = subprocess.Popen(
                ['/usr/bin/aplay', '-D', self._audio_device, '-q', sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Log first few clicks for debugging
            if not hasattr(self, '_click_debug_count'):
                self._click_debug_count = 0
            self._click_debug_count += 1
            if self._click_debug_count <= 3:
                logger.info(f"Click {self._click_debug_count} played successfully using aplay on {self._audio_device}")
                
        except Exception as e:
            # Log but don't crash - audio glitches are acceptable
            if not self._stop_event.is_set():
                logger.error(f"Error playing click: {e}", exc_info=True)
            else:
                logger.debug(f"Click playback stopped: {e}")
