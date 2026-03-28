"""
Unit tests for the Set Screen Controller.

These tests verify the navigation and playback control logic of the
SetScreenController, including boundary conditions and state management.
"""

import pytest
from unittest.mock import Mock, MagicMock

from clicktrack.models import Song, Set, PlaybackState, TimeSignature
from clicktrack.set_screen_controller import SetScreenController


@pytest.fixture
def mock_set_manager():
    """Create a mock SetManager."""
    return Mock()


@pytest.fixture
def mock_song_manager():
    """Create a mock SongManager."""
    return Mock()


@pytest.fixture
def mock_playback_engine():
    """Create a mock PlaybackEngine."""
    engine = Mock()
    engine.is_playing.return_value = False
    return engine


@pytest.fixture
def controller(mock_set_manager, mock_song_manager, mock_playback_engine):
    """Create a SetScreenController with mocked dependencies."""
    return SetScreenController(
        mock_set_manager,
        mock_song_manager,
        mock_playback_engine,
        storage_manager=None
    )


@pytest.fixture
def sample_song():
    """Create a sample song for testing."""
    return Song(
        id="song-1",
        title="Test Song",
        bpm=120.0,
        time_signature=TimeSignature(4, 4),
        subdivision="single",
        accent_pattern=[True, False, False, False],
        click_sound="wood_block"
    )


@pytest.fixture
def sample_set():
    """Create a sample set for testing."""
    return Set(
        id="set-1",
        name="Test Set",
        songs=["song-1", "song-2", "song-3"]
    )


class TestLoadSet:
    """Tests for loading a set."""
    
    def test_load_set_success(self, controller, mock_set_manager, sample_set):
        """Test successfully loading a set."""
        mock_set_manager.get_set.return_value = sample_set
        
        controller.load_set("set-1")
        
        # Verify set was retrieved
        mock_set_manager.get_set.assert_called_once_with("set-1")
        
        # Verify playback state was updated
        state = controller.get_playback_state()
        assert state.current_set_id == "set-1"
        assert state.current_song_index == 0
        assert state.is_playing is False
        assert state.current_bpm is None
    
    def test_load_set_not_found(self, controller, mock_set_manager):
        """Test loading a non-existent set raises ValueError."""
        mock_set_manager.get_set.return_value = None
        
        with pytest.raises(ValueError, match="Set with ID set-999 not found"):
            controller.load_set("set-999")
    
    def test_load_set_stops_playback(self, controller, mock_set_manager, mock_playback_engine, sample_set):
        """Test that loading a new set stops current playback."""
        mock_set_manager.get_set.return_value = sample_set
        
        # Simulate active playback
        controller._playback_state.is_playing = True
        controller._playback_state.current_set_id = "old-set"
        
        controller.load_set("set-1")
        
        # Verify playback was stopped
        mock_playback_engine.stop_playback.assert_called_once()
        assert controller._playback_state.is_playing is False


class TestNextSong:
    """Tests for navigating to the next song."""
    
    def test_next_song_advances_index(self, controller, mock_set_manager, sample_set):
        """Test that next_song advances the song index."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0
        
        controller.next_song()
        
        assert controller._playback_state.current_song_index == 1
    
    def test_next_song_on_last_song_stays(self, controller, mock_set_manager, sample_set):
        """Test that next_song on the last song stays on last song."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 2  # Last song (index 2 of 3 songs)
        
        controller.next_song()
        
        # Should stay on index 2
        assert controller._playback_state.current_song_index == 2
    
    def test_next_song_auto_plays_when_playing(self, controller, mock_set_manager, mock_playback_engine, mock_song_manager, sample_set):
        """Test that next_song auto-plays the new song if currently playing."""
        mock_set_manager.get_set.return_value = sample_set
        mock_song_manager.get_song.return_value = Mock()
        mock_playback_engine.is_playing.return_value = True
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0
        controller._playback_state.is_playing = True
        
        controller.next_song()
        
        # Verify playback was stopped then restarted
        mock_playback_engine.stop_playback.assert_called()
        assert controller._playback_state.is_playing is True
    
    def test_next_song_no_set_loaded(self, controller):
        """Test that next_song raises error when no set is loaded."""
        with pytest.raises(RuntimeError, match="No set is currently loaded"):
            controller.next_song()


class TestPreviousSong:
    """Tests for navigating to the previous song."""
    
    def test_previous_song_decreases_index(self, controller, mock_set_manager, sample_set):
        """Test that previous_song decreases the song index."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 1
        
        controller.previous_song()
        
        assert controller._playback_state.current_song_index == 0
    
    def test_previous_song_on_first_song_stays(self, controller, mock_set_manager, sample_set):
        """Test that previous_song on the first song stays on first song."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0  # First song
        
        controller.previous_song()
        
        # Should stay on index 0
        assert controller._playback_state.current_song_index == 0
    
    def test_previous_song_auto_plays_when_playing(self, controller, mock_set_manager, mock_playback_engine, mock_song_manager, sample_set):
        """Test that previous_song auto-plays the new song if currently playing."""
        mock_set_manager.get_set.return_value = sample_set
        mock_song_manager.get_song.return_value = Mock()
        mock_playback_engine.is_playing.return_value = True
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 1
        controller._playback_state.is_playing = True
        
        controller.previous_song()
        
        # Verify playback was stopped then restarted
        mock_playback_engine.stop_playback.assert_called()
        assert controller._playback_state.is_playing is True
    
    def test_previous_song_no_set_loaded(self, controller):
        """Test that previous_song raises error when no set is loaded."""
        with pytest.raises(RuntimeError, match="No set is currently loaded"):
            controller.previous_song()


class TestPlay:
    """Tests for starting playback."""
    
    def test_play_starts_playback(self, controller, mock_set_manager, mock_song_manager, mock_playback_engine, sample_set, sample_song):
        """Test that play starts playback with the current song."""
        mock_set_manager.get_set.return_value = sample_set
        mock_song_manager.get_song.return_value = sample_song
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0
        
        controller.play()
        
        # Verify song was retrieved
        mock_song_manager.get_song.assert_called_once_with("song-1")
        
        # Verify playback was started
        mock_playback_engine.start_playback.assert_called_once_with(sample_song)
        
        # Verify playback state was updated
        assert controller._playback_state.is_playing is True
        assert controller._playback_state.current_bpm == 120.0
    
    def test_play_no_set_loaded(self, controller):
        """Test that play raises error when no set is loaded."""
        with pytest.raises(RuntimeError, match="No set is currently loaded"):
            controller.play()
    
    def test_play_empty_set(self, controller, mock_set_manager):
        """Test that play raises error when set is empty."""
        empty_set = Set(id="set-1", name="Empty Set", songs=[])
        mock_set_manager.get_set.return_value = empty_set
        controller._playback_state.current_set_id = "set-1"
        
        with pytest.raises(RuntimeError, match="Current set is empty"):
            controller.play()
    
    def test_play_song_not_found(self, controller, mock_set_manager, mock_song_manager, sample_set):
        """Test that play raises error when song is not found."""
        mock_set_manager.get_set.return_value = sample_set
        mock_song_manager.get_song.return_value = None
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0
        
        with pytest.raises(ValueError, match="Song with ID song-1 not found"):
            controller.play()


class TestStop:
    """Tests for stopping playback."""
    
    def test_stop_stops_playback(self, controller, mock_playback_engine):
        """Test that stop stops the playback engine."""
        controller._playback_state.is_playing = True
        controller._playback_state.current_bpm = 120.0
        
        controller.stop()
        
        # Verify playback was stopped
        mock_playback_engine.stop_playback.assert_called_once()
        
        # Verify playback state was updated
        assert controller._playback_state.is_playing is False
        assert controller._playback_state.current_bpm is None
    
    def test_stop_when_not_playing(self, controller, mock_playback_engine):
        """Test that stop is safe to call when not playing."""
        controller._playback_state.is_playing = False
        
        controller.stop()
        
        # Should not call playback engine
        mock_playback_engine.stop_playback.assert_not_called()


class TestGetCurrentSong:
    """Tests for getting the current song."""
    
    def test_get_current_song_success(self, controller, mock_set_manager, mock_song_manager, sample_set, sample_song):
        """Test getting the current song."""
        mock_set_manager.get_set.return_value = sample_set
        mock_song_manager.get_song.return_value = sample_song
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0
        
        song = controller.get_current_song()
        
        assert song == sample_song
        mock_song_manager.get_song.assert_called_once_with("song-1")
    
    def test_get_current_song_no_set_loaded(self, controller):
        """Test getting current song when no set is loaded."""
        song = controller.get_current_song()
        assert song is None
    
    def test_get_current_song_empty_set(self, controller, mock_set_manager):
        """Test getting current song when set is empty."""
        empty_set = Set(id="set-1", name="Empty Set", songs=[])
        mock_set_manager.get_set.return_value = empty_set
        controller._playback_state.current_set_id = "set-1"
        
        song = controller.get_current_song()
        assert song is None
    
    def test_get_current_song_invalid_index(self, controller, mock_set_manager, sample_set):
        """Test getting current song when index is out of bounds."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 999  # Out of bounds
        
        song = controller.get_current_song()
        assert song is None


class TestGetPlaybackState:
    """Tests for getting playback state."""
    
    def test_get_playback_state(self, controller):
        """Test getting the playback state."""
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 2
        controller._playback_state.is_playing = True
        controller._playback_state.current_bpm = 140.0
        
        state = controller.get_playback_state()
        
        assert state.current_set_id == "set-1"
        assert state.current_song_index == 2
        assert state.is_playing is True
        assert state.current_bpm == 140.0


class TestNavigationBoundaries:
    """Tests for navigation boundary conditions."""
    
    def test_multiple_next_calls_at_end(self, controller, mock_set_manager, sample_set):
        """Test multiple next_song calls when at the end of the set."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 2  # Last song
        
        # Call next multiple times
        controller.next_song()
        controller.next_song()
        controller.next_song()
        
        # Should still be on last song
        assert controller._playback_state.current_song_index == 2
    
    def test_multiple_previous_calls_at_start(self, controller, mock_set_manager, sample_set):
        """Test multiple previous_song calls when at the start of the set."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0  # First song
        
        # Call previous multiple times
        controller.previous_song()
        controller.previous_song()
        controller.previous_song()
        
        # Should still be on first song
        assert controller._playback_state.current_song_index == 0
    
    def test_navigate_through_entire_set(self, controller, mock_set_manager, sample_set):
        """Test navigating through the entire set."""
        mock_set_manager.get_set.return_value = sample_set
        controller._playback_state.current_set_id = "set-1"
        controller._playback_state.current_song_index = 0
        
        # Navigate forward through all songs
        assert controller._playback_state.current_song_index == 0
        controller.next_song()
        assert controller._playback_state.current_song_index == 1
        controller.next_song()
        assert controller._playback_state.current_song_index == 2
        
        # Navigate backward through all songs
        controller.previous_song()
        assert controller._playback_state.current_song_index == 1
        controller.previous_song()
        assert controller._playback_state.current_song_index == 0


class TestPlaybackStatePersistence:
    """Tests for persisting and restoring playback state."""
    
    def test_load_set_persists_state(self, mock_set_manager, mock_song_manager, mock_playback_engine, sample_set):
        """Test that loading a set persists the playback state."""
        mock_storage = Mock()
        mock_storage.load_playback_state.return_value = None
        ctrl = SetScreenController(mock_set_manager, mock_song_manager, mock_playback_engine, storage_manager=mock_storage)
        
        mock_set_manager.get_set.return_value = sample_set
        ctrl.load_set("set-1")
        
        mock_storage.save_playback_state.assert_called()
        saved_state = mock_storage.save_playback_state.call_args[0][0]
        assert saved_state.current_set_id == "set-1"
        assert saved_state.current_song_index == 0
        assert saved_state.is_playing is False
    
    def test_next_song_persists_state(self, mock_set_manager, mock_song_manager, mock_playback_engine, sample_set):
        """Test that navigating to next song persists the playback state."""
        mock_storage = Mock()
        mock_storage.load_playback_state.return_value = None
        ctrl = SetScreenController(mock_set_manager, mock_song_manager, mock_playback_engine, storage_manager=mock_storage)
        
        mock_set_manager.get_set.return_value = sample_set
        ctrl._playback_state.current_set_id = "set-1"
        ctrl._playback_state.current_song_index = 0
        
        ctrl.next_song()
        
        mock_storage.save_playback_state.assert_called()
        saved_state = mock_storage.save_playback_state.call_args[0][0]
        assert saved_state.current_song_index == 1
    
    def test_restores_state_on_init(self, mock_set_manager, mock_song_manager, mock_playback_engine, sample_set):
        """Test that playback state is restored from storage on init."""
        mock_storage = Mock()
        saved_state = PlaybackState(current_set_id="set-1", current_song_index=2)
        mock_storage.load_playback_state.return_value = saved_state
        mock_set_manager.get_set.return_value = sample_set
        
        ctrl = SetScreenController(mock_set_manager, mock_song_manager, mock_playback_engine, storage_manager=mock_storage)
        
        state = ctrl.get_playback_state()
        assert state.current_set_id == "set-1"
        assert state.current_song_index == 2
        assert state.is_playing is False
    
    def test_restores_state_clamps_index(self, mock_set_manager, mock_song_manager, mock_playback_engine):
        """Test that restored song index is clamped to valid range."""
        mock_storage = Mock()
        saved_state = PlaybackState(current_set_id="set-1", current_song_index=99)
        mock_storage.load_playback_state.return_value = saved_state
        small_set = Set(id="set-1", name="Small Set", songs=["song-1", "song-2"])
        mock_set_manager.get_set.return_value = small_set
        
        ctrl = SetScreenController(mock_set_manager, mock_song_manager, mock_playback_engine, storage_manager=mock_storage)
        
        state = ctrl.get_playback_state()
        assert state.current_song_index == 1  # Clamped to last valid index
    
    def test_restores_state_ignores_deleted_set(self, mock_set_manager, mock_song_manager, mock_playback_engine):
        """Test that restoration ignores a set that no longer exists."""
        mock_storage = Mock()
        saved_state = PlaybackState(current_set_id="deleted-set", current_song_index=0)
        mock_storage.load_playback_state.return_value = saved_state
        mock_set_manager.get_set.return_value = None
        
        ctrl = SetScreenController(mock_set_manager, mock_song_manager, mock_playback_engine, storage_manager=mock_storage)
        
        state = ctrl.get_playback_state()
        assert state.current_set_id is None
    
    def test_no_storage_manager_works_fine(self, mock_set_manager, mock_song_manager, mock_playback_engine):
        """Test that controller works without a storage manager."""
        ctrl = SetScreenController(mock_set_manager, mock_song_manager, mock_playback_engine, storage_manager=None)
        
        state = ctrl.get_playback_state()
        assert state.current_set_id is None
