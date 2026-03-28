"""
Song Manager for the Click Track Player application.

This module provides CRUD operations for songs and integrates with the
Storage Manager for persistence.
"""

import logging
from typing import List, Optional

from clicktrack.models import Song, TimeSignature
from clicktrack.storage import StorageManager

logger = logging.getLogger(__name__)


class SongManager:
    """
    Manages CRUD operations for songs with automatic persistence.
    
    The SongManager maintains an in-memory collection of songs and
    automatically persists changes to storage through the StorageManager.
    """
    
    def __init__(self, storage_manager: StorageManager):
        """
        Initialize the song manager.
        
        Args:
            storage_manager: StorageManager instance for persistence
        """
        self.storage_manager = storage_manager
        self._songs: dict[str, Song] = {}
        
        # Load existing songs from storage
        self._load_songs()
    
    def _load_songs(self):
        """Load songs from storage into memory."""
        try:
            songs = self.storage_manager.load_songs()
            self._songs = {song.id: song for song in songs}
            logger.info(f"Loaded {len(self._songs)} songs into memory")
            if self._songs:
                logger.debug(f"Song IDs: {list(self._songs.keys())}")
        except Exception as e:
            logger.error(f"Error loading songs from storage: {e}", exc_info=True)
            self._songs = {}
            logger.warning("Starting with empty song library due to load error")
    
    def _persist(self):
        """Persist current songs to storage."""
        try:
            songs_list = list(self._songs.values())
            self.storage_manager.save_songs(songs_list)
            logger.debug(f"Persisted {len(songs_list)} songs to storage")
        except Exception as e:
            logger.error(f"Failed to persist songs to storage: {e}", exc_info=True)
            raise RuntimeError("Failed to save songs to storage") from e
    
    def create_song(
        self,
        title: str,
        bpm: float,
        time_signature: TimeSignature,
        subdivision: str,
        accent_pattern: List[bool],
        click_sound: str
    ) -> Song:
        """
        Create a new song and persist it to storage.
        
        Args:
            title: Song title (non-empty string)
            bpm: Beats per minute (positive number)
            time_signature: TimeSignature object
            subdivision: Click rate ("single" or "double")
            accent_pattern: Boolean array indicating accented beats
            click_sound: Name of click sound ("wood_block", "beep", or "cowbell")
            
        Returns:
            The created Song object
            
        Raises:
            ValueError: If validation fails
        """
        # Create song (validation happens in Song.__post_init__)
        song = Song(
            title=title,
            bpm=bpm,
            time_signature=time_signature,
            subdivision=subdivision,
            accent_pattern=accent_pattern,
            click_sound=click_sound
        )
        
        # Add to in-memory collection
        self._songs[song.id] = song
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Created song: {song.title} (ID: {song.id})")
        return song
    
    def update_song(
        self,
        song_id: str,
        title: Optional[str] = None,
        bpm: Optional[float] = None,
        time_signature: Optional[TimeSignature] = None,
        subdivision: Optional[str] = None,
        accent_pattern: Optional[List[bool]] = None,
        click_sound: Optional[str] = None
    ) -> Song:
        """
        Update an existing song and persist changes to storage.
        
        Args:
            song_id: ID of the song to update
            title: New title (optional)
            bpm: New BPM (optional)
            time_signature: New time signature (optional)
            subdivision: New subdivision (optional)
            accent_pattern: New accent pattern (optional)
            click_sound: New click sound (optional)
            
        Returns:
            The updated Song object
            
        Raises:
            ValueError: If song not found or validation fails
        """
        # Check if song exists
        if song_id not in self._songs:
            raise ValueError(f"Song with ID {song_id} not found")
        
        existing_song = self._songs[song_id]
        
        # Create updated song with new values (or keep existing)
        updated_song = Song(
            id=song_id,
            title=title if title is not None else existing_song.title,
            bpm=bpm if bpm is not None else existing_song.bpm,
            time_signature=time_signature if time_signature is not None else existing_song.time_signature,
            subdivision=subdivision if subdivision is not None else existing_song.subdivision,
            accent_pattern=accent_pattern if accent_pattern is not None else existing_song.accent_pattern,
            click_sound=click_sound if click_sound is not None else existing_song.click_sound
        )
        
        # Update in-memory collection
        self._songs[song_id] = updated_song
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Updated song: {updated_song.title} (ID: {song_id})")
        return updated_song
    
    def delete_song(self, song_id: str):
        """
        Delete a song and persist changes to storage.
        
        Args:
            song_id: ID of the song to delete
            
        Raises:
            ValueError: If song not found
        """
        # Check if song exists
        if song_id not in self._songs:
            raise ValueError(f"Song with ID {song_id} not found")
        
        song_title = self._songs[song_id].title
        
        # Remove from in-memory collection
        del self._songs[song_id]
        
        # Persist to storage
        self._persist()
        
        logger.info(f"Deleted song: {song_title} (ID: {song_id})")
    
    def get_song(self, song_id: str) -> Optional[Song]:
        """
        Retrieve a song by ID.
        
        Args:
            song_id: ID of the song to retrieve
            
        Returns:
            Song object if found, None otherwise
        """
        return self._songs.get(song_id)
    
    def get_all_songs(self) -> List[Song]:
        """
        Retrieve all songs, sorted alphabetically by title (case-insensitive).
        
        Returns:
            List of all Song objects
        """
        return sorted(self._songs.values(), key=lambda s: s.title.lower())
