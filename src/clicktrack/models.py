"""
Data models for the Click Track Player application.

This module defines the core data structures used throughout the application:
- Song: Musical piece with tempo, time signature, and click configuration
- Set: Ordered collection of songs for a performance
- PlaybackState: Current playback status and position
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Literal


# Valid time signatures supported by the application
VALID_TIME_SIGNATURES = [
    (2, 4), (3, 4), (4, 4), (5, 4),
    (6, 8), (7, 8), (9, 8), (12, 8)
]


@dataclass
class TimeSignature:
    """Represents a musical time signature."""
    beats_per_measure: int
    note_value: int
    
    def __post_init__(self):
        """Validate time signature after initialization."""
        if (self.beats_per_measure, self.note_value) not in VALID_TIME_SIGNATURES:
            raise ValueError(
                f"Invalid time signature {self.beats_per_measure}/{self.note_value}. "
                f"Supported time signatures: {', '.join(f'{b}/{n}' for b, n in VALID_TIME_SIGNATURES)}"
            )
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "beatsPerMeasure": self.beats_per_measure,
            "noteValue": self.note_value
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary."""
        return cls(
            beats_per_measure=data["beatsPerMeasure"],
            note_value=data["noteValue"]
        )
    
    def __str__(self):
        return f"{self.beats_per_measure}/{self.note_value}"


@dataclass
class Song:
    """
    Represents a musical piece with click track configuration.
    
    Attributes:
        id: Unique identifier (UUID)
        title: Song title (non-empty string)
        bpm: Beats per minute (positive number)
        time_signature: Time signature (e.g., 4/4, 3/4, 6/8)
        subdivision: Click rate ("single" for one click per beat, "double" for two)
        accent_pattern: Boolean array indicating accented beats
        click_sound: Name of the click sound to use
    """
    title: str
    bpm: float
    time_signature: TimeSignature
    subdivision: Literal["single", "double"]
    accent_pattern: List[bool]
    click_sound: Literal["wood_block", "beep", "cowbell"]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate song data after initialization."""
        # Validate title
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
        
        # Validate BPM
        if self.bpm <= 0:
            raise ValueError("BPM must be a positive number")
        
        # Validate accent pattern length matches beats per measure
        if len(self.accent_pattern) != self.time_signature.beats_per_measure:
            raise ValueError(
                f"Accent pattern length ({len(self.accent_pattern)}) must match "
                f"beats per measure ({self.time_signature.beats_per_measure})"
            )
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "bpm": self.bpm,
            "timeSignature": self.time_signature.to_dict(),
            "subdivision": self.subdivision,
            "accentPattern": self.accent_pattern,
            "clickSound": self.click_sound
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Song from dictionary."""
        # Migrate old subdivision values
        subdivision = data["subdivision"]
        if subdivision == "quarter":
            subdivision = "single"
        elif subdivision == "eighth":
            subdivision = "double"
        
        return cls(
            id=data["id"],
            title=data["title"],
            bpm=data["bpm"],
            time_signature=TimeSignature.from_dict(data["timeSignature"]),
            subdivision=subdivision,
            accent_pattern=data["accentPattern"],
            click_sound=data["clickSound"]
        )


@dataclass
class Set:
    """
    Represents an ordered collection of songs for a performance.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Set name (non-empty string)
        songs: Ordered list of song IDs
    """
    name: str
    songs: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate set data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Set name cannot be empty")
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "songs": self.songs
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Set from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            songs=data.get("songs", [])
        )


@dataclass
class PlaybackState:
    """
    Represents the current playback state.
    
    Attributes:
        current_set_id: ID of the currently loaded set (None if no set loaded)
        current_song_index: Index of current song in the set
        is_playing: Whether playback is active
        current_bpm: BPM of currently playing song (None if not playing)
    """
    current_set_id: Optional[str] = None
    current_song_index: int = 0
    is_playing: bool = False
    current_bpm: Optional[float] = None
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "currentSetId": self.current_set_id,
            "currentSongIndex": self.current_song_index,
            "isPlaying": self.is_playing,
            "currentBpm": self.current_bpm
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create PlaybackState from dictionary."""
        return cls(
            current_set_id=data.get("currentSetId"),
            current_song_index=data.get("currentSongIndex", 0),
            is_playing=data.get("isPlaying", False),
            current_bpm=data.get("currentBpm")
        )
