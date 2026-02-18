# Click Track Player API Documentation

## Overview

The Click Track Player provides a RESTful API for managing songs, sets, and controlling playback. All endpoints return JSON responses and accept JSON request bodies where applicable.

**Base URL:** `http://localhost:3000/api`

**Content-Type:** `application/json`

## Authentication

Currently, the API does not require authentication. It is designed for use on a local network during live performances.

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Validation error message"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error message"
}
```

## Song Endpoints

### List All Songs

Retrieve all songs in the library.

**Endpoint:** `GET /api/songs`

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Warm Up",
    "bpm": 80,
    "timeSignature": {
      "beatsPerMeasure": 4,
      "noteValue": 4
    },
    "subdivision": "quarter",
    "accentPattern": [true, false, false, false],
    "clickSound": "wood_block",
    "volume": 70
  }
]
```

### Get Single Song

Retrieve a specific song by ID.

**Endpoint:** `GET /api/songs/{id}`

**Parameters:**
- `id` (path) - UUID of the song

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Warm Up",
  "bpm": 80,
  "timeSignature": {
    "beatsPerMeasure": 4,
    "noteValue": 4
  },
  "subdivision": "quarter",
  "accentPattern": [true, false, false, false],
  "clickSound": "wood_block",
  "volume": 70
}
```

### Create Song

Create a new song in the library.

**Endpoint:** `POST /api/songs`

**Request Body:**
```json
{
  "title": "New Song",
  "bpm": 120,
  "timeSignature": {
    "beatsPerMeasure": 4,
    "noteValue": 4
  },
  "subdivision": "quarter",
  "accentPattern": [true, false, false, false],
  "clickSound": "wood_block",
  "volume": 80
}
```

**Field Descriptions:**
- `title` (string, required) - Song name, must be non-empty
- `bpm` (number, required) - Tempo in beats per minute, must be positive
- `timeSignature` (object, required)
  - `beatsPerMeasure` (number, required) - Number of beats per measure
  - `noteValue` (number, required) - Note value (2, 4, 8, or 16)
- `subdivision` (string, required) - "quarter" or "eighth"
- `accentPattern` (array, required) - Boolean array, length must equal beatsPerMeasure
- `clickSound` (string, required) - "wood_block", "beep", or "cowbell"
- `volume` (number, required) - Volume level from 0 to 100

**Supported Time Signatures:**
- 2/4, 3/4, 4/4, 5/4 (simple meters)
- 6/8, 7/8, 9/8, 12/8 (compound meters)

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "New Song",
  "bpm": 120,
  "timeSignature": {
    "beatsPerMeasure": 4,
    "noteValue": 4
  },
  "subdivision": "quarter",
  "accentPattern": [true, false, false, false],
  "clickSound": "wood_block",
  "volume": 80
}
```

**Validation Errors:**
- Empty title: `{"error": "Title cannot be empty"}`
- Non-positive BPM: `{"error": "BPM must be a positive number"}`
- Invalid volume: `{"error": "Volume must be between 0 and 100"}`
- Invalid time signature: `{"error": "Time signature must be in format X/Y where X and Y are positive numbers"}`
- Accent pattern mismatch: `{"error": "Accent pattern length must match beats per measure"}`

### Update Song

Update an existing song's properties.

**Endpoint:** `PUT /api/songs/{id}`

**Parameters:**
- `id` (path) - UUID of the song to update

**Request Body:** (all fields optional)
```json
{
  "title": "Updated Title",
  "bpm": 140,
  "volume": 90
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Title",
  "bpm": 140,
  "timeSignature": {
    "beatsPerMeasure": 4,
    "noteValue": 4
  },
  "subdivision": "quarter",
  "accentPattern": [true, false, false, false],
  "clickSound": "wood_block",
  "volume": 90
}
```

### Delete Song

Delete a song from the library.

**Endpoint:** `DELETE /api/songs/{id}`

**Parameters:**
- `id` (path) - UUID of the song to delete

**Response:** `204 No Content`

**Note:** Deleting a song removes it from the library but does not affect sets that reference it (the song ID remains in the set's song list).

## Set Endpoints

### List All Sets

Retrieve all sets in the library.

**Endpoint:** `GET /api/sets`

**Response:** `200 OK`
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "Friday Night Gig",
    "songs": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440001"
    ]
  }
]
```

### Get Single Set

Retrieve a specific set by ID.

**Endpoint:** `GET /api/sets/{id}`

**Parameters:**
- `id` (path) - UUID of the set

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Friday Night Gig",
  "songs": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

### Create Set

Create a new empty set.

**Endpoint:** `POST /api/sets`

**Request Body:**
```json
{
  "name": "New Set"
}
```

**Field Descriptions:**
- `name` (string, required) - Set name, must be non-empty

**Response:** `201 Created`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "New Set",
  "songs": []
}
```

**Validation Errors:**
- Empty name: `{"error": "Set name cannot be empty"}`

### Update Set

Update a set's name.

**Endpoint:** `PUT /api/sets/{id}`

**Parameters:**
- `id` (path) - UUID of the set to update

**Request Body:**
```json
{
  "name": "Updated Name"
}
```

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Name",
  "songs": [
    "550e8400-e29b-41d4-a716-446655440000"
  ]
}
```

### Delete Set

Delete a set from the library.

**Endpoint:** `DELETE /api/sets/{id}`

**Parameters:**
- `id` (path) - UUID of the set to delete

**Response:** `204 No Content`

**Note:** Deleting a set does not affect the songs in the song library.

### Add Song to Set

Add a song to a set's song list.

**Endpoint:** `POST /api/sets/{id}/songs`

**Parameters:**
- `id` (path) - UUID of the set

**Request Body:**
```json
{
  "songId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Field Descriptions:**
- `songId` (string, required) - UUID of the song to add

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Friday Night Gig",
  "songs": [
    "550e8400-e29b-41d4-a716-446655440000"
  ]
}
```

**Note:** Songs are appended to the end of the set's song list.

### Remove Song from Set

Remove a song from a set's song list.

**Endpoint:** `DELETE /api/sets/{id}/songs/{songId}`

**Parameters:**
- `id` (path) - UUID of the set
- `songId` (path) - UUID of the song to remove

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Friday Night Gig",
  "songs": []
}
```

**Note:** Removing a song from a set does not delete it from the song library.

## Playback Endpoints

### Get Playback State

Retrieve the current playback state.

**Endpoint:** `GET /api/playback/state`

**Response:** `200 OK`
```json
{
  "currentSetId": "660e8400-e29b-41d4-a716-446655440000",
  "currentSongIndex": 0,
  "isPlaying": false,
  "currentBpm": 120
}
```

**Field Descriptions:**
- `currentSetId` (string|null) - UUID of the currently loaded set, or null if no set is loaded
- `currentSongIndex` (number) - Index of the current song in the set (0-based)
- `isPlaying` (boolean) - Whether a click track is currently playing
- `currentBpm` (number|null) - BPM of the current song, or null if no song is selected

### Load Set

Load a set for playback.

**Endpoint:** `POST /api/playback/load-set`

**Request Body:**
```json
{
  "setId": "660e8400-e29b-41d4-a716-446655440000"
}
```

**Field Descriptions:**
- `setId` (string, required) - UUID of the set to load

**Response:** `200 OK`
```json
{
  "currentSetId": "660e8400-e29b-41d4-a716-446655440000",
  "currentSongIndex": 0,
  "isPlaying": false,
  "currentBpm": 120
}
```

**Note:** Loading a set stops any currently playing click track and resets to the first song.

### Start Playback

Start playing the click track for the current song.

**Endpoint:** `POST /api/playback/play`

**Response:** `200 OK`
```json
{
  "currentSetId": "660e8400-e29b-41d4-a716-446655440000",
  "currentSongIndex": 0,
  "isPlaying": true,
  "currentBpm": 120
}
```

**Note:** If no set is loaded or the set is empty, this will return an error.

### Stop Playback

Stop the currently playing click track.

**Endpoint:** `POST /api/playback/stop`

**Response:** `200 OK`
```json
{
  "currentSetId": "660e8400-e29b-41d4-a716-446655440000",
  "currentSongIndex": 0,
  "isPlaying": false,
  "currentBpm": 120
}
```

### Next Song

Advance to the next song in the set.

**Endpoint:** `POST /api/playback/next`

**Response:** `200 OK`
```json
{
  "currentSetId": "660e8400-e29b-41d4-a716-446655440000",
  "currentSongIndex": 1,
  "isPlaying": false,
  "currentBpm": 140
}
```

**Note:** 
- If currently playing, playback will stop before advancing
- If already on the last song, the index will not change

### Previous Song

Go back to the previous song in the set.

**Endpoint:** `POST /api/playback/previous`

**Response:** `200 OK`
```json
{
  "currentSetId": "660e8400-e29b-41d4-a716-446655440000",
  "currentSongIndex": 0,
  "isPlaying": false,
  "currentBpm": 120
}
```

**Note:**
- If currently playing, playback will stop before going back
- If already on the first song, the index will not change

## WebSocket API

The application uses Socket.IO for real-time bidirectional communication.

**Connection URL:** `ws://localhost:3000/socket.io/`

### Client → Server Events

#### play
Start playback of the current song.

**Payload:** None

**Example:**
```javascript
socket.emit('play');
```

#### stop
Stop the currently playing click track.

**Payload:** None

**Example:**
```javascript
socket.emit('stop');
```

#### next
Advance to the next song in the set.

**Payload:** None

**Example:**
```javascript
socket.emit('next');
```

#### previous
Go back to the previous song in the set.

**Payload:** None

**Example:**
```javascript
socket.emit('previous');
```

#### load-set
Load a set for playback.

**Payload:**
```javascript
{
  setId: "660e8400-e29b-41d4-a716-446655440000"
}
```

**Example:**
```javascript
socket.emit('load-set', { setId: '660e8400-e29b-41d4-a716-446655440000' });
```

### Server → Client Events

#### playback-state-changed
Emitted when the playback state changes (play, stop, navigation).

**Payload:**
```javascript
{
  currentSetId: "660e8400-e29b-41d4-a716-446655440000",
  currentSongIndex: 0,
  isPlaying: true,
  currentBpm: 120
}
```

**Example:**
```javascript
socket.on('playback-state-changed', (state) => {
  console.log('Playback state:', state);
  updateUI(state);
});
```

#### song-updated
Emitted when a song is created or modified.

**Payload:**
```javascript
{
  id: "550e8400-e29b-41d4-a716-446655440000",
  title: "Updated Song",
  bpm: 140,
  // ... other song properties
}
```

#### song-deleted
Emitted when a song is deleted.

**Payload:**
```javascript
{
  id: "550e8400-e29b-41d4-a716-446655440000"
}
```

#### set-updated
Emitted when a set is created or modified.

**Payload:**
```javascript
{
  id: "660e8400-e29b-41d4-a716-446655440000",
  name: "Updated Set",
  songs: ["550e8400-e29b-41d4-a716-446655440000"]
}
```

#### set-deleted
Emitted when a set is deleted.

**Payload:**
```javascript
{
  id: "660e8400-e29b-41d4-a716-446655440000"
}
```

## Rate Limiting

Currently, there is no rate limiting implemented. The API is designed for local network use during live performances.

## CORS

CORS is enabled for all origins to allow access from any device on the local network.

## Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:3000/api';

// Create a song
async function createSong() {
  const response = await axios.post(`${BASE_URL}/songs`, {
    title: 'My Song',
    bpm: 120,
    timeSignature: { beatsPerMeasure: 4, noteValue: 4 },
    subdivision: 'quarter',
    accentPattern: [true, false, false, false],
    clickSound: 'wood_block',
    volume: 80
  });
  return response.data;
}

// Start playback
async function startPlayback() {
  const response = await axios.post(`${BASE_URL}/playback/play`);
  return response.data;
}
```

### Python

```python
import requests

BASE_URL = 'http://localhost:3000/api'

# Create a song
def create_song():
    response = requests.post(f'{BASE_URL}/songs', json={
        'title': 'My Song',
        'bpm': 120,
        'timeSignature': {'beatsPerMeasure': 4, 'noteValue': 4},
        'subdivision': 'quarter',
        'accentPattern': [True, False, False, False],
        'clickSound': 'wood_block',
        'volume': 80
    })
    return response.json()

# Start playback
def start_playback():
    response = requests.post(f'{BASE_URL}/playback/play')
    return response.json()
```

### cURL

```bash
# Create a song
curl -X POST http://localhost:3000/api/songs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Song",
    "bpm": 120,
    "timeSignature": {"beatsPerMeasure": 4, "noteValue": 4},
    "subdivision": "quarter",
    "accentPattern": [true, false, false, false],
    "clickSound": "wood_block",
    "volume": 80
  }'

# Start playback
curl -X POST http://localhost:3000/api/playback/play
```
