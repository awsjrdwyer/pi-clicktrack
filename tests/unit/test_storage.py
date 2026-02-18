"""
Unit tests for the Storage Manager.

Tests cover:
- File creation and directory setup
- JSON serialization/deserialization
- Error handling for corrupted data
- Backup creation
- First run scenarios
"""

import json
import pytest
import tempfile
from pathlib import Path

from clicktrack.storage import StorageManager
from clicktrack.models import Song, Set, PlaybackState, TimeSignature


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a StorageManager instance with temporary storage."""
    return StorageManager(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_song():
    """Create a sample song for testing."""
    return Song(
        title="Test Song",
        bpm=120.0,
        time_signature=TimeSignature(4, 4),
        subdivision="quarter",
        accent_pattern=[True, False, False, False],
        click_sound="wood_block",
        volume=75
    )


@pytest.fixture
def sample_set():
    """Create a sample set for testing."""
    return Set(
        name="Test Set",
        songs=["song-id-1", "song-id-2"]
    )


class TestStorageManagerInitialization:
    """Test storage manager initialization and directory creation."""
    
    def test_creates_storage_directory(self, temp_storage_dir):
        """Test that storage directory is created on initialization."""
        storage_dir = temp_storage_dir / "new_dir"
        assert not storage_dir.exists()
        
        StorageManager(storage_dir=storage_dir)
        
        assert storage_dir.exists()
        assert storage_dir.is_dir()
    
    def test_uses_default_directory_when_none_provided(self):
        """Test that default ~/.clicktrack directory is used when no path provided."""
        manager = StorageManager()
        expected_dir = Path.home() / ".clicktrack"
        assert manager.storage_dir == expected_dir


class TestSongStorage:
    """Test song save and load operations."""
    
    def test_save_and_load_songs(self, storage_manager, sample_song):
        """Test saving and loading songs."""
        songs = [sample_song]
        
        storage_manager.save_songs(songs)
        loaded_songs = storage_manager.load_songs()
        
        assert len(loaded_songs) == 1
        assert loaded_songs[0].title == sample_song.title
        assert loaded_songs[0].bpm == sample_song.bpm
        assert loaded_songs[0].volume == sample_song.volume
    
    def test_load_songs_returns_empty_list_on_first_run(self, storage_manager):
        """Test that loading songs on first run returns empty list."""
        songs = storage_manager.load_songs()
        assert songs == []
    
    def test_save_multiple_songs(self, storage_manager):
        """Test saving multiple songs."""
        songs = [
            Song(
                title=f"Song {i}",
                bpm=120.0 + i,
                time_signature=TimeSignature(4, 4),
                subdivision="quarter",
                accent_pattern=[True, False, False, False],
                click_sound="wood_block",
                volume=75
            )
            for i in range(3)
        ]
        
        storage_manager.save_songs(songs)
        loaded_songs = storage_manager.load_songs()
        
        assert len(loaded_songs) == 3
        assert [s.title for s in loaded_songs] == ["Song 0", "Song 1", "Song 2"]


class TestSetStorage:
    """Test set save and load operations."""
    
    def test_save_and_load_sets(self, storage_manager, sample_set):
        """Test saving and loading sets."""
        sets = [sample_set]
        
        storage_manager.save_sets(sets)
        loaded_sets = storage_manager.load_sets()
        
        assert len(loaded_sets) == 1
        assert loaded_sets[0].name == sample_set.name
        assert loaded_sets[0].songs == sample_set.songs
    
    def test_load_sets_returns_empty_list_on_first_run(self, storage_manager):
        """Test that loading sets on first run returns empty list."""
        sets = storage_manager.load_sets()
        assert sets == []
    
    def test_save_multiple_sets(self, storage_manager):
        """Test saving multiple sets."""
        sets = [
            Set(name=f"Set {i}", songs=[f"song-{i}-1", f"song-{i}-2"])
            for i in range(3)
        ]
        
        storage_manager.save_sets(sets)
        loaded_sets = storage_manager.load_sets()
        
        assert len(loaded_sets) == 3
        assert [s.name for s in loaded_sets] == ["Set 0", "Set 1", "Set 2"]


class TestPlaybackStateStorage:
    """Test playback state save and load operations."""
    
    def test_save_and_load_playback_state(self, storage_manager):
        """Test saving and loading playback state."""
        state = PlaybackState(
            current_set_id="set-123",
            current_song_index=2,
            is_playing=True,
            current_bpm=140.0
        )
        
        storage_manager.save_playback_state(state)
        loaded_state = storage_manager.load_playback_state()
        
        assert loaded_state is not None
        assert loaded_state.current_set_id == "set-123"
        assert loaded_state.current_song_index == 2
        assert loaded_state.is_playing is True
        assert loaded_state.current_bpm == 140.0
    
    def test_load_playback_state_returns_none_on_first_run(self, storage_manager):
        """Test that loading playback state on first run returns None."""
        state = storage_manager.load_playback_state()
        assert state is None


class TestErrorHandling:
    """Test error handling for corrupted data."""
    
    def test_load_songs_handles_corrupted_json(self, storage_manager):
        """Test that corrupted JSON is handled gracefully."""
        # Write invalid JSON to songs file
        with open(storage_manager.songs_file, 'w') as f:
            f.write("{ invalid json }")
        
        songs = storage_manager.load_songs()
        assert songs == []
    
    def test_load_sets_handles_corrupted_json(self, storage_manager):
        """Test that corrupted JSON is handled gracefully."""
        # Write invalid JSON to sets file
        with open(storage_manager.sets_file, 'w') as f:
            f.write("{ invalid json }")
        
        sets = storage_manager.load_sets()
        assert sets == []
    
    def test_load_playback_state_handles_corrupted_json(self, storage_manager):
        """Test that corrupted JSON is handled gracefully."""
        # Write invalid JSON to state file
        with open(storage_manager.state_file, 'w') as f:
            f.write("{ invalid json }")
        
        state = storage_manager.load_playback_state()
        assert state is None
    
    def test_load_songs_handles_invalid_data_structure(self, storage_manager):
        """Test that invalid data structure is handled gracefully."""
        # Write valid JSON but invalid structure
        with open(storage_manager.songs_file, 'w') as f:
            json.dump({"songs": [{"invalid": "structure"}]}, f)
        
        songs = storage_manager.load_songs()
        assert songs == []


class TestBackupCreation:
    """Test backup file creation."""
    
    def test_creates_backup_before_overwriting(self, storage_manager, sample_song):
        """Test that backup is created before overwriting existing file."""
        # Save initial data
        songs = [sample_song]
        storage_manager.save_songs(songs)
        
        # Modify and save again
        sample_song.title = "Modified Song"
        storage_manager.save_songs([sample_song])
        
        # Check that backup exists
        backup_file = storage_manager.songs_file.with_suffix(".json.backup")
        assert backup_file.exists()
        
        # Verify backup contains original data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        assert backup_data["songs"][0]["title"] == "Test Song"
    
    def test_no_backup_on_first_save(self, storage_manager, sample_song):
        """Test that no backup is created on first save."""
        songs = [sample_song]
        storage_manager.save_songs(songs)
        
        backup_file = storage_manager.songs_file.with_suffix(".json.backup")
        assert not backup_file.exists()
