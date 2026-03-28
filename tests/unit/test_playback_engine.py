"""
Unit tests for the PlaybackEngine.

These tests verify the basic functionality of the playback engine including
initialization, playback control, and state management.
"""

import pytest
import time
from pathlib import Path
from clicktrack.playback_engine import PlaybackEngine
from clicktrack.models import Song, TimeSignature


@pytest.fixture
def sounds_dir():
    """Get the path to the sounds directory."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "assets" / "sounds"


@pytest.fixture
def playback_engine(sounds_dir):
    """Create a PlaybackEngine instance for testing."""
    return PlaybackEngine(sounds_dir=str(sounds_dir))


@pytest.fixture
def sample_song():
    """Create a sample song for testing."""
    return Song(
        title="Test Song",
        bpm=120,
        time_signature=TimeSignature(4, 4),
        subdivision="single",
        accent_pattern=[True, False, False, False],
        click_sound="wood_block"
    )


class TestPlaybackEngineInitialization:
    """Test PlaybackEngine initialization."""
    
    def test_engine_initializes_successfully(self, playback_engine):
        """Test that the engine initializes without errors."""
        assert playback_engine is not None
        assert not playback_engine.is_playing()
        assert playback_engine.get_current_bpm() is None
    
    def test_engine_loads_click_sounds(self, playback_engine):
        """Test that click sounds are loaded during initialization."""
        assert len(playback_engine._click_sound_paths) > 0


class TestPlaybackControl:
    """Test playback control methods."""
    
    def test_start_playback(self, playback_engine, sample_song):
        """Test starting playback."""
        playback_engine.start_playback(sample_song)
        
        assert playback_engine.is_playing()
        assert playback_engine.get_current_bpm() == 120
        
        playback_engine.stop_playback()
    
    def test_stop_playback(self, playback_engine, sample_song):
        """Test stopping playback."""
        playback_engine.start_playback(sample_song)
        assert playback_engine.is_playing()
        
        playback_engine.stop_playback()
        
        assert not playback_engine.is_playing()
        assert playback_engine.get_current_bpm() is None
    
    def test_start_playback_twice_auto_stops_first(self, playback_engine, sample_song):
        """Test that starting playback twice auto-stops the first."""
        playback_engine.start_playback(sample_song)
        assert playback_engine.is_playing()
        
        # Starting again should auto-stop and restart (no error)
        playback_engine.start_playback(sample_song)
        assert playback_engine.is_playing()
        
        playback_engine.stop_playback()
    
    def test_stop_when_not_playing_is_safe(self, playback_engine):
        """Test that stopping when not playing doesn't raise an error."""
        assert not playback_engine.is_playing()
        playback_engine.stop_playback()
        assert not playback_engine.is_playing()


class TestClickSoundLoading:
    """Test click sound loading functionality."""
    
    def test_load_click_sound_valid(self, playback_engine):
        """Test loading a valid click sound."""
        playback_engine.load_click_sound("beep")
        assert "beep" in playback_engine._click_sound_paths
    
    def test_load_click_sound_invalid(self, playback_engine):
        """Test that loading an invalid sound raises an error."""
        with pytest.raises(ValueError, match="Unsupported click sound"):
            playback_engine.load_click_sound("invalid_sound")


class TestPlaybackTiming:
    """Test playback timing functionality."""
    
    def test_playback_runs_for_expected_duration(self, playback_engine, sample_song):
        """Test that playback runs and can be stopped."""
        playback_engine.start_playback(sample_song)
        
        time.sleep(0.5)
        assert playback_engine.is_playing()
        
        playback_engine.stop_playback()
        assert not playback_engine.is_playing()
    
    def test_different_subdivisions(self, playback_engine):
        """Test playback with different subdivisions."""
        song_single = Song(
            title="Single Test",
            bpm=120,
            time_signature=TimeSignature(4, 4),
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block"
        )
        
        playback_engine.start_playback(song_single)
        time.sleep(0.3)
        playback_engine.stop_playback()
        
        song_double = Song(
            title="Double Test",
            bpm=120,
            time_signature=TimeSignature(4, 4),
            subdivision="double",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block"
        )
        
        playback_engine.start_playback(song_double)
        time.sleep(0.3)
        playback_engine.stop_playback()
        
        assert not playback_engine.is_playing()
    
    def test_different_time_signatures(self, playback_engine):
        """Test playback with different time signatures."""
        time_signatures = [
            (3, 4, [True, False, False]),
            (6, 8, [True, False, False, False, False, False]),
            (5, 4, [True, False, False, False, False])
        ]
        
        for beats, note_value, pattern in time_signatures:
            song = Song(
                title=f"Test {beats}/{note_value}",
                bpm=120,
                time_signature=TimeSignature(beats, note_value),
                subdivision="single",
                accent_pattern=pattern,
                click_sound="wood_block"
            )
            
            playback_engine.start_playback(song)
            time.sleep(0.2)
            playback_engine.stop_playback()
            
            assert not playback_engine.is_playing()


class TestClickSounds:
    """Test different click sounds."""
    
    def test_all_click_sounds(self, playback_engine):
        """Test playback with all available click sounds."""
        click_sounds = ["wood_block", "beep", "cowbell"]
        
        for sound in click_sounds:
            song = Song(
                title=f"Test {sound}",
                bpm=120,
                time_signature=TimeSignature(4, 4),
                subdivision="single",
                accent_pattern=[True, False, False, False],
                click_sound=sound
            )
            
            playback_engine.start_playback(song)
            time.sleep(0.2)
            playback_engine.stop_playback()
            
            assert not playback_engine.is_playing()
