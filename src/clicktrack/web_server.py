"""
Web Server for the Click Track Player application.

This module provides a Flask-based REST API for managing songs, sets,
and playback control. It exposes HTTP endpoints for CRUD operations
and integrates with the Song Manager, Set Manager, and Set Screen Controller.
It also provides WebSocket support for real-time updates.
"""

import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from typing import Optional

from clicktrack.song_manager import SongManager
from clicktrack.set_manager import SetManager
from clicktrack.set_screen_controller import SetScreenController
from clicktrack.models import TimeSignature
from clicktrack.midi_handler import MIDIHandler

logger = logging.getLogger(__name__)


class WebServer:
    """
    Flask-based web server providing REST API and WebSocket support for the Click Track Player.
    
    This server exposes endpoints for:
    - Song management (CRUD operations)
    - Set management (CRUD operations)
    - Playback control (play, stop, next, previous, load set)
    - Real-time updates via WebSocket
    """
    
    def __init__(
        self,
        song_manager: SongManager,
        set_manager: SetManager,
        set_screen_controller: SetScreenController,
        midi_handler: Optional[MIDIHandler] = None,
        host: str = "0.0.0.0",
        port: int = 3000
    ):
        """
        Initialize the web server.
        
        Args:
            song_manager: SongManager instance
            set_manager: SetManager instance
            set_screen_controller: SetScreenController instance
            midi_handler: Optional MIDIHandler instance for MIDI integration
            host: Host address to bind to (default: 0.0.0.0)
            port: Port to listen on (default: 3000)
        """
        self.song_manager = song_manager
        self.set_manager = set_manager
        self.set_screen_controller = set_screen_controller
        self.midi_handler = midi_handler
        self.host = host
        self.port = port
        
        # Create Flask app with template folder
        import os
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates')
        self.app = Flask(__name__, template_folder=template_dir)
        
        # Enable CORS for all routes
        CORS(self.app)
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Register routes
        self._register_routes()
        
        # Register WebSocket event handlers
        self._register_socketio_handlers()
        
        # Wire MIDI callbacks if MIDI handler is provided
        if self.midi_handler:
            self._wire_midi_callbacks()
        
        # Wire beat callback for visual flash on play page
        self._wire_beat_callback()
        
        logger.info(f"WebServer initialized on {host}:{port} with WebSocket support")
    
    def _register_routes(self):
        """Register all API routes."""
        
        # HTML page routes
        self.app.route('/')(self.index)
        self.app.route('/songs')(self.songs_page)
        self.app.route('/sets')(self.sets_page)
        self.app.route('/play')(self.play_page)
        self.app.route('/favicon.svg')(self.favicon)
        self.app.route('/assets/socket.io.min.js')(self.serve_socketio_js)
        
        # Song endpoints
        self.app.route('/api/songs', methods=['GET'])(self.get_songs)
        self.app.route('/api/songs', methods=['POST'])(self.create_song)
        self.app.route('/api/songs/<song_id>', methods=['PUT'])(self.update_song)
        self.app.route('/api/songs/<song_id>', methods=['DELETE'])(self.delete_song)
        
        # Set endpoints
        self.app.route('/api/sets', methods=['GET'])(self.get_sets)
        self.app.route('/api/sets', methods=['POST'])(self.create_set)
        self.app.route('/api/sets/<set_id>', methods=['PUT'])(self.update_set)
        self.app.route('/api/sets/<set_id>', methods=['DELETE'])(self.delete_set)
        self.app.route('/api/sets/<set_id>/songs', methods=['POST'])(self.add_song_to_set)
        self.app.route('/api/sets/<set_id>/songs/<song_id>', methods=['DELETE'])(self.remove_song_from_set)
        self.app.route('/api/sets/<set_id>/reorder', methods=['PUT'])(self.reorder_set_songs)
        
        # Playback control endpoints
        self.app.route('/api/playback/state', methods=['GET'])(self.get_playback_state)
        self.app.route('/api/playback/play', methods=['POST'])(self.playback_play)
        self.app.route('/api/playback/stop', methods=['POST'])(self.playback_stop)
        self.app.route('/api/playback/next', methods=['POST'])(self.playback_next)
        self.app.route('/api/playback/previous', methods=['POST'])(self.playback_previous)
        self.app.route('/api/playback/jump-to-song', methods=['POST'])(self.playback_jump_to_song)
        self.app.route('/api/playback/load-set', methods=['POST'])(self.playback_load_set)
    
    def _register_socketio_handlers(self):
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info("Client connected via WebSocket")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info("Client disconnected from WebSocket")
        
        @self.socketio.on('play')
        def handle_play():
            """Handle play command from WebSocket client."""
            try:
                self.set_screen_controller.play()
                state = self.set_screen_controller.get_playback_state()
                # Emit playback state change to all clients
                self.socketio.emit('playback-state-changed', state.to_dict())
                logger.info("Play command received via WebSocket")
            except Exception as e:
                logger.error(f"Error handling play command: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('stop')
        def handle_stop():
            """Handle stop command from WebSocket client."""
            try:
                self.set_screen_controller.stop()
                state = self.set_screen_controller.get_playback_state()
                # Emit playback state change to all clients
                self.socketio.emit('playback-state-changed', state.to_dict())
                logger.info("Stop command received via WebSocket")
            except Exception as e:
                logger.error(f"Error handling stop command: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('next')
        def handle_next():
            """Handle next song command from WebSocket client."""
            try:
                self.set_screen_controller.next_song()
                state = self.set_screen_controller.get_playback_state()
                # Emit playback state change to all clients
                self.socketio.emit('playback-state-changed', state.to_dict())
                logger.info("Next song command received via WebSocket")
            except Exception as e:
                logger.error(f"Error handling next command: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('previous')
        def handle_previous():
            """Handle previous song command from WebSocket client."""
            try:
                self.set_screen_controller.previous_song()
                state = self.set_screen_controller.get_playback_state()
                # Emit playback state change to all clients
                self.socketio.emit('playback-state-changed', state.to_dict())
                logger.info("Previous song command received via WebSocket")
            except Exception as e:
                logger.error(f"Error handling previous command: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('load-set')
        def handle_load_set(data):
            """Handle load set command from WebSocket client."""
            try:
                if 'setId' not in data:
                    emit('error', {'message': 'Missing required field: setId'})
                    return
                
                self.set_screen_controller.load_set(data['setId'])
                state = self.set_screen_controller.get_playback_state()
                # Emit playback state change to all clients
                self.socketio.emit('playback-state-changed', state.to_dict())
                logger.info(f"Load set command received via WebSocket: {data['setId']}")
            except Exception as e:
                logger.error(f"Error handling load-set command: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('jump-to-song')
        def handle_jump_to_song(data):
            """Handle jump to song command from WebSocket client."""
            try:
                if 'songIndex' not in data:
                    emit('error', {'message': 'Missing required field: songIndex'})
                    return
                
                self.set_screen_controller.jump_to_song(data['songIndex'])
                state = self.set_screen_controller.get_playback_state()
                # Emit playback state change to all clients
                self.socketio.emit('playback-state-changed', state.to_dict())
                logger.info(f"Jump to song command received via WebSocket: index {data['songIndex']}")
            except Exception as e:
                logger.error(f"Error handling jump-to-song command: {e}")
                emit('error', {'message': str(e)})
    
    def _wire_midi_callbacks(self):
        """
        Wire MIDI handler callbacks to SetScreenController methods and WebSocket events.
        
        This method connects MIDI commands to the application logic and ensures
        that WebSocket events are emitted when MIDI commands are received, keeping
        the web UI synchronized with MIDI control actions.
        """
        def handle_midi_play():
            """Handle MIDI play command."""
            try:
                self.set_screen_controller.play()
                # Emit WebSocket event to update all connected clients
                self.emit_playback_state_changed()
                logger.info("MIDI play command executed")
            except Exception as e:
                logger.error(f"Error handling MIDI play command: {e}")
        
        def handle_midi_stop():
            """Handle MIDI stop command."""
            try:
                self.set_screen_controller.stop()
                # Emit WebSocket event to update all connected clients
                self.emit_playback_state_changed()
                logger.info("MIDI stop command executed")
            except Exception as e:
                logger.error(f"Error handling MIDI stop command: {e}")
        
        def handle_midi_next():
            """Handle MIDI next song command."""
            try:
                self.set_screen_controller.next_song()
                # Emit WebSocket event to update all connected clients
                self.emit_playback_state_changed()
                logger.info("MIDI next command executed")
            except Exception as e:
                logger.error(f"Error handling MIDI next command: {e}")
        
        def handle_midi_previous():
            """Handle MIDI previous song command."""
            try:
                self.set_screen_controller.previous_song()
                # Emit WebSocket event to update all connected clients
                self.emit_playback_state_changed()
                logger.info("MIDI previous command executed")
            except Exception as e:
                logger.error(f"Error handling MIDI previous command: {e}")
        
        # Register callbacks with MIDI handler
        self.midi_handler.on_play_command(handle_midi_play)
        self.midi_handler.on_stop_command(handle_midi_stop)
        self.midi_handler.on_next_command(handle_midi_next)
        self.midi_handler.on_previous_command(handle_midi_previous)
        
        logger.info("MIDI callbacks wired to SetScreenController and WebSocket events")

    def _wire_beat_callback(self):
        """Wire playback engine beat callback to emit WebSocket beat events."""
        def handle_beat(beat_info):
            try:
                self.socketio.emit('beat', beat_info)
            except Exception:
                pass  # Don't let emit errors affect playback timing
        
        self.set_screen_controller.playback_engine.on_beat(handle_beat)
        logger.info("Beat callback wired for visual sync")

    
    # HTML page routes
    
    def index(self):
        """Redirect to songs page."""
        from flask import redirect
        return redirect('songs')
    
    def songs_page(self):
        """Render songs management page."""
        return render_template('songs.html')
    
    def sets_page(self):
        """Render sets management page."""
        return render_template('sets.html')
    
    def play_page(self):
        """Render set screen (playback control) page."""
        return render_template('play.html')
    
    def favicon(self):
        """Serve the favicon."""
        return render_template('favicon.svg'), 200, {'Content-Type': 'image/svg+xml'}
    
    def serve_socketio_js(self):
        """Serve the bundled Socket.IO client library."""
        import os
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets')
        js_path = os.path.join(assets_dir, 'socket.io.min.js')
        with open(js_path, 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'application/javascript', 'Cache-Control': 'public, max-age=86400'}
    
    # Helper methods for emitting WebSocket events
    
    def emit_song_updated(self, song_id: str):
        """Emit song-updated event to all connected clients."""
        try:
            song = self.song_manager.get_song(song_id)
            if song:
                self.socketio.emit('song-updated', song.to_dict())
                logger.debug(f"Emitted song-updated event for song {song_id}")
        except Exception as e:
            logger.error(f"Error emitting song-updated event: {e}")
    
    def emit_song_deleted(self, song_id: str):
        """Emit song-deleted event to all connected clients."""
        try:
            self.socketio.emit('song-deleted', {'id': song_id})
            logger.debug(f"Emitted song-deleted event for song {song_id}")
        except Exception as e:
            logger.error(f"Error emitting song-deleted event: {e}")
    
    def emit_set_updated(self, set_id: str):
        """Emit set-updated event to all connected clients."""
        try:
            set_obj = self.set_manager.get_set(set_id)
            if set_obj:
                self.socketio.emit('set-updated', set_obj.to_dict())
                logger.debug(f"Emitted set-updated event for set {set_id}")
        except Exception as e:
            logger.error(f"Error emitting set-updated event: {e}")
    
    def emit_set_deleted(self, set_id: str):
        """Emit set-deleted event to all connected clients."""
        try:
            self.socketio.emit('set-deleted', {'id': set_id})
            logger.debug(f"Emitted set-deleted event for set {set_id}")
        except Exception as e:
            logger.error(f"Error emitting set-deleted event: {e}")
    
    def emit_playback_state_changed(self):
        """Emit playback-state-changed event to all connected clients."""
        try:
            state = self.set_screen_controller.get_playback_state()
            self.socketio.emit('playback-state-changed', state.to_dict())
            logger.debug("Emitted playback-state-changed event")
        except Exception as e:
            logger.error(f"Error emitting playback-state-changed event: {e}")
    
    # Song endpoints
    
    def get_songs(self):
        """GET /api/songs - List all songs."""
        try:
            songs = self.song_manager.get_all_songs()
            return jsonify([song.to_dict() for song in songs]), 200
        except Exception as e:
            logger.error(f"Error getting songs: {e}")
            return jsonify({"error": str(e)}), 500
    
    def create_song(self):
        """POST /api/songs - Create a new song."""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['title', 'bpm', 'timeSignature', 'subdivision', 'accentPattern', 'clickSound']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Parse time signature
            time_sig_data = data['timeSignature']
            time_signature = TimeSignature(
                beats_per_measure=time_sig_data['beatsPerMeasure'],
                note_value=time_sig_data['noteValue']
            )
            
            # Create song
            song = self.song_manager.create_song(
                title=data['title'],
                bpm=data['bpm'],
                time_signature=time_signature,
                subdivision=data['subdivision'],
                accent_pattern=data['accentPattern'],
                click_sound=data['clickSound']
            )
            
            # Emit WebSocket event
            self.emit_song_updated(song.id)
            
            return jsonify(song.to_dict()), 201
        
        except ValueError as e:
            logger.warning(f"Validation error creating song: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error creating song: {e}")
            return jsonify({"error": str(e)}), 500
    
    def update_song(self, song_id: str):
        """PUT /api/songs/:id - Update an existing song."""
        try:
            data = request.get_json()
            
            # Parse optional time signature
            time_signature = None
            if 'timeSignature' in data:
                time_sig_data = data['timeSignature']
                time_signature = TimeSignature(
                    beats_per_measure=time_sig_data['beatsPerMeasure'],
                    note_value=time_sig_data['noteValue']
                )
            
            # Update song
            song = self.song_manager.update_song(
                song_id=song_id,
                title=data.get('title'),
                bpm=data.get('bpm'),
                time_signature=time_signature,
                subdivision=data.get('subdivision'),
                accent_pattern=data.get('accentPattern'),
                click_sound=data.get('clickSound')
            )
            
            # Emit WebSocket event
            self.emit_song_updated(song_id)
            
            return jsonify(song.to_dict()), 200
        
        except ValueError as e:
            logger.warning(f"Validation error updating song {song_id}: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error updating song {song_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    def delete_song(self, song_id: str):
        """DELETE /api/songs/:id - Delete a song."""
        try:
            self.song_manager.delete_song(song_id)
            
            # Emit WebSocket event
            self.emit_song_deleted(song_id)
            
            return '', 204
        
        except ValueError as e:
            logger.warning(f"Error deleting song {song_id}: {e}")
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            logger.error(f"Error deleting song {song_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Set endpoints
    
    def get_sets(self):
        """GET /api/sets - List all sets."""
        try:
            sets = self.set_manager.get_all_sets()
            return jsonify([s.to_dict() for s in sets]), 200
        except Exception as e:
            logger.error(f"Error getting sets: {e}")
            return jsonify({"error": str(e)}), 500
    
    def create_set(self):
        """POST /api/sets - Create a new set."""
        try:
            data = request.get_json()
            
            # Validate required fields
            if 'name' not in data:
                return jsonify({"error": "Missing required field: name"}), 400
            
            # Create set
            new_set = self.set_manager.create_set(name=data['name'])
            
            # Emit WebSocket event
            self.emit_set_updated(new_set.id)
            
            return jsonify(new_set.to_dict()), 201
        
        except ValueError as e:
            logger.warning(f"Validation error creating set: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error creating set: {e}")
            return jsonify({"error": str(e)}), 500
    
    def update_set(self, set_id: str):
        """PUT /api/sets/:id - Update an existing set."""
        try:
            data = request.get_json()
            
            # Validate required fields
            if 'name' not in data:
                return jsonify({"error": "Missing required field: name"}), 400
            
            # Update set
            updated_set = self.set_manager.update_set(set_id=set_id, name=data['name'])
            
            # Emit WebSocket event
            self.emit_set_updated(set_id)
            
            return jsonify(updated_set.to_dict()), 200
        
        except ValueError as e:
            logger.warning(f"Validation error updating set {set_id}: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error updating set {set_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    def delete_set(self, set_id: str):
        """DELETE /api/sets/:id - Delete a set."""
        try:
            self.set_manager.delete_set(set_id)
            
            # Emit WebSocket event
            self.emit_set_deleted(set_id)
            
            return '', 204
        
        except ValueError as e:
            logger.warning(f"Error deleting set {set_id}: {e}")
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            logger.error(f"Error deleting set {set_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    def add_song_to_set(self, set_id: str):
        """POST /api/sets/:id/songs - Add a song to a set."""
        try:
            data = request.get_json()
            
            # Validate required fields
            if 'songId' not in data:
                return jsonify({"error": "Missing required field: songId"}), 400
            
            # Add song to set
            self.set_manager.add_song_to_set(set_id=set_id, song_id=data['songId'])
            
            # Emit WebSocket event
            self.emit_set_updated(set_id)
            
            # Return updated set
            updated_set = self.set_manager.get_set(set_id)
            return jsonify(updated_set.to_dict()), 200
        
        except ValueError as e:
            logger.warning(f"Error adding song to set {set_id}: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error adding song to set {set_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    def remove_song_from_set(self, set_id: str, song_id: str):
        """DELETE /api/sets/:id/songs/:songId - Remove a song from a set."""
        try:
            # Check for song_index query param (for duplicate song handling)
            song_index = request.args.get('index', None, type=int)
            self.set_manager.remove_song_from_set(set_id=set_id, song_id=song_id, song_index=song_index)
            
            # Emit WebSocket event
            self.emit_set_updated(set_id)
            
            # Return updated set
            updated_set = self.set_manager.get_set(set_id)
            return jsonify(updated_set.to_dict()), 200
        
        except ValueError as e:
            logger.warning(f"Error removing song {song_id} from set {set_id}: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error removing song {song_id} from set {set_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Playback control endpoints
    
    def reorder_set_songs(self, set_id: str):
        """PUT /api/sets/:id/reorder - Reorder songs in a set."""
        try:
            data = request.get_json()
            song_ids = data.get('songs', [])
            
            self.set_manager.reorder_songs(set_id=set_id, song_ids=song_ids)
            
            # Emit WebSocket event
            self.emit_set_updated(set_id)
            
            updated_set = self.set_manager.get_set(set_id)
            return jsonify(updated_set.to_dict()), 200
        
        except ValueError as e:
            logger.warning(f"Error reordering songs in set {set_id}: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error reordering songs in set {set_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    def get_playback_state(self):
        """GET /api/playback/state - Get current playback state."""
        try:
            state = self.set_screen_controller.get_playback_state()
            return jsonify(state.to_dict()), 200
        except Exception as e:
            logger.error(f"Error getting playback state: {e}")
            return jsonify({"error": str(e)}), 500
    
    def playback_play(self):
        """POST /api/playback/play - Start playback."""
        try:
            self.set_screen_controller.play()
            state = self.set_screen_controller.get_playback_state()
            
            # Emit WebSocket event
            self.emit_playback_state_changed()
            
            return jsonify(state.to_dict()), 200
        
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Error starting playback: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            return jsonify({"error": str(e)}), 500
    
    def playback_stop(self):
        """POST /api/playback/stop - Stop playback."""
        try:
            self.set_screen_controller.stop()
            state = self.set_screen_controller.get_playback_state()
            
            # Emit WebSocket event
            self.emit_playback_state_changed()
            
            return jsonify(state.to_dict()), 200
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return jsonify({"error": str(e)}), 500
    
    def playback_next(self):
        """POST /api/playback/next - Navigate to next song."""
        try:
            self.set_screen_controller.next_song()
            state = self.set_screen_controller.get_playback_state()
            
            # Emit WebSocket event
            self.emit_playback_state_changed()
            
            return jsonify(state.to_dict()), 200
        
        except RuntimeError as e:
            logger.warning(f"Error navigating to next song: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error navigating to next song: {e}")
            return jsonify({"error": str(e)}), 500
    
    def playback_previous(self):
        """POST /api/playback/previous - Navigate to previous song."""
        try:
            self.set_screen_controller.previous_song()
            state = self.set_screen_controller.get_playback_state()
            
            # Emit WebSocket event
            self.emit_playback_state_changed()
            
            return jsonify(state.to_dict()), 200
        
        except RuntimeError as e:
            logger.warning(f"Error navigating to previous song: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error navigating to previous song: {e}")
            return jsonify({"error": str(e)}), 500
    
    def playback_jump_to_song(self):
        """POST /api/playback/jump-to-song - Jump to a specific song by index."""
        try:
            data = request.get_json()
            
            # Validate required fields
            if 'songIndex' not in data:
                return jsonify({"error": "Missing required field: songIndex"}), 400
            
            # Jump to song
            self.set_screen_controller.jump_to_song(data['songIndex'])
            state = self.set_screen_controller.get_playback_state()
            
            # Emit WebSocket event
            self.emit_playback_state_changed()
            
            return jsonify(state.to_dict()), 200
        
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Error jumping to song: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error jumping to song: {e}")
            return jsonify({"error": str(e)}), 500
    
    def playback_load_set(self):
        """POST /api/playback/load-set - Load a set for playback."""
        try:
            data = request.get_json()
            
            # Validate required fields
            if 'setId' not in data:
                return jsonify({"error": "Missing required field: setId"}), 400
            
            # Load set
            self.set_screen_controller.load_set(data['setId'])
            state = self.set_screen_controller.get_playback_state()
            
            # Emit WebSocket event
            self.emit_playback_state_changed()
            
            return jsonify(state.to_dict()), 200
        
        except ValueError as e:
            logger.warning(f"Error loading set: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error loading set: {e}")
            return jsonify({"error": str(e)}), 500
    
    def run(self, debug: bool = False):
        """
        Start the Flask web server with WebSocket support.
        
        Args:
            debug: Enable debug mode (default: False)
            
        Raises:
            OSError: If the port is already in use and no alternative ports are available
        """
        logger.info(f"Starting web server with WebSocket support on {self.host}:{self.port}")
        
        # Try the configured port first, then try alternatives if it fails
        ports_to_try = [self.port, 3001, 3002, 3003]
        last_error = None
        
        for port in ports_to_try:
            try:
                logger.info(f"Attempting to start server on port {port}...")
                # Note: allow_unsafe_werkzeug=True is required for Flask-SocketIO 5.x+
                # This is acceptable for local network use on a Raspberry Pi
                self.socketio.run(
                    self.app, 
                    host=self.host, 
                    port=port, 
                    debug=debug,
                    allow_unsafe_werkzeug=True
                )
                return  # Success - server is running
            except OSError as e:
                if "Address already in use" in str(e) or "Only one usage" in str(e):
                    logger.warning(f"Port {port} is already in use")
                    last_error = e
                    if port == ports_to_try[-1]:
                        # This was the last port to try
                        logger.error(f"All ports exhausted. Tried: {ports_to_try}")
                        raise OSError(f"Unable to start server. All ports in use: {ports_to_try}") from e
                    # Try next port
                    continue
                else:
                    # Different OSError - re-raise immediately
                    logger.error(f"Network error starting server on port {port}: {e}", exc_info=True)
                    raise
            except Exception as e:
                logger.error(f"Unexpected error starting server on port {port}: {e}", exc_info=True)
                raise
