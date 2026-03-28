"""
Basic unit tests for data models to verify implementation.
"""

import pytest
from clicktrack.models import Song, Set, PlaybackState, TimeSignature


def test_song_creation_valid():
    """Test creating a valid song."""
    ts = TimeSignature(4, 4)
    song = Song(
        title="Test Song",
        bpm=120,
        time_signature=ts,
        subdivision="single",
        accent_pattern=[True, False, False, False],
        click_sound="wood_block"
    )
    assert song.title == "Test Song"
    assert song.bpm == 120
    assert len(song.accent_pattern) == 4


def test_song_empty_title_rejected():
    """Test that empty title is rejected."""
    ts = TimeSignature(4, 4)
    with pytest.raises(ValueError, match="Title cannot be empty"):
        Song(
            title="",
            bpm=120,
            time_signature=ts,
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block"
        )


def test_song_negative_bpm_rejected():
    """Test that negative BPM is rejected."""
    ts = TimeSignature(4, 4)
    with pytest.raises(ValueError, match="BPM must be a positive number"):
        Song(
            title="Test",
            bpm=-10,
            time_signature=ts,
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block"
        )


def test_song_accent_pattern_length_mismatch():
    """Test that accent pattern length must match beats per measure."""
    ts = TimeSignature(4, 4)
    with pytest.raises(ValueError, match="Accent pattern length"):
        Song(
            title="Test",
            bpm=120,
            time_signature=ts,
            subdivision="single",
            accent_pattern=[True, False],  # Only 2 beats for 4/4 time
            click_sound="wood_block"
        )


def test_time_signature_valid():
    """Test creating valid time signatures."""
    ts = TimeSignature(4, 4)
    assert ts.beats_per_measure == 4
    assert ts.note_value == 4
    
    ts2 = TimeSignature(6, 8)
    assert ts2.beats_per_measure == 6
    assert ts2.note_value == 8


def test_time_signature_invalid():
    """Test that invalid time signature is rejected."""
    with pytest.raises(ValueError, match="Invalid time signature"):
        TimeSignature(13, 16)


def test_set_creation_valid():
    """Test creating a valid set."""
    s = Set(name="My Set")
    assert s.name == "My Set"
    assert s.songs == []
    assert s.id is not None


def test_set_empty_name_rejected():
    """Test that empty set name is rejected."""
    with pytest.raises(ValueError, match="Set name cannot be empty"):
        Set(name="")


def test_playback_state_creation():
    """Test creating playback state."""
    state = PlaybackState()
    assert state.current_set_id is None
    assert state.current_song_index == 0
    assert state.is_playing is False
    assert state.current_bpm is None


def test_song_serialization():
    """Test song to_dict and from_dict."""
    ts = TimeSignature(3, 4)
    song = Song(
        title="Test Song",
        bpm=90,
        time_signature=ts,
        subdivision="double",
        accent_pattern=[True, False, False],
        click_sound="beep"
    )
    
    data = song.to_dict()
    assert data["title"] == "Test Song"
    assert data["bpm"] == 90
    assert data["timeSignature"]["beatsPerMeasure"] == 3
    
    song2 = Song.from_dict(data)
    assert song2.title == song.title
    assert song2.bpm == song.bpm
    assert song2.time_signature.beats_per_measure == song.time_signature.beats_per_measure


def test_song_subdivision_migration():
    """Test that old subdivision values are migrated on from_dict."""
    ts = TimeSignature(4, 4)
    song = Song(
        title="Migration Test",
        bpm=120,
        time_signature=ts,
        subdivision="single",
        accent_pattern=[True, False, False, False],
        click_sound="wood_block"
    )
    
    # Simulate old data with "quarter" subdivision
    data = song.to_dict()
    data["subdivision"] = "quarter"
    
    migrated = Song.from_dict(data)
    assert migrated.subdivision == "single"
    
    # Simulate old data with "eighth" subdivision
    data["subdivision"] = "eighth"
    migrated = Song.from_dict(data)
    assert migrated.subdivision == "double"
