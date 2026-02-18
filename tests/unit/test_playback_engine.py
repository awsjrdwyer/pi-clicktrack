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
        subdivision="quarter",
        accent_pattern=[True, False, False, False],
        click_sound="wood_block",
        volume=80
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
        # The engine should have loaded the sounds
        assert len(playback_engine._click_sounds) > 0


class TestPlaybackControl:
    """Test playback control methods."""
    
    def test_start_playback(self, playback_engine, sample_song):
        """Test starting playback."""
        playback_engine.start_playback(sample_song)
        
        assert playback_engine.is_playing()
        assert playback_engine.get_current_bpm() == 120
        
        # Clean up
        playback_engine.stop_playback()
    
    def test_stop_playback(self, playback_engine, sample_song):
        """Test stopping playback."""
        playback_engine.start_playback(sample_song)
        assert playback_engine.is_playing()
        
        playback_engine.stop_playback()
        
        assert not playback_engine.is_playing()
        assert playback_engine.get_current_bpm() is None
    
    def test_cannot_start_playback_twice(self, playback_engine, sample_song):
        """Test that starting playback twice raises an error."""
        playback_engine.start_playback(sample_song)
        
        with pytest.raises(RuntimeError, match="already active"):
            playback_engine.start_playback(sample_song)
        
        # Clean up
        playback_engine.stop_playback()
    
    def test_stop_when_not_playing_is_safe(self, playback_engine):
        """Test that stopping when not playing doesn't raise an error."""
        assert not playback_engine.is_playing()
        playback_engine.stop_playback()  # Should not raise
        assert not playback_engine.is_playing()


class TestVolumeControl:
    """Test volume control functionality."""
    
    def test_set_volume_valid(self, playback_engine):
        """Test setting volume to valid values."""
        playback_engine.set_volume(50)
        assert playback_engine._volume == 50
        
        playback_engine.set_volume(0)
        assert playback_engine._volume == 0
        
        playback_engine.set_volume(100)
        assert playback_engine._volume == 100
    
    def test_set_volume_invalid(self, playback_engine):
        """Test that invalid volume values raise errors."""
        with pytest.raises(ValueError, match="Volume must be between 0 and 100"):
            playback_engine.set_volume(-1)
        
        with pytest.raises(ValueError, match="Volume must be between 0 and 100"):
            playback_engine.set_volume(101)


class TestClickSoundLoading:
    """Test click sound loading functionality."""
    
    def test_load_click_sound_valid(self, playback_engine):
        """Test loading a valid click sound."""
        playback_engine.load_click_sound("beep")
        assert "beep" in playback_engine._click_sounds
    
    def test_load_click_sound_invalid(self, playback_engine):
        """Test that loading an invalid sound raises an error."""
        with pytest.raises(ValueError, match="Unsupported click sound"):
            playback_engine.load_click_sound("invalid_sound")


class TestPlaybackTiming:
    """Test playback timing functionality."""
    
    def test_playback_runs_for_expected_duration(self, playback_engine, sample_song):
        """Test that playback runs and can be stopped."""
        playback_engine.start_playback(sample_song)
        
        # Let it play for a short time
        time.sleep(0.5)
        
        assert playback_engine.is_playing()
        
        playback_engine.stop_playback()
        
        assert not playback_engine.is_playing()
    
    def test_different_subdivisions(self, playback_engine):
        """Test playback with different subdivisions."""
        # Quarter note subdivision
        song_quarter = Song(
            title="Quarter Test",
            bpm=120,
            time_signature=TimeSignature(4, 4),
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=80
        )
        
        playback_engine.start_playback(song_quarter)
        time.sleep(0.3)
        playback_engine.stop_playback()
        
        # Eighth note subdivision
        song_eighth = Song(
            title="Eighth Test",
            bpm=120,
            time_signature=TimeSignature(4, 4),
            subdivision="eighth",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=80
        )
        
        playback_engine.start_playback(song_eighth)
        time.sleep(0.3)
        playback_engine.stop_playback()
        
        # Both should complete without errors
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
                subdivision="quarter",
                accent_pattern=pattern,
                click_sound="wood_block",
                volume=80
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
                subdivision="quarter",
                accent_pattern=[True, False, False, False],
                click_sound=sound,
                volume=80
            )
            
            playback_engine.start_playback(song)
            time.sleep(0.2)
            playback_engine.stop_playback()
            
            assert not playback_engine.is_playing()
