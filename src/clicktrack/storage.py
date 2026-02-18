"""
Storage Manager for the Click Track Player application.

This module handles file-based persistence of songs, sets, and playback state
using JSON serialization. It provides error handling for corrupted data and
automatic backup creation.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

from clicktrack.models import Song, Set, PlaybackState

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages file-based storage for songs, sets, and playback state.
    
    Storage locations:
        - Songs: ~/.clicktrack/songs.json
        - Sets: ~/.clicktrack/sets.json
        - Playback state: ~/.clicktrack/state.json
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the storage manager.
        
        Args:
            storage_dir: Optional custom storage directory. 
                        Defaults to ~/.clicktrack
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".clicktrack"
        
        self.storage_dir = Path(storage_dir)
        self.songs_file = self.storage_dir / "songs.json"
        self.sets_file = self.storage_dir / "sets.json"
        self.state_file = self.storage_dir / "state.json"
        
        # Create storage directory if it doesn't exist
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Create the storage directory if it doesn't exist."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ready: {self.storage_dir}")
        except PermissionError as e:
            logger.error(f"Permission denied creating storage directory {self.storage_dir}: {e}")
            raise RuntimeError(f"Cannot create storage directory (permission denied): {self.storage_dir}") from e
        except OSError as e:
            logger.error(f"OS error creating storage directory {self.storage_dir}: {e}")
            raise RuntimeError(f"Cannot create storage directory: {self.storage_dir}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating storage directory: {e}", exc_info=True)
            raise
    
    def _create_backup(self, file_path: Path):
        """
        Create a backup of a file before writing.
        
        Args:
            file_path: Path to the file to backup
        """
        if file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            try:
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup for {file_path}: {e}")
    
    def _write_json(self, file_path: Path, data: dict):
        """
        Write data to a JSON file with backup creation.
        
        Args:
            file_path: Path to the file to write
            data: Data to write
            
        Raises:
            IOError: If write fails
        """
        # Create backup before writing
        self._create_backup(file_path)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Successfully wrote to {file_path}")
        except PermissionError as e:
            logger.error(f"Permission denied writing to {file_path}: {e}")
            raise IOError(f"Cannot write to file (permission denied): {file_path}") from e
        except OSError as e:
            logger.error(f"OS error writing to {file_path}: {e}")
            raise IOError(f"Cannot write to file: {file_path}") from e
        except Exception as e:
            logger.error(f"Unexpected error writing to {file_path}: {e}", exc_info=True)
            raise
    
    def _read_json(self, file_path: Path) -> dict:
        """
        Read data from a JSON file with error handling.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Parsed JSON data, or empty dict if file doesn't exist or is corrupted
        """
        # Handle file not found (first run)
        if not file_path.exists():
            logger.info(f"File not found (first run): {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Successfully read from {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted JSON in {file_path}: {e}")
            logger.info("Returning empty data due to corruption")
            # Try to restore from backup
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            if backup_path.exists():
                logger.info(f"Attempting to restore from backup: {backup_path}")
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info("Successfully restored from backup")
                    return data
                except Exception as backup_error:
                    logger.error(f"Failed to restore from backup: {backup_error}")
            return {}
        except PermissionError as e:
            logger.error(f"Permission denied reading {file_path}: {e}")
            return {}
        except OSError as e:
            logger.error(f"OS error reading {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path}: {e}", exc_info=True)
            return {}
    
    def save_songs(self, songs: List[Song]):
        """
        Save songs to storage.
        
        Args:
            songs: List of Song objects to save
        """
        data = {
            "songs": [song.to_dict() for song in songs]
        }
        self._write_json(self.songs_file, data)
        logger.info(f"Saved {len(songs)} songs")
    
    def load_songs(self) -> List[Song]:
        """
        Load songs from storage.
        
        Returns:
            List of Song objects, empty list if no data or error
        """
        data = self._read_json(self.songs_file)
        
        if not data or "songs" not in data:
            logger.info("No songs found in storage")
            return []
        
        try:
            songs = [Song.from_dict(song_data) for song_data in data["songs"]]
            logger.info(f"Loaded {len(songs)} songs")
            return songs
        except Exception as e:
            logger.error(f"Failed to parse songs from storage: {e}")
            return []
    
    def save_sets(self, sets: List[Set]):
        """
        Save sets to storage.
        
        Args:
            sets: List of Set objects to save
        """
        data = {
            "sets": [s.to_dict() for s in sets]
        }
        self._write_json(self.sets_file, data)
        logger.info(f"Saved {len(sets)} sets")
    
    def load_sets(self) -> List[Set]:
        """
        Load sets from storage.
        
        Returns:
            List of Set objects, empty list if no data or error
        """
        data = self._read_json(self.sets_file)
        
        if not data or "sets" not in data:
            logger.info("No sets found in storage")
            return []
        
        try:
            sets = [Set.from_dict(set_data) for set_data in data["sets"]]
            logger.info(f"Loaded {len(sets)} sets")
            return sets
        except Exception as e:
            logger.error(f"Failed to parse sets from storage: {e}")
            return []
    
    def save_playback_state(self, state: PlaybackState):
        """
        Save playback state to storage.
        
        Args:
            state: PlaybackState object to save
        """
        data = state.to_dict()
        self._write_json(self.state_file, data)
        logger.debug("Saved playback state")
    
    def load_playback_state(self) -> Optional[PlaybackState]:
        """
        Load playback state from storage.
        
        Returns:
            PlaybackState object, or None if no data or error
        """
        data = self._read_json(self.state_file)
        
        if not data:
            logger.info("No playback state found in storage")
            return None
        
        try:
            state = PlaybackState.from_dict(data)
            logger.debug("Loaded playback state")
            return state
        except Exception as e:
            logger.error(f"Failed to parse playback state from storage: {e}")
            return None
