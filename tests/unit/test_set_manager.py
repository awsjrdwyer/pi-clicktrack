"""
Unit tests for SetManager.

These tests verify the CRUD operations and song management functionality
of the SetManager class.
"""

import pytest
import tempfile
from pathlib import Path

from clicktrack.models import Set
from clicktrack.storage import StorageManager
from clicktrack.set_manager import SetManager


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_manager(temp_storage):
    """Create a StorageManager instance with temporary storage."""
    return StorageManager(temp_storage)


@pytest.fixture
def set_manager(storage_manager):
    """Create a SetManager instance for testing."""
    return SetManager(storage_manager)


class TestSetManagerCRUD:
    """Test CRUD operations for sets."""
    
    def test_create_set(self, set_manager):
        """Test creating a new set."""
        new_set = set_manager.create_set("My Performance")
        
        assert new_set.name == "My Performance"
        assert new_set.id is not None
        assert len(new_set.songs) == 0
        
        # Verify it's retrievable
        retrieved = set_manager.get_set(new_set.id)
        assert retrieved is not None
        assert retrieved.name == "My Performance"
    
    def test_create_set_with_empty_name_fails(self, set_manager):
        """Test that creating a set with empty name fails."""
        with pytest.raises(ValueError, match="Set name cannot be empty"):
            set_manager.create_set("")
    
    def test_update_set(self, set_manager):
        """Test updating a set's name."""
        new_set = set_manager.create_set("Original Name")
        
        updated = set_manager.update_set(new_set.id, "Updated Name")
        
        assert updated.name == "Updated Name"
        assert updated.id == new_set.id
        
        # Verify persistence
        retrieved = set_manager.get_set(new_set.id)
        assert retrieved.name == "Updated Name"
    
    def test_update_nonexistent_set_fails(self, set_manager):
        """Test that updating a nonexistent set fails."""
        with pytest.raises(ValueError, match="Set with ID .* not found"):
            set_manager.update_set("nonexistent-id", "New Name")
    
    def test_delete_set(self, set_manager):
        """Test deleting a set."""
        new_set = set_manager.create_set("To Delete")
        set_id = new_set.id
        
        set_manager.delete_set(set_id)
        
        # Verify it's no longer retrievable
        retrieved = set_manager.get_set(set_id)
        assert retrieved is None
    
    def test_delete_nonexistent_set_fails(self, set_manager):
        """Test that deleting a nonexistent set fails."""
        with pytest.raises(ValueError, match="Set with ID .* not found"):
            set_manager.delete_set("nonexistent-id")
    
    def test_get_all_sets(self, set_manager):
        """Test retrieving all sets."""
        set1 = set_manager.create_set("Set 1")
        set2 = set_manager.create_set("Set 2")
        set3 = set_manager.create_set("Set 3")
        
        all_sets = set_manager.get_all_sets()
        
        assert len(all_sets) == 3
        set_ids = {s.id for s in all_sets}
        assert set1.id in set_ids
        assert set2.id in set_ids
        assert set3.id in set_ids


class TestSetManagerSongOperations:
    """Test song management operations within sets."""
    
    def test_add_song_to_set(self, set_manager):
        """Test adding a song to a set."""
        new_set = set_manager.create_set("My Set")
        song_id = "song-123"
        
        set_manager.add_song_to_set(new_set.id, song_id)
        
        # Verify song was added
        retrieved = set_manager.get_set(new_set.id)
        assert song_id in retrieved.songs
        assert len(retrieved.songs) == 1
    
    def test_add_multiple_songs_to_set(self, set_manager):
        """Test adding multiple songs to a set."""
        new_set = set_manager.create_set("My Set")
        song_ids = ["song-1", "song-2", "song-3"]
        
        for song_id in song_ids:
            set_manager.add_song_to_set(new_set.id, song_id)
        
        # Verify all songs were added in order
        retrieved = set_manager.get_set(new_set.id)
        assert retrieved.songs == song_ids
    
    def test_add_duplicate_song_to_set(self, set_manager):
        """Test that adding a duplicate song doesn't create duplicates."""
        new_set = set_manager.create_set("My Set")
        song_id = "song-123"
        
        set_manager.add_song_to_set(new_set.id, song_id)
        set_manager.add_song_to_set(new_set.id, song_id)  # Add again
        
        # Verify only one instance exists
        retrieved = set_manager.get_set(new_set.id)
        assert retrieved.songs.count(song_id) == 1
    
    def test_add_song_to_nonexistent_set_fails(self, set_manager):
        """Test that adding a song to a nonexistent set fails."""
        with pytest.raises(ValueError, match="Set with ID .* not found"):
            set_manager.add_song_to_set("nonexistent-id", "song-123")
    
    def test_remove_song_from_set(self, set_manager):
        """Test removing a song from a set."""
        new_set = set_manager.create_set("My Set")
        song_id = "song-123"
        
        set_manager.add_song_to_set(new_set.id, song_id)
        set_manager.remove_song_from_set(new_set.id, song_id)
        
        # Verify song was removed
        retrieved = set_manager.get_set(new_set.id)
        assert song_id not in retrieved.songs
        assert len(retrieved.songs) == 0
    
    def test_remove_song_from_nonexistent_set_fails(self, set_manager):
        """Test that removing a song from a nonexistent set fails."""
        with pytest.raises(ValueError, match="Set with ID .* not found"):
            set_manager.remove_song_from_set("nonexistent-id", "song-123")
    
    def test_remove_nonexistent_song_from_set_fails(self, set_manager):
        """Test that removing a nonexistent song from a set fails."""
        new_set = set_manager.create_set("My Set")
        
        with pytest.raises(ValueError, match="Song .* not found in set"):
            set_manager.remove_song_from_set(new_set.id, "nonexistent-song")
    
    def test_reorder_songs(self, set_manager):
        """Test reordering songs in a set."""
        new_set = set_manager.create_set("My Set")
        song_ids = ["song-1", "song-2", "song-3"]
        
        # Add songs in original order
        for song_id in song_ids:
            set_manager.add_song_to_set(new_set.id, song_id)
        
        # Reorder songs
        new_order = ["song-3", "song-1", "song-2"]
        set_manager.reorder_songs(new_set.id, new_order)
        
        # Verify new order
        retrieved = set_manager.get_set(new_set.id)
        assert retrieved.songs == new_order
    
    def test_reorder_songs_in_nonexistent_set_fails(self, set_manager):
        """Test that reordering songs in a nonexistent set fails."""
        with pytest.raises(ValueError, match="Set with ID .* not found"):
            set_manager.reorder_songs("nonexistent-id", ["song-1", "song-2"])


class TestSetManagerPersistence:
    """Test persistence of set operations."""
    
    def test_sets_persist_across_instances(self, storage_manager):
        """Test that sets persist when creating a new SetManager instance."""
        # Create first manager and add a set
        manager1 = SetManager(storage_manager)
        new_set = manager1.create_set("Persistent Set")
        set_id = new_set.id
        
        # Create second manager (should load from storage)
        manager2 = SetManager(storage_manager)
        retrieved = manager2.get_set(set_id)
        
        assert retrieved is not None
        assert retrieved.name == "Persistent Set"
    
    def test_song_additions_persist(self, storage_manager):
        """Test that song additions persist across instances."""
        # Create first manager and add songs to a set
        manager1 = SetManager(storage_manager)
        new_set = manager1.create_set("My Set")
        manager1.add_song_to_set(new_set.id, "song-1")
        manager1.add_song_to_set(new_set.id, "song-2")
        
        # Create second manager (should load from storage)
        manager2 = SetManager(storage_manager)
        retrieved = manager2.get_set(new_set.id)
        
        assert retrieved.songs == ["song-1", "song-2"]
