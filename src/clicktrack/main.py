"""
Main application entry point for Click Track Player.

This module initializes all components and starts the web server.
It coordinates the startup sequence, loads configuration, and ensures
all managers and controllers are properly initialized.
"""

import logging
import sys
import signal
from pathlib import Path
from typing import Optional

from clicktrack.logging_config import setup_logging
from clicktrack.storage import StorageManager
from clicktrack.song_manager import SongManager
from clicktrack.set_manager import SetManager
from clicktrack.playback_engine import PlaybackEngine
from clicktrack.set_screen_controller import SetScreenController
from clicktrack.midi_handler import MIDIHandler
from clicktrack.web_server import WebServer

logger = logging.getLogger(__name__)


class ClickTrackApplication:
    """
    Main application class that coordinates all components.
    
    This class handles:
    - Component initialization
    - Configuration loading
    - Graceful shutdown
    - Error handling during startup
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Click Track Player application.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = None
        
        # Components (initialized in start())
        self.storage_manager: Optional[StorageManager] = None
        self.song_manager: Optional[SongManager] = None
        self.set_manager: Optional[SetManager] = None
        self.playback_engine: Optional[PlaybackEngine] = None
        self.set_screen_controller: Optional[SetScreenController] = None
        self.midi_handler: Optional[MIDIHandler] = None
        self.web_server: Optional[WebServer] = None
        
        logger.info("ClickTrackApplication instance created")
    
    def load_configuration(self):
        """
        Load application configuration from file.
        
        If no configuration file is provided or found, uses sensible defaults.
        """
        if self.config_path:
            config_file = Path(self.config_path)
        else:
            # Default config location
            config_file = Path.home() / '.clicktrack' / 'config.yaml'
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_file}")
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML in configuration file {config_file}: {e}")
                logger.info("Using default configuration")
                self.config = self._get_default_config()
            except IOError as e:
                logger.error(f"Failed to read configuration file {config_file}: {e}")
                logger.info("Using default configuration")
                self.config = self._get_default_config()
            except Exception as e:
                logger.error(f"Unexpected error loading configuration from {config_file}: {e}", exc_info=True)
                logger.info("Using default configuration")
                self.config = self._get_default_config()
        else:
            logger.info(f"Configuration file not found at {config_file}, using defaults")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """
        Get default configuration.
        
        Returns:
            Dictionary containing default configuration values
        """
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 3000,
                'debug': False
            },
            'midi': {
                'enabled': True,
                'mappings': {
                    'play': 60,
                    'stop': 61,
                    'next': 62,
                    'previous': 63
                }
            },
            'audio': {
                'sounds_dir': None  # Will use default (assets/sounds)
            },
            'storage': {
                'dir': None  # Will use default (~/.clicktrack)
            }
        }
    
    def initialize_components(self):
        """
        Initialize all application components in the correct order.
        
        Raises:
            Exception: If critical components fail to initialize
        """
        logger.info("Initializing application components...")
        
        try:
            # 1. Initialize Storage Manager
            storage_dir = self.config.get('storage', {}).get('dir')
            self.storage_manager = StorageManager(storage_dir=storage_dir)
            logger.info("Storage Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Storage Manager: {e}", exc_info=True)
            raise RuntimeError("Critical component initialization failed: Storage Manager") from e
        
        try:
            # 2. Initialize Song Manager (loads songs from storage)
            self.song_manager = SongManager(self.storage_manager)
            logger.info("Song Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Song Manager: {e}", exc_info=True)
            raise RuntimeError("Critical component initialization failed: Song Manager") from e
        
        try:
            # 3. Initialize Set Manager (loads sets from storage)
            self.set_manager = SetManager(self.storage_manager)
            logger.info("Set Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Set Manager: {e}", exc_info=True)
            raise RuntimeError("Critical component initialization failed: Set Manager") from e
        
        try:
            # 4. Initialize Playback Engine
            sounds_dir = self.config.get('audio', {}).get('sounds_dir')
            audio_device = self.config.get('audio', {}).get('device', 'hw:2,0')
            self.playback_engine = PlaybackEngine(sounds_dir=sounds_dir, audio_device=audio_device)
            logger.info("Playback Engine initialized")
        except FileNotFoundError as e:
            logger.error(f"Audio files not found: {e}")
            logger.warning("Playback Engine initialized but audio may not work properly")
            # Continue - web interface can still be used for management
            self.playback_engine = PlaybackEngine(sounds_dir=sounds_dir, audio_device=audio_device)
        except Exception as e:
            logger.error(f"Failed to initialize Playback Engine: {e}", exc_info=True)
            logger.warning("Continuing without audio playback support")
            # Create a minimal playback engine that won't crash
            self.playback_engine = PlaybackEngine(sounds_dir=sounds_dir, audio_device=audio_device)
        
        try:
            # 5. Initialize Set Screen Controller
            self.set_screen_controller = SetScreenController(
                set_manager=self.set_manager,
                song_manager=self.song_manager,
                playback_engine=self.playback_engine
            )
            logger.info("Set Screen Controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Set Screen Controller: {e}", exc_info=True)
            raise RuntimeError("Critical component initialization failed: Set Screen Controller") from e
        
        # 6. Initialize MIDI Handler (optional)
        midi_config = self.config.get('midi', {})
        if midi_config.get('enabled', True):
            try:
                midi_mappings = midi_config.get('mappings')
                device_name = midi_config.get('device_name')
                enable_display_output = midi_config.get('enable_display_output', False)
                self.midi_handler = MIDIHandler(
                    mappings=midi_mappings, 
                    device_name=device_name,
                    enable_display_output=enable_display_output
                )
                
                # Attempt to connect to MIDI device
                if self.midi_handler.initialize():
                    logger.info("MIDI Handler initialized and connected")
                else:
                    logger.warning("MIDI Handler initialized but no device connected")
                
                # Set MIDI handler in SetScreenController for display output
                self.set_screen_controller.set_midi_handler(self.midi_handler)
            except ImportError as e:
                logger.warning(f"MIDI library not available: {e}")
                logger.info("Continuing without MIDI support")
                self.midi_handler = None
            except Exception as e:
                logger.error(f"Failed to initialize MIDI Handler: {e}", exc_info=True)
                logger.info("Continuing without MIDI support")
                self.midi_handler = None
        else:
            logger.info("MIDI support disabled in configuration")
            self.midi_handler = None
        
        try:
            # 7. Initialize Web Server
            server_config = self.config.get('server', {})
            self.web_server = WebServer(
                song_manager=self.song_manager,
                set_manager=self.set_manager,
                set_screen_controller=self.set_screen_controller,
                midi_handler=self.midi_handler,
                host=server_config.get('host', '0.0.0.0'),
                port=server_config.get('port', 3000)
            )
            logger.info("Web Server initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Web Server: {e}", exc_info=True)
            raise RuntimeError("Critical component initialization failed: Web Server") from e
        
        logger.info("All components initialized successfully")
    
    def start(self):
        """
        Start the Click Track Player application.
        
        This method:
        1. Loads configuration
        2. Initializes all components
        3. Starts the web server
        
        Raises:
            Exception: If startup fails
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting Click Track Player")
            logger.info("=" * 60)
            
            # Load configuration
            self.load_configuration()
            
            # Initialize all components
            self.initialize_components()
            
            # Register signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start web server (this blocks until server stops)
            server_config = self.config.get('server', {})
            debug_mode = server_config.get('debug', False)
            
            logger.info("=" * 60)
            logger.info(f"Click Track Player is running on http://{server_config.get('host', '0.0.0.0')}:{server_config.get('port', 3000)}")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)
            
            self.web_server.run(debug=debug_mode)
        
        except Exception as e:
            logger.error(f"Failed to start application: {e}", exc_info=True)
            self.shutdown()
            raise
    
    def shutdown(self):
        """
        Gracefully shutdown the application.
        
        This method:
        1. Stops playback
        2. Closes MIDI connection
        3. Saves any pending state
        """
        logger.info("Shutting down Click Track Player...")
        
        try:
            # Stop playback if active
            if self.set_screen_controller and self.playback_engine:
                if self.playback_engine.is_playing():
                    logger.info("Stopping active playback...")
                    self.set_screen_controller.stop()
            
            # Close MIDI connection
            if self.midi_handler:
                logger.info("Closing MIDI connection...")
                self.midi_handler.close()
            
            logger.info("Shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals (SIGINT, SIGTERM).
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()
        sys.exit(0)


def main():
    """
    Main entry point for the Click Track Player application.
    
    This function:
    1. Sets up logging
    2. Creates and starts the application
    3. Handles any startup errors
    """
    # Set up logging first
    setup_logging()
    
    try:
        # Create and start application
        app = ClickTrackApplication()
        app.start()
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
