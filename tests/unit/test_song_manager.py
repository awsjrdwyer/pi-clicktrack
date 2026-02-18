"""
Unit tests for the Song Manager.

Tests cover:
- CRUD operations (create, read, update, delete)
- Integration with Storage Manager
- Error handling for invalid operations
"""

import pytest
import tempfile
from pathlib import Path

from clicktrack.song_manager import SongManager
from clicktrack.storage import StorageManager
from clicktrack.models import Song, TimeSignature


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
def song_manager(storage_manager):
    """Create a SongManager instance with temporary storage."""
    return SongManager(storage_manager=storage_manager)


class TestSongCreation:
    """Test song creation operations."""
    
    def test_create_song_basic(self, song_manager):
        """Test creating a basic song."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="Test Song",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        assert song.title == "Test Song"
        assert song.bpm == 120.0
        assert song.volume == 75
        assert song.id is not None
    
    def test_create_song_persists_to_storage(self, song_manager, storage_manager):
        """Test that created song is persisted to storage."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="Persisted Song",
            bpm=140.0,
            time_signature=ts,
            subdivision="eighth",
            accent_pattern=[True, False, False, False],
            click_sound="beep",
            volume=80
        )
        
        # Load directly from storage to verify persistence
        loaded_songs = storage_manager.load_songs()
        assert len(loaded_songs) == 1
        assert loaded_songs[0].title == "Persisted Song"
        assert loaded_songs[0].id == song.id
    
    def test_create_song_with_invalid_bpm_raises_error(self, song_manager):
        """Test that creating song with invalid BPM raises error."""
        ts = TimeSignature(4, 4)
        with pytest.raises(ValueError, match="BPM must be a positive number"):
            song_manager.create_song(
                title="Invalid Song",
                bpm=-10.0,
                time_signature=ts,
                subdivision="quarter",
                accent_pattern=[True, False, False, False],
                click_sound="wood_block",
                volume=75
            )
    
    def test_create_song_with_empty_title_raises_error(self, song_manager):
        """Test that creating song with empty title raises error."""
        ts = TimeSignature(4, 4)
        with pytest.raises(ValueError, match="Title cannot be empty"):
            song_manager.create_song(
                title="",
                bpm=120.0,
                time_signature=ts,
                subdivision="quarter",
                accent_pattern=[True, False, False, False],
                click_sound="wood_block",
                volume=75
            )


class TestSongRetrieval:
    """Test song retrieval operations."""
    
    def test_get_song_by_id(self, song_manager):
        """Test retrieving a song by ID."""
        ts = TimeSignature(4, 4)
        created_song = song_manager.create_song(
            title="Retrievable Song",
            bpm=130.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="cowbell",
            volume=85
        )
        
        retrieved_song = song_manager.get_song(created_song.id)
        assert retrieved_song is not None
        assert retrieved_song.id == created_song.id
        assert retrieved_song.title == "Retrievable Song"
    
    def test_get_song_returns_none_for_nonexistent_id(self, song_manager):
        """Test that getting nonexistent song returns None."""
        song = song_manager.get_song("nonexistent-id")
        assert song is None
    
    def test_get_all_songs_empty(self, song_manager):
        """Test getting all songs when library is empty."""
        songs = song_manager.get_all_songs()
        assert songs == []
    
    def test_get_all_songs_multiple(self, song_manager):
        """Test getting all songs with multiple songs in library."""
        ts = TimeSignature(4, 4)
        
        song1 = song_manager.create_song(
            title="Song 1",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        song2 = song_manager.create_song(
            title="Song 2",
            bpm=140.0,
            time_signature=ts,
            subdivision="eighth",
            accent_pattern=[True, False, False, False],
            click_sound="beep",
            volume=80
        )
        
        all_songs = song_manager.get_all_songs()
        assert len(all_songs) == 2
        song_ids = {s.id for s in all_songs}
        assert song1.id in song_ids
        assert song2.id in song_ids


class TestSongUpdate:
    """Test song update operations."""
    
    def test_update_song_title(self, song_manager):
        """Test updating a song's title."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="Original Title",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        updated_song = song_manager.update_song(song.id, title="Updated Title")
        
        assert updated_song.title == "Updated Title"
        assert updated_song.bpm == 120.0  # Other fields unchanged
        assert updated_song.id == song.id
    
    def test_update_song_bpm(self, song_manager):
        """Test updating a song's BPM."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="Test Song",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        updated_song = song_manager.update_song(song.id, bpm=150.0)
        
        assert updated_song.bpm == 150.0
        assert updated_song.title == "Test Song"  # Other fields unchanged
    
    def test_update_song_multiple_fields(self, song_manager):
        """Test updating multiple fields at once."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="Test Song",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        updated_song = song_manager.update_song(
            song.id,
            title="New Title",
            bpm=160.0,
            volume=90
        )
        
        assert updated_song.title == "New Title"
        assert updated_song.bpm == 160.0
        assert updated_song.volume == 90
    
    def test_update_song_persists_to_storage(self, song_manager, storage_manager):
        """Test that updated song is persisted to storage."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="Original",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        song_manager.update_song(song.id, title="Updated")
        
        # Load directly from storage to verify persistence
        loaded_songs = storage_manager.load_songs()
        assert len(loaded_songs) == 1
        assert loaded_songs[0].title == "Updated"
    
    def test_update_nonexistent_song_raises_error(self, song_manager):
        """Test that updating nonexistent song raises error."""
        with pytest.raises(ValueError, match="Song with ID .* not found"):
            song_manager.update_song("nonexistent-id", title="New Title")
    
    def test_update_song_with_invalid_bpm_raises_error(self, song_manager):
        """Test that updating with invalid BPM raises error."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="Test Song",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        with pytest.raises(ValueError, match="BPM must be a positive number"):
            song_manager.update_song(song.id, bpm=-50.0)


class TestSongDeletion:
    """Test song deletion operations."""
    
    def test_delete_song(self, song_manager):
        """Test deleting a song."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="To Delete",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        song_manager.delete_song(song.id)
        
        # Verify song is no longer retrievable
        retrieved_song = song_manager.get_song(song.id)
        assert retrieved_song is None
    
    def test_delete_song_persists_to_storage(self, song_manager, storage_manager):
        """Test that song deletion is persisted to storage."""
        ts = TimeSignature(4, 4)
        song = song_manager.create_song(
            title="To Delete",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        song_manager.delete_song(song.id)
        
        # Load directly from storage to verify persistence
        loaded_songs = storage_manager.load_songs()
        assert len(loaded_songs) == 0
    
    def test_delete_nonexistent_song_raises_error(self, song_manager):
        """Test that deleting nonexistent song raises error."""
        with pytest.raises(ValueError, match="Song with ID .* not found"):
            song_manager.delete_song("nonexistent-id")
    
    def test_delete_one_song_preserves_others(self, song_manager):
        """Test that deleting one song doesn't affect others."""
        ts = TimeSignature(4, 4)
        
        song1 = song_manager.create_song(
            title="Song 1",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        
        song2 = song_manager.create_song(
            title="Song 2",
            bpm=140.0,
            time_signature=ts,
            subdivision="eighth",
            accent_pattern=[True, False, False, False],
            click_sound="beep",
            volume=80
        )
        
        song_manager.delete_song(song1.id)
        
        # Verify song2 still exists
        remaining_songs = song_manager.get_all_songs()
        assert len(remaining_songs) == 1
        assert remaining_songs[0].id == song2.id


class TestSongManagerPersistence:
    """Test that SongManager loads existing songs on initialization."""
    
    def test_loads_existing_songs_on_init(self, storage_manager):
        """Test that SongManager loads existing songs from storage on initialization."""
        # Create and save a song directly to storage
        ts = TimeSignature(4, 4)
        song = Song(
            title="Existing Song",
            bpm=120.0,
            time_signature=ts,
            subdivision="quarter",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block",
            volume=75
        )
        storage_manager.save_songs([song])
        
        # Create new SongManager instance
        new_manager = SongManager(storage_manager=storage_manager)
        
        # Verify song was loaded
        loaded_songs = new_manager.get_all_songs()
        assert len(loaded_songs) == 1
        assert loaded_songs[0].title == "Existing Song"
