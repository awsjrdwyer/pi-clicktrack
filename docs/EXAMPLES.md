# Click Track Player Usage Examples

This document provides practical examples for common use cases of the Click Track Player.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Creating Songs](#creating-songs)
3. [Building Sets](#building-sets)
4. [Live Performance Workflows](#live-performance-workflows)
5. [API Automation](#api-automation)
6. [Advanced Configurations](#advanced-configurations)

## Basic Setup

### First-Time Setup

```bash
# Install the application
./install.sh

# Install as a system service
sudo ./install-service.sh

# Start the service
sudo systemctl start clicktrack@$USER.service

# Access the web interface
# Open browser to http://localhost:3000
```

### Creating Your First Song

1. Navigate to `http://localhost:3000/songs`
2. Click "Add Song"
3. Fill in the details:
   - Title: "Warm Up"
   - BPM: 80
   - Time Signature: 4/4
   - Subdivision: Quarter notes
   - Accent Pattern: Check first beat only
   - Click Sound: Wood block
   - Volume: 70
4. Click "Save"

### Creating Your First Set

1. Navigate to `http://localhost:3000/sets`
2. Click "Add Set"
3. Name it "Practice Session"
4. Click "Save"
5. Click on the set to open it
6. Click "Add Song" and select "Warm Up"
7. Add more songs as needed

## Creating Songs

### Example 1: Simple 4/4 Rock Song

**Via Web Interface:**
- Title: "Rock Groove"
- BPM: 120
- Time Signature: 4/4
- Subdivision: Quarter notes
- Accent Pattern: [✓] [ ] [ ] [ ] (accent on beat 1)
- Click Sound: Wood block
- Volume: 80

**Via API:**
```bash
curl -X POST http://localhost:3000/api/songs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Rock Groove",
    "bpm": 120,
    "timeSignature": {"beatsPerMeasure": 4, "noteValue": 4},
    "subdivision": "quarter",
    "accentPattern": [true, false, false, false],
    "clickSound": "wood_block",
    "volume": 80
  }'
```

### Example 2: Waltz in 3/4

**Via Web Interface:**
- Title: "Waltz"
- BPM: 180
- Time Signature: 3/4
- Subdivision: Quarter notes
- Accent Pattern: [✓] [ ] [ ] (accent on beat 1)
- Click Sound: Cowbell
- Volume: 75

**Via API:**
```bash
curl -X POST http://localhost:3000/api/songs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Waltz",
    "bpm": 180,
    "timeSignature": {"beatsPerMeasure": 3, "noteValue": 4},
    "subdivision": "quarter",
    "accentPattern": [true, false, false],
    "clickSound": "cowbell",
    "volume": 75
  }'
```

### Example 3: Complex 7/8 Time Signature

**Via Web Interface:**
- Title: "Odd Meter"
- BPM: 140
- Time Signature: 7/8
- Subdivision: Eighth notes
- Accent Pattern: [✓] [ ] [✓] [ ] [✓] [ ] [ ] (3+2+2 grouping)
- Click Sound: Beep
- Volume: 85

**Via API:**
```bash
curl -X POST http://localhost:3000/api/songs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Odd Meter",
    "bpm": 140,
    "timeSignature": {"beatsPerMeasure": 7, "noteValue": 8},
    "subdivision": "eighth",
    "accentPattern": [true, false, true, false, true, false, false],
    "clickSound": "beep",
    "volume": 85
  }'
```

### Example 4: Compound Meter (6/8)

**Via Web Interface:**
- Title: "Shuffle Feel"
- BPM: 90
- Time Signature: 6/8
- Subdivision: Eighth notes
- Accent Pattern: [✓] [ ] [ ] [✓] [ ] [ ] (two groups of three)
- Click Sound: Wood block
- Volume: 80

**Via API:**
```bash
curl -X POST http://localhost:3000/api/songs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Shuffle Feel",
    "bpm": 90,
    "timeSignature": {"beatsPerMeasure": 6, "noteValue": 8},
    "subdivision": "eighth",
    "accentPattern": [true, false, false, true, false, false],
    "clickSound": "wood_block",
    "volume": 80
  }'
```

### Example 5: Progressive Tempo Changes

Create multiple versions of the same song at different tempos for practice:

```python
import requests

BASE_URL = "http://localhost:3000/api"

# Create songs at increasing tempos
tempos = [60, 80, 100, 120, 140]
for bpm in tempos:
    requests.post(f"{BASE_URL}/songs", json={
        "title": f"Practice Exercise - {bpm} BPM",
        "bpm": bpm,
        "timeSignature": {"beatsPerMeasure": 4, "noteValue": 4},
        "subdivision": "quarter",
        "accentPattern": [True, False, False, False],
        "clickSound": "wood_block",
        "volume": 80
    })
```

## Building Sets

### Example 1: Practice Session Set

Create a set for a practice session with warm-up, exercises, and songs:

```python
import requests

BASE_URL = "http://localhost:3000/api"

# Create songs
songs = []
song_data = [
    ("Warm Up", 60),
    ("Technique Exercise", 80),
    ("Song 1", 120),
    ("Song 2", 140),
    ("Cool Down", 70)
]

for title, bpm in song_data:
    response = requests.post(f"{BASE_URL}/songs", json={
        "title": title,
        "bpm": bpm,
        "timeSignature": {"beatsPerMeasure": 4, "noteValue": 4},
        "subdivision": "quarter",
        "accentPattern": [True, False, False, False],
        "clickSound": "wood_block",
        "volume": 80
    })
    songs.append(response.json()["id"])

# Create set
response = requests.post(f"{BASE_URL}/sets", json={"name": "Practice Session"})
set_id = response.json()["id"]

# Add songs to set
for song_id in songs:
    requests.post(f"{BASE_URL}/sets/{set_id}/songs", json={"songId": song_id})

print(f"Created practice set with {len(songs)} songs")
```

### Example 2: Live Performance Set

Create a set for a live gig with proper song order:

```bash
# Create the set
SET_ID=$(curl -X POST http://localhost:3000/api/sets \
  -H "Content-Type: application/json" \
  -d '{"name": "Friday Night Gig"}' | jq -r '.id')

# Add songs in performance order
curl -X POST http://localhost:3000/api/sets/$SET_ID/songs \
  -H "Content-Type: application/json" \
  -d '{"songId": "opener-song-id"}'

curl -X POST http://localhost:3000/api/sets/$SET_ID/songs \
  -H "Content-Type: application/json" \
  -d '{"songId": "song-2-id"}'

# ... add more songs
```

### Example 3: Multiple Sets for Different Venues

```python
import requests

BASE_URL = "http://localhost:3000/api"

# Get all songs
response = requests.get(f"{BASE_URL}/songs")
all_songs = response.json()

# Create sets for different venues
venues = {
    "Small Club": ["song1", "song2", "song3"],  # 30-minute set
    "Festival": ["song1", "song2", "song3", "song4", "song5"],  # 60-minute set
    "Wedding": ["song6", "song7", "song8"]  # Special repertoire
}

for venue_name, song_titles in venues.items():
    # Create set
    response = requests.post(f"{BASE_URL}/sets", json={"name": venue_name})
    set_id = response.json()["id"]
    
    # Add songs
    for title in song_titles:
        # Find song by title
        song = next((s for s in all_songs if s["title"] == title), None)
        if song:
            requests.post(f"{BASE_URL}/sets/{set_id}/songs", 
                         json={"songId": song["id"]})
```

## Live Performance Workflows

### Workflow 1: Band Rehearsal

**Setup:**
1. Connect Raspberry Pi to PA system
2. Load rehearsal set
3. Position tablet with web interface where all band members can see

**During Rehearsal:**
```bash
# Load the rehearsal set
curl -X POST http://localhost:3000/api/playback/load-set \
  -H "Content-Type: application/json" \
  -d '{"setId": "rehearsal-set-id"}'

# Start first song
curl -X POST http://localhost:3000/api/playback/play

# When ready for next song
curl -X POST http://localhost:3000/api/playback/next
curl -X POST http://localhost:3000/api/playback/play
```

### Workflow 2: Solo Practice with MIDI Foot Controller

**Setup:**
1. Connect MIDI foot controller
2. Configure MIDI mappings
3. Load practice set

**During Practice:**
- Press foot pedal 1: Start click
- Press foot pedal 2: Stop click
- Press foot pedal 3: Next song
- Press foot pedal 4: Previous song

**Configuration:**
```yaml
midi:
  enabled: true
  mappings:
    play: 0
    stop: 1
    next: 2
    previous: 3
```

### Workflow 3: Live Performance with Drummer

**Setup:**
1. Drummer has in-ear monitors
2. MIDI foot controller at drum kit
3. Tablet with web interface for backup control

**During Performance:**
1. Load set before show starts
2. Drummer controls click with foot pedals
3. Band leader can override with tablet if needed
4. Click track only goes to drummer's in-ears

### Workflow 4: Recording Session

**Setup:**
1. Connect click to recording interface
2. Route click to headphone mix only (not recorded)
3. Load recording session set

**During Recording:**
```python
import requests
import time

BASE_URL = "http://localhost:3000/api"

# Load set
requests.post(f"{BASE_URL}/playback/load-set", 
              json={"setId": "recording-set-id"})

# For each take
for take in range(1, 4):
    print(f"Take {take}")
    
    # Start click
    requests.post(f"{BASE_URL}/playback/play")
    
    # Wait for song duration (e.g., 3 minutes)
    time.sleep(180)
    
    # Stop click
    requests.post(f"{BASE_URL}/playback/stop")
    
    # Short break
    time.sleep(30)
```

## API Automation

### Example 1: Automated Setlist Generator

Generate a setlist based on tempo progression:

```python
import requests

BASE_URL = "http://localhost:3000/api"

def create_progressive_setlist(name, start_bpm, end_bpm, steps):
    """Create a set with songs at progressively increasing tempos"""
    
    # Calculate BPM increments
    bpm_increment = (end_bpm - start_bpm) / (steps - 1)
    
    # Create songs
    song_ids = []
    for i in range(steps):
        bpm = int(start_bpm + (i * bpm_increment))
        response = requests.post(f"{BASE_URL}/songs", json={
            "title": f"Exercise {i+1} - {bpm} BPM",
            "bpm": bpm,
            "timeSignature": {"beatsPerMeasure": 4, "noteValue": 4},
            "subdivision": "quarter",
            "accentPattern": [True, False, False, False],
            "clickSound": "wood_block",
            "volume": 80
        })
        song_ids.append(response.json()["id"])
    
    # Create set
    response = requests.post(f"{BASE_URL}/sets", json={"name": name})
    set_id = response.json()["id"]
    
    # Add songs to set
    for song_id in song_ids:
        requests.post(f"{BASE_URL}/sets/{set_id}/songs", 
                     json={"songId": song_id})
    
    return set_id

# Create a progressive practice set from 60 to 120 BPM in 5 steps
set_id = create_progressive_setlist("Progressive Practice", 60, 120, 5)
print(f"Created set: {set_id}")
```

### Example 2: Backup and Restore

```python
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:3000/api"

def backup_library(filename):
    """Backup all songs and sets to a JSON file"""
    
    # Get all songs
    songs = requests.get(f"{BASE_URL}/songs").json()
    
    # Get all sets
    sets = requests.get(f"{BASE_URL}/sets").json()
    
    # Create backup
    backup = {
        "timestamp": datetime.now().isoformat(),
        "songs": songs,
        "sets": sets
    }
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(backup, f, indent=2)
    
    print(f"Backed up {len(songs)} songs and {len(sets)} sets")

def restore_library(filename):
    """Restore songs and sets from a backup file"""
    
    # Load backup
    with open(filename, 'r') as f:
        backup = json.load(f)
    
    # Restore songs
    song_id_map = {}
    for song in backup["songs"]:
        old_id = song["id"]
        del song["id"]  # Let server generate new ID
        response = requests.post(f"{BASE_URL}/songs", json=song)
        new_id = response.json()["id"]
        song_id_map[old_id] = new_id
    
    # Restore sets
    for set_data in backup["sets"]:
        # Create set
        response = requests.post(f"{BASE_URL}/sets", 
                                json={"name": set_data["name"]})
        set_id = response.json()["id"]
        
        # Add songs with updated IDs
        for old_song_id in set_data["songs"]:
            new_song_id = song_id_map.get(old_song_id)
            if new_song_id:
                requests.post(f"{BASE_URL}/sets/{set_id}/songs",
                            json={"songId": new_song_id})
    
    print(f"Restored {len(backup['songs'])} songs and {len(backup['sets'])} sets")

# Usage
backup_library("clicktrack_backup.json")
# restore_library("clicktrack_backup.json")
```

### Example 3: Batch Song Import from CSV

```python
import requests
import csv

BASE_URL = "http://localhost:3000/api"

def import_songs_from_csv(filename):
    """Import songs from a CSV file"""
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Parse accent pattern
            accent_pattern = [
                x.strip().lower() == 'true' 
                for x in row['accent_pattern'].split(',')
            ]
            
            # Create song
            song_data = {
                "title": row['title'],
                "bpm": int(row['bpm']),
                "timeSignature": {
                    "beatsPerMeasure": int(row['beats_per_measure']),
                    "noteValue": int(row['note_value'])
                },
                "subdivision": row['subdivision'],
                "accentPattern": accent_pattern,
                "clickSound": row['click_sound'],
                "volume": int(row['volume'])
            }
            
            response = requests.post(f"{BASE_URL}/songs", json=song_data)
            print(f"Created: {row['title']}")

# CSV format:
# title,bpm,beats_per_measure,note_value,subdivision,accent_pattern,click_sound,volume
# "Song 1",120,4,4,quarter,"true,false,false,false",wood_block,80
# "Song 2",140,3,4,quarter,"true,false,false",cowbell,75

import_songs_from_csv("songs.csv")
```

## Advanced Configurations

### Configuration 1: Multiple Click Sounds per Set

Create songs with different click sounds for variety:

```python
import requests

BASE_URL = "http://localhost:3000/api"

sounds = ["wood_block", "beep", "cowbell"]
song_ids = []

for i, sound in enumerate(sounds):
    response = requests.post(f"{BASE_URL}/songs", json={
        "title": f"Song with {sound}",
        "bpm": 120,
        "timeSignature": {"beatsPerMeasure": 4, "noteValue": 4},
        "subdivision": "quarter",
        "accentPattern": [True, False, False, False],
        "clickSound": sound,
        "volume": 80
    })
    song_ids.append(response.json()["id"])

# Create set with all sounds
response = requests.post(f"{BASE_URL}/sets", json={"name": "Sound Variety"})
set_id = response.json()["id"]

for song_id in song_ids:
    requests.post(f"{BASE_URL}/sets/{set_id}/songs", json={"songId": song_id})
```

### Configuration 2: Dynamic Volume Adjustment

Adjust volume for different performance contexts:

```python
import requests

BASE_URL = "http://localhost:3000/api"

def adjust_set_volume(set_id, volume_multiplier):
    """Adjust volume for all songs in a set"""
    
    # Get set
    set_data = requests.get(f"{BASE_URL}/sets/{set_id}").json()
    
    # Update each song
    for song_id in set_data["songs"]:
        song = requests.get(f"{BASE_URL}/songs/{song_id}").json()
        new_volume = min(100, int(song["volume"] * volume_multiplier))
        
        requests.put(f"{BASE_URL}/songs/{song_id}", 
                    json={"volume": new_volume})
        print(f"Updated {song['title']}: {song['volume']} -> {new_volume}")

# Make set quieter for acoustic performance
adjust_set_volume("set-id", 0.7)

# Make set louder for loud venue
adjust_set_volume("set-id", 1.3)
```

### Configuration 3: Custom Accent Patterns

Create songs with complex accent patterns:

```python
import requests

BASE_URL = "http://localhost:3000/api"

# Clave pattern in 4/4
clave_pattern = [True, False, False, True, False, False, True, False]

requests.post(f"{BASE_URL}/songs", json={
    "title": "Clave Groove",
    "bpm": 100,
    "timeSignature": {"beatsPerMeasure": 8, "noteValue": 8},
    "subdivision": "eighth",
    "accentPattern": clave_pattern,
    "clickSound": "cowbell",
    "volume": 85
})

# Polyrhythm: 3 against 4
polyrhythm_pattern = [True, False, False, True, False, False, 
                      True, False, False, True, False, False]

requests.post(f"{BASE_URL}/songs", json={
    "title": "Polyrhythm",
    "bpm": 120,
    "timeSignature": {"beatsPerMeasure": 12, "noteValue": 8},
    "subdivision": "eighth",
    "accentPattern": polyrhythm_pattern,
    "clickSound": "beep",
    "volume": 80
})
```

## Tips and Tricks

1. **Use Descriptive Names**: Name songs and sets clearly for easy identification during performances

2. **Test Before Performing**: Always test your setlist before a live performance

3. **Create Backup Sets**: Duplicate important sets in case you need to make last-minute changes

4. **Use Volume Strategically**: Adjust volume based on venue acoustics and monitoring setup

5. **Organize by Context**: Create separate sets for practice, rehearsal, and performance

6. **Document Your Setup**: Keep notes on MIDI mappings and configurations

7. **Regular Backups**: Use the backup script to save your library regularly

8. **Version Control**: Keep old versions of sets when making changes

9. **Test MIDI Thoroughly**: Verify all MIDI controls work before relying on them live

10. **Have a Backup Plan**: Always have the web interface available as a fallback
