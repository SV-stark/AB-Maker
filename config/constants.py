"""
AB-Maker Configuration Constants and Settings
Centralized configuration management with validation
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioQualityPreset:
    """Audio quality configuration preset."""
    name: str
    bitrate: str
    channels: int
    sample_rate: int
    description: str


@dataclass
class UIConfig:
    """UI-related configuration constants."""
    window_title: str = "AB-Maker: Audiobook Creator"
    default_width: int = 900
    default_height: int = 700
    min_width: int = 800
    min_height: int = 600
    theme_mode: str = "system"
    
    # Progress update intervals (seconds)
    progress_update_interval: float = 0.1
    
    # Debounce settings
    config_save_debounce: float = 1.0
    
    # Max recent files to display
    max_recent_files: int = 10


@dataclass
class AudioConfig:
    """Audio processing configuration."""
    # Default speed range
    min_speed: float = 0.5
    max_speed: float = 2.5
    default_speed: float = 1.0
    
    # Default speaker ID
    default_speaker_id: str = "0"
    
    # Audio formats
    supported_formats: List[str] = field(default_factory=lambda: ["m4b", "mp3"])
    default_format: str = "m4b"
    
    # Preview text
    preview_text: str = "This is a preview of the selected voice and speed settings."
    
    # Supported image formats for covers
    supported_cover_formats: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    )


@dataclass
class CacheConfig:
    """Caching and storage configuration."""
    # Max log file size (10MB)
    max_log_size: int = 10 * 1024 * 1024
    log_backup_count: int = 3
    
    # Cache settings
    cache_enabled: bool = True
    
    # Temp file retry settings
    temp_file_cleanup_retries: int = 3
    temp_file_cleanup_delay: float = 0.5


@dataclass
class ConversionConfig:
    """Conversion process configuration."""
    # Thread pool settings
    max_workers: int = 4
    
    # Download progress notification interval (%)
    download_progress_interval: int = 10
    
    # Batch processing
    batch_mode: bool = True


@dataclass
class AppConfig:
    """Main application configuration container."""
    ui: UIConfig = field(default_factory=UIConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    conversion: ConversionConfig = field(default_factory=ConversionConfig)
    
    # Quality presets
    quality_presets: Dict[str, AudioQualityPreset] = field(default_factory=dict)
    
    # File type filters
    epub_filter: List[tuple] = field(
        default_factory=lambda: [("EPUB files", "*.epub"), ("All files", "*.*")]
    )
    image_filter: List[tuple] = field(
        default_factory=lambda: [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("All files", "*.*")
        ]
    )
    
    def __post_init__(self):
        """Initialize default quality presets if not provided."""
        if not self.quality_presets:
            self.quality_presets = {
                "Low": AudioQualityPreset(
                    name="Low",
                    bitrate="32k",
                    channels=1,
                    sample_rate=22050,
                    description="Low quality - testing/small files"
                ),
                "Medium": AudioQualityPreset(
                    name="Medium",
                    bitrate="64k",
                    channels=1,
                    sample_rate=22050,
                    description="Medium quality - balanced"
                ),
                "High": AudioQualityPreset(
                    name="High",
                    bitrate="128k",
                    channels=2,
                    sample_rate=44100,
                    description="High quality - excellent fidelity"
                ),
                "Lossless": AudioQualityPreset(
                    name="Lossless",
                    bitrate="320k",
                    channels=2,
                    sample_rate=48000,
                    description="Lossless quality - archival"
                ),
                "Podcast": AudioQualityPreset(
                    name="Podcast",
                    bitrate="48k",
                    channels=1,
                    sample_rate=22050,
                    description="Podcast optimized - voice focused"
                ),
                "Audible": AudioQualityPreset(
                    name="Audible",
                    bitrate="64k",
                    channels=1,
                    sample_rate=22050,
                    description="Audible compatible specs"
                ),
            }


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global application configuration."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def load_config_from_file(path: Path) -> AppConfig:
    """Load configuration from a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create config from loaded data
        config = AppConfig()
        
        # Update with loaded values
        if 'ui' in data:
            for key, value in data['ui'].items():
                if hasattr(config.ui, key):
                    setattr(config.ui, key, value)
        
        if 'audio' in data:
            for key, value in data['audio'].items():
                if hasattr(config.audio, key):
                    setattr(config.audio, key, value)
        
        if 'cache' in data:
            for key, value in data['cache'].items():
                if hasattr(config.cache, key):
                    setattr(config.cache, key, value)
        
        if 'conversion' in data:
            for key, value in data['conversion'].items():
                if hasattr(config.conversion, key):
                    setattr(config.conversion, key, value)
        
        # Load custom quality presets
        if 'quality_presets' in data:
            for name, preset_data in data['quality_presets'].items():
                config.quality_presets[name] = AudioQualityPreset(**preset_data)
        
        logger.info(f"Configuration loaded from {path}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load config from {path}: {e}")
        logger.info("Using default configuration")
        return AppConfig()


def save_config_to_file(config: AppConfig, path: Path) -> bool:
    """Save configuration to a JSON file."""
    try:
        data = {
            'ui': {
                'window_title': config.ui.window_title,
                'default_width': config.ui.default_width,
                'default_height': config.ui.default_height,
                'theme_mode': config.ui.theme_mode,
            },
            'audio': {
                'min_speed': config.audio.min_speed,
                'max_speed': config.audio.max_speed,
                'default_speed': config.audio.default_speed,
                'default_speaker_id': config.audio.default_speaker_id,
                'default_format': config.audio.default_format,
                'supported_formats': config.audio.supported_formats,
            },
            'cache': {
                'cache_enabled': config.cache.cache_enabled,
                'max_log_size': config.cache.max_log_size,
                'log_backup_count': config.cache.log_backup_count,
            },
            'conversion': {
                'max_workers': config.conversion.max_workers,
                'download_progress_interval': config.conversion.download_progress_interval,
            },
            'quality_presets': {
                name: {
                    'name': preset.name,
                    'bitrate': preset.bitrate,
                    'channels': preset.channels,
                    'sample_rate': preset.sample_rate,
                    'description': preset.description,
                }
                for name, preset in config.quality_presets.items()
            }
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Configuration saved to {path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save config to {path}: {e}")
        return False
