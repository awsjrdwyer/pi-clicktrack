"""
Set Manager for the Click Track Player application.

This module provides CRUD operations for sets and integrates with the
Storage Manager for persistence.
"""

import logging
from typing import List, Optional

from clicktrack.models import Set
from clicktrack.storage import StorageManager

logger = logging.getLogger(__name__)


class SetManager:
    """
    Manages CRUD operations for sets with automatic persistence.
    
    The SetManager maintains an in-memory collection of sets and
    automatically persists changes to storage through the StorageManager.
    """
    
    def __init__(self, storage_manager: StorageManager):
        """
        Initialize the set manager.
        
        Args:
            storage_manager: StorageManager instance for persistence
        """
        self.storage_manager = storage_manager
        self._sets: dict[str, Set] = {}
        
        # Load existing sets from storage
        self._load_sets()
    
    def _load_sets(self):
        """Load sets from storage into memory."""
        try:
            sets = self.storage_manager.load_sets()
            self._sets = {s.id: s for s in sets}
            logger.info(f"Loaded {len(self._sets)} sets into memory")
            if self._sets:
                logger.debug(f"Set IDs: {list(self._sets.keys())}")
        except Exception as e:
            logger.error(f"Error loading sets from storage: {e}", exc_info=True)
            self._sets = {}
            logger.warning("Starting with empty set library due to load error")
    
    def _persist(self):
        """Persist current sets to storage."""
        try:
            sets_list = list(self._sets.values())
            self.storage_manager.save_sets(sets_list)
            logger.debug(f"Persisted {len(sets_list)} sets to storage")
        except Exception as e:
            logger.error(f"Failed to persist sets to storage: {e}", exc_info=True)
            raise RuntimeError("Failed to save sets to storage") from e
    
    def create_set(self, name: str) -> Set:
        """
        Create a new set and persist it to storage.
        
        Args:
            name: Set name (non-empty string)
            
        Returns:
            The created Set object
            
        Raises:
            ValueError: If validation fails
        """
        # Create set (validation happens in Set.__post_init__)
        new_set = Set(name=name)
        
        # Add to in-memory collection
        self._sets[new_set.id] = new_set
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Created set: {new_set.name} (ID: {new_set.id})")
        return new_set
    
    def update_set(self, set_id: str, name: str) -> Set:
        """
        Update an existing set and persist changes to storage.
        
        Args:
            set_id: ID of the set to update
            name: New name for the set
            
        Returns:
            The updated Set object
            
        Raises:
            ValueError: If set not found or validation fails
        """
        # Check if set exists
        if set_id not in self._sets:
            raise ValueError(f"Set with ID {set_id} not found")
        
        existing_set = self._sets[set_id]
        
        # Create updated set with new name (keep existing songs)
        updated_set = Set(
            id=set_id,
            name=name,
            songs=existing_set.songs.copy()
        )
        
        # Update in-memory collection
        self._sets[set_id] = updated_set
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Updated set: {updated_set.name} (ID: {set_id})")
        return updated_set
    
    def delete_set(self, set_id: str):
        """
        Delete a set and persist changes to storage.
        
        Args:
            set_id: ID of the set to delete
            
        Raises:
            ValueError: If set not found
        """
        # Check if set exists
        if set_id not in self._sets:
            raise ValueError(f"Set with ID {set_id} not found")
        
        set_name = self._sets[set_id].name
        
        # Remove from in-memory collection
        del self._sets[set_id]
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Deleted set: {set_name} (ID: {set_id})")
    
    def get_set(self, set_id: str) -> Optional[Set]:
        """
        Retrieve a set by ID.
        
        Args:
            set_id: ID of the set to retrieve
            
        Returns:
            Set object if found, None otherwise
        """
        return self._sets.get(set_id)
    
    def get_all_sets(self) -> List[Set]:
        """
        Retrieve all sets.
        
        Returns:
            List of all Set objects
        """
        return list(self._sets.values())
    
    def add_song_to_set(self, set_id: str, song_id: str):
        """
        Add a song to a set and persist changes to storage.
        
        Args:
            set_id: ID of the set
            song_id: ID of the song to add
            
        Raises:
            ValueError: If set not found
        """
        # Check if set exists
        if set_id not in self._sets:
            raise ValueError(f"Set with ID {set_id} not found")
        
        current_set = self._sets[set_id]
        
        # Add song ID to the set's song list (duplicates allowed for encores, etc.)
        current_set.songs.append(song_id)
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Added song {song_id} to set {current_set.name} (ID: {set_id})")
    
    def remove_song_from_set(self, set_id: str, song_id: str, song_index: Optional[int] = None):
        """
        Remove a song from a set and persist changes to storage.
        
        Args:
            set_id: ID of the set
            song_id: ID of the song to remove
            song_index: Optional index of the song to remove (for duplicate handling).
                       If provided, removes the song at that specific index.
                       If not provided, removes the first occurrence.
            
        Raises:
            ValueError: If set not found or song not in set
        """
        # Check if set exists
        if set_id not in self._sets:
            raise ValueError(f"Set with ID {set_id} not found")
        
        current_set = self._sets[set_id]
        
        if song_index is not None:
            # Remove by index
            if 0 <= song_index < len(current_set.songs) and current_set.songs[song_index] == song_id:
                current_set.songs.pop(song_index)
                self._persist()
                logger.info(f"Removed song {song_id} at index {song_index} from set {current_set.name}")
            else:
                raise ValueError(f"Song {song_id} not found at index {song_index} in set {set_id}")
        elif song_id in current_set.songs:
            # Remove first occurrence (backward compatible)
            current_set.songs.remove(song_id)
            self._persist()
            logger.info(f"Removed song {song_id} from set {current_set.name} (ID: {set_id})")
        else:
            raise ValueError(f"Song {song_id} not found in set {set_id}")
    
    def reorder_songs(self, set_id: str, song_ids: List[str]):
        """
        Reorder songs in a set and persist changes to storage.
        
        Args:
            set_id: ID of the set
            song_ids: Complete ordered list of song IDs
            
        Raises:
            ValueError: If set not found
        """
        # Check if set exists
        if set_id not in self._sets:
            raise ValueError(f"Set with ID {set_id} not found")
        
        current_set = self._sets[set_id]
        
        # Replace the song list with the new order
        current_set.songs = song_ids.copy()
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Reordered songs in set {current_set.name} (ID: {set_id})")
