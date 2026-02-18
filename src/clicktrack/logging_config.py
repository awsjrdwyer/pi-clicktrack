"""
Logging configuration module for Click Track Player.

This module provides centralized logging setup with support for both
console and file output, including rotation and detailed formatting.
"""

import logging
import logging.config
import os
from pathlib import Path
import yaml


def setup_logging(config_path: str = None, default_level: int = logging.INFO):
    """
    Set up logging configuration for the application.
    
    Args:
        config_path: Path to logging configuration YAML file.
                    If None, uses default config from config/logging.yaml
        default_level: Default logging level if config file is not found
    """
    # Ensure log directory exists
    log_dir = Path.home() / '.clicktrack' / 'logs'
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"Log directory ready: {log_dir}")
    except Exception as e:
        print(f"Warning: Failed to create log directory {log_dir}: {e}")
        print("Logging to console only")
    
    if config_path is None:
        # Try to find config file relative to this module
        module_dir = Path(__file__).parent.parent.parent
        config_path = module_dir / 'config' / 'logging.yaml'
    
    config_path = Path(config_path)
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Expand home directory in file paths
            for handler in config.get('handlers', {}).values():
                if 'filename' in handler:
                    handler['filename'] = os.path.expanduser(handler['filename'])
            
            logging.config.dictConfig(config)
            logging.info(f"Logging configured from {config_path}")
        except yaml.YAMLError as e:
            # Fall back to basic configuration
            logging.basicConfig(
                level=default_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logging.error(f"Invalid YAML in logging config {config_path}: {e}")
        except IOError as e:
            # Fall back to basic configuration
            logging.basicConfig(
                level=default_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logging.error(f"Failed to read logging config from {config_path}: {e}")
        except Exception as e:
            # Fall back to basic configuration
            logging.basicConfig(
                level=default_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logging.error(f"Unexpected error loading logging config from {config_path}: {e}")
    else:
        # Use basic configuration if config file not found
        logging.basicConfig(
            level=default_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.warning(f"Logging config file not found at {config_path}, using basic config")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name for the logger (typically __name__ of the module)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
