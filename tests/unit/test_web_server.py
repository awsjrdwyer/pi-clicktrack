"""
Unit tests for the Web Server.

These tests verify the REST API endpoints for song management, set management,
and playback control.
"""

import pytest
import json
from clicktrack.web_server import WebServer
from clicktrack.song_manager import SongManager
from clicktrack.set_manager import SetManager
from clicktrack.set_screen_controller import SetScreenController
from clicktrack.playback_engine import PlaybackEngine
from clicktrack.storage import StorageManager
from clicktrack.models import TimeSignature


@pytest.fixture
def storage_manager(tmp_path):
    """Create a storage manager with temporary directory."""
    return StorageManager(str(tmp_path))


@pytest.fixture
def song_manager(storage_manager):
    """Create a song manager."""
    return SongManager(storage_manager)


@pytest.fixture
def set_manager(storage_manager):
    """Create a set manager."""
    return SetManager(storage_manager)


@pytest.fixture
def playback_engine():
    """Create a playback engine."""
    return PlaybackEngine()


@pytest.fixture
def set_screen_controller(set_manager, song_manager, playback_engine):
    """Create a set screen controller."""
    return SetScreenController(set_manager, song_manager, playback_engine)


@pytest.fixture
def web_server(song_manager, set_manager, set_screen_controller):
    """Create a web server instance."""
    server = WebServer(song_manager, set_manager, set_screen_controller)
    server.app.config['TESTING'] = True
    return server


@pytest.fixture
def client(web_server):
    """Create a test client."""
    return web_server.app.test_client()


def _song_data(**overrides):
    """Helper to build song data dict with sensible defaults."""
    data = {
        'title': 'Test Song',
        'bpm': 120,
        'timeSignature': {'beatsPerMeasure': 4, 'noteValue': 4},
        'subdivision': 'single',
        'accentPattern': [True, False, False, False],
        'clickSound': 'wood_block'
    }
    data.update(overrides)
    return data


class TestSongEndpoints:
    """Tests for song management endpoints."""
    
    def test_get_songs_empty(self, client):
        """Test getting songs when library is empty."""
        response = client.get('/api/songs')
        assert response.status_code == 200
        assert response.json == []
    
    def test_create_song(self, client):
        """Test creating a new song."""
        response = client.post('/api/songs',
                              data=json.dumps(_song_data()),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.json
        assert data['title'] == 'Test Song'
        assert data['bpm'] == 120
        assert 'id' in data
    
    def test_create_song_missing_field(self, client):
        """Test creating a song with missing required field."""
        song_data = {
            'title': 'Test Song',
            'bpm': 120
            # Missing other required fields
        }
        
        response = client.post('/api/songs',
                              data=json.dumps(song_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_create_song_invalid_bpm(self, client):
        """Test creating a song with invalid BPM."""
        response = client.post('/api/songs',
                              data=json.dumps(_song_data(bpm=-10)),
                              content_type='application/json')
        
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_get_songs_after_create(self, client):
        """Test getting songs after creating one."""
        create_response = client.post('/api/songs',
                                     data=json.dumps(_song_data()),
                                     content_type='application/json')
        assert create_response.status_code == 201
        
        response = client.get('/api/songs')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['title'] == 'Test Song'
    
    def test_update_song(self, client):
        """Test updating an existing song."""
        create_response = client.post('/api/songs',
                                     data=json.dumps(_song_data(title='Original Title')),
                                     content_type='application/json')
        song_id = create_response.json['id']
        
        update_data = {'title': 'Updated Title', 'bpm': 140}
        response = client.put(f'/api/songs/{song_id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        assert response.json['title'] == 'Updated Title'
        assert response.json['bpm'] == 140
    
    def test_delete_song(self, client):
        """Test deleting a song."""
        create_response = client.post('/api/songs',
                                     data=json.dumps(_song_data()),
                                     content_type='application/json')
        song_id = create_response.json['id']
        
        response = client.delete(f'/api/songs/{song_id}')
        assert response.status_code == 204
        
        get_response = client.get('/api/songs')
        assert len(get_response.json) == 0
    
    def test_delete_nonexistent_song(self, client):
        """Test deleting a song that doesn't exist."""
        response = client.delete('/api/songs/nonexistent-id')
        assert response.status_code == 404


class TestSetEndpoints:
    """Tests for set management endpoints."""
    
    def test_get_sets_empty(self, client):
        """Test getting sets when library is empty."""
        response = client.get('/api/sets')
        assert response.status_code == 200
        assert response.json == []
    
    def test_create_set(self, client):
        """Test creating a new set."""
        response = client.post('/api/sets',
                              data=json.dumps({'name': 'Test Set'}),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.json
        assert data['name'] == 'Test Set'
        assert 'id' in data
        assert data['songs'] == []
    
    def test_create_set_missing_name(self, client):
        """Test creating a set without a name."""
        response = client.post('/api/sets',
                              data=json.dumps({}),
                              content_type='application/json')
        
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_update_set(self, client):
        """Test updating a set."""
        create_response = client.post('/api/sets',
                                     data=json.dumps({'name': 'Original Name'}),
                                     content_type='application/json')
        set_id = create_response.json['id']
        
        response = client.put(f'/api/sets/{set_id}',
                             data=json.dumps({'name': 'Updated Name'}),
                             content_type='application/json')
        
        assert response.status_code == 200
        assert response.json['name'] == 'Updated Name'
    
    def test_delete_set(self, client):
        """Test deleting a set."""
        create_response = client.post('/api/sets',
                                     data=json.dumps({'name': 'Test Set'}),
                                     content_type='application/json')
        set_id = create_response.json['id']
        
        response = client.delete(f'/api/sets/{set_id}')
        assert response.status_code == 204
        
        get_response = client.get('/api/sets')
        assert len(get_response.json) == 0
    
    def test_add_song_to_set(self, client):
        """Test adding a song to a set."""
        song_response = client.post('/api/songs',
                                   data=json.dumps(_song_data()),
                                   content_type='application/json')
        song_id = song_response.json['id']
        
        set_response = client.post('/api/sets',
                                  data=json.dumps({'name': 'Test Set'}),
                                  content_type='application/json')
        set_id = set_response.json['id']
        
        response = client.post(f'/api/sets/{set_id}/songs',
                              data=json.dumps({'songId': song_id}),
                              content_type='application/json')
        
        assert response.status_code == 200
        assert song_id in response.json['songs']
    
    def test_remove_song_from_set(self, client):
        """Test removing a song from a set."""
        song_response = client.post('/api/songs',
                                   data=json.dumps(_song_data()),
                                   content_type='application/json')
        song_id = song_response.json['id']
        
        set_response = client.post('/api/sets',
                                  data=json.dumps({'name': 'Test Set'}),
                                  content_type='application/json')
        set_id = set_response.json['id']
        
        client.post(f'/api/sets/{set_id}/songs',
                   data=json.dumps({'songId': song_id}),
                   content_type='application/json')
        
        response = client.delete(f'/api/sets/{set_id}/songs/{song_id}')
        
        assert response.status_code == 200
        assert song_id not in response.json['songs']


class TestPlaybackEndpoints:
    """Tests for playback control endpoints."""
    
    def test_get_playback_state_initial(self, client):
        """Test getting initial playback state."""
        response = client.get('/api/playback/state')
        assert response.status_code == 200
        data = response.json
        assert data['currentSetId'] is None
        assert data['isPlaying'] is False
    
    def test_load_set(self, client):
        """Test loading a set for playback."""
        set_response = client.post('/api/sets',
                                  data=json.dumps({'name': 'Test Set'}),
                                  content_type='application/json')
        set_id = set_response.json['id']
        
        response = client.post('/api/playback/load-set',
                              data=json.dumps({'setId': set_id}),
                              content_type='application/json')
        
        assert response.status_code == 200
        assert response.json['currentSetId'] == set_id
    
    def test_play_without_loaded_set(self, client):
        """Test playing without a loaded set."""
        response = client.post('/api/playback/play')
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_stop_playback(self, client):
        """Test stopping playback."""
        response = client.post('/api/playback/stop')
        assert response.status_code == 200
    
    def test_next_without_loaded_set(self, client):
        """Test next without a loaded set."""
        response = client.post('/api/playback/next')
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_previous_without_loaded_set(self, client):
        """Test previous without a loaded set."""
        response = client.post('/api/playback/previous')
        assert response.status_code == 400
        assert 'error' in response.json


class TestMIDIIntegration:
    """Test suite for MIDI handler integration with WebServer."""
    
    def test_web_server_with_midi_handler(self, song_manager, set_manager, set_screen_controller):
        """Test that WebServer can be initialized with a MIDI handler."""
        from clicktrack.midi_handler import MIDIHandler
        from unittest.mock import Mock
        
        midi_handler = Mock(spec=MIDIHandler)
        web_server = WebServer(
            song_manager=song_manager,
            set_manager=set_manager,
            set_screen_controller=set_screen_controller,
            midi_handler=midi_handler
        )
        
        assert web_server.midi_handler == midi_handler
    
    def test_web_server_without_midi_handler(self, song_manager, set_manager, set_screen_controller):
        """Test that WebServer works without a MIDI handler."""
        web_server = WebServer(
            song_manager=song_manager,
            set_manager=set_manager,
            set_screen_controller=set_screen_controller,
            midi_handler=None
        )
        
        assert web_server.midi_handler is None
    
    def test_midi_callbacks_wired_correctly(self, song_manager, set_manager, set_screen_controller):
        """Test that MIDI callbacks are wired to SetScreenController methods."""
        from clicktrack.midi_handler import MIDIHandler
        from unittest.mock import Mock
        
        midi_handler = Mock(spec=MIDIHandler)
        WebServer(
            song_manager=song_manager,
            set_manager=set_manager,
            set_screen_controller=set_screen_controller,
            midi_handler=midi_handler
        )
        
        assert midi_handler.on_play_command.called
        assert midi_handler.on_stop_command.called
        assert midi_handler.on_next_command.called
        assert midi_handler.on_previous_command.called
    
    def test_midi_play_command_triggers_websocket_event(
        self, song_manager, set_manager, set_screen_controller
    ):
        """Test that MIDI play command triggers WebSocket event."""
        from clicktrack.midi_handler import MIDIHandler
        from unittest.mock import patch
        
        midi_handler = MIDIHandler()
        web_server = WebServer(
            song_manager=song_manager,
            set_manager=set_manager,
            set_screen_controller=set_screen_controller,
            midi_handler=midi_handler
        )
        
        song = song_manager.create_song(
            title="Test Song",
            bpm=120,
            time_signature=TimeSignature(4, 4),
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block"
        )
        test_set = set_manager.create_set("Test Set")
        set_manager.add_song_to_set(test_set.id, song.id)
        set_screen_controller.load_set(test_set.id)
        
        with patch.object(web_server, 'emit_playback_state_changed') as mock_emit:
            midi_handler._play_callback()
            mock_emit.assert_called_once()
    
    def test_midi_stop_command_triggers_websocket_event(
        self, song_manager, set_manager, set_screen_controller
    ):
        """Test that MIDI stop command triggers WebSocket event."""
        from clicktrack.midi_handler import MIDIHandler
        from unittest.mock import patch
        
        midi_handler = MIDIHandler()
        web_server = WebServer(
            song_manager=song_manager,
            set_manager=set_manager,
            set_screen_controller=set_screen_controller,
            midi_handler=midi_handler
        )
        
        with patch.object(web_server, 'emit_playback_state_changed') as mock_emit:
            midi_handler._stop_callback()
            mock_emit.assert_called_once()
    
    def test_midi_next_command_triggers_websocket_event(
        self, song_manager, set_manager, set_screen_controller
    ):
        """Test that MIDI next command triggers WebSocket event."""
        from clicktrack.midi_handler import MIDIHandler
        from unittest.mock import patch
        
        midi_handler = MIDIHandler()
        web_server = WebServer(
            song_manager=song_manager,
            set_manager=set_manager,
            set_screen_controller=set_screen_controller,
            midi_handler=midi_handler
        )
        
        song1 = song_manager.create_song(
            title="Song 1", bpm=120,
            time_signature=TimeSignature(4, 4),
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block"
        )
        song2 = song_manager.create_song(
            title="Song 2", bpm=140,
            time_signature=TimeSignature(4, 4),
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="beep"
        )
        test_set = set_manager.create_set("Test Set")
        set_manager.add_song_to_set(test_set.id, song1.id)
        set_manager.add_song_to_set(test_set.id, song2.id)
        set_screen_controller.load_set(test_set.id)
        
        with patch.object(web_server, 'emit_playback_state_changed') as mock_emit:
            midi_handler._next_callback()
            mock_emit.assert_called_once()
    
    def test_midi_previous_command_triggers_websocket_event(
        self, song_manager, set_manager, set_screen_controller
    ):
        """Test that MIDI previous command triggers WebSocket event."""
        from clicktrack.midi_handler import MIDIHandler
        from unittest.mock import patch
        
        midi_handler = MIDIHandler()
        web_server = WebServer(
            song_manager=song_manager,
            set_manager=set_manager,
            set_screen_controller=set_screen_controller,
            midi_handler=midi_handler
        )
        
        song1 = song_manager.create_song(
            title="Song 1", bpm=120,
            time_signature=TimeSignature(4, 4),
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="wood_block"
        )
        song2 = song_manager.create_song(
            title="Song 2", bpm=140,
            time_signature=TimeSignature(4, 4),
            subdivision="single",
            accent_pattern=[True, False, False, False],
            click_sound="beep"
        )
        test_set = set_manager.create_set("Test Set")
        set_manager.add_song_to_set(test_set.id, song1.id)
        set_manager.add_song_to_set(test_set.id, song2.id)
        set_screen_controller.load_set(test_set.id)
        
        set_screen_controller.next_song()
        
        with patch.object(web_server, 'emit_playback_state_changed') as mock_emit:
            midi_handler._previous_callback()
            mock_emit.assert_called_once()
