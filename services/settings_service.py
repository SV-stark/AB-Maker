"""
Settings Service
Handles application settings and configuration management
"""
from typing import Optional, Any, Dict, List
from pathlib import Path
import logging
import threading

from config.constants import get_config, AppConfig
from models.domain import VoiceSettings, OutputSettings

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing application settings and configuration."""
    
    def __init__(self, config_manager):
        """
        Initialize settings service.
        
        Args:
            config_manager: ConfigManager instance for persistence
        """
        self._config_manager = config_manager
        self._app_config = get_config()
        self._lock = threading.Lock()
        self._cache: Dict[str, Any] = {}
        
        # Load settings into cache
        self._load_cache()
    
    def _load_cache(self):
        """Load settings from config manager into cache."""
        self._cache = {
            'theme_mode': self._config_manager.get('theme_mode', self._app_config.ui.theme_mode),
            'last_speed': self._config_manager.get('last_speed', self._app_config.audio.default_speed),
            'last_speaker_id': self._config_manager.get('last_speaker_id', self._app_config.audio.default_speaker_id),
            'use_gpu': self._config_manager.get('use_gpu', False),
            'last_model': self._config_manager.get('last_model', None),
            'output_format': self._config_manager.get('output_format', self._app_config.audio.default_format),
            'last_quality': self._config_manager.get('last_quality', 'Medium'),
            'normalize': self._config_manager.get('normalize', False),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        with self._lock:
            return self._cache.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        with self._lock:
            self._cache[key] = value
            self._config_manager.set(key, value)
    
    def get_voice_settings(self) -> VoiceSettings:
        """
        Get current voice settings.
        
        Returns:
            VoiceSettings instance
        """
        return VoiceSettings(
            model_name=self.get('last_model', ''),
            speed=float(self.get('last_speed', self._app_config.audio.default_speed)),
            speaker_id=int(self.get('last_speaker_id', self._app_config.audio.default_speaker_id)),
            use_gpu=self.get('use_gpu', False)
        )
    
    def set_voice_settings(self, settings: VoiceSettings) -> None:
        """
        Save voice settings.
        
        Args:
            settings: VoiceSettings to save
        """
        self.set('last_model', settings.model_name)
        self.set('last_speed', settings.speed)
        self.set('last_speaker_id', str(settings.speaker_id))
        self.set('use_gpu', settings.use_gpu)
    
    def get_output_settings(self) -> OutputSettings:
        """
        Get current output settings.
        
        Returns:
            OutputSettings instance
        """
        from models.domain import AudioFormat
        return OutputSettings(
            format=AudioFormat(self.get('output_format', self._app_config.audio.default_format)),
            quality=self.get('last_quality', 'Medium'),
            normalize=self.get('normalize', False)
        )
    
    def set_output_settings(self, settings: OutputSettings) -> None:
        """
        Save output settings.
        
        Args:
            settings: OutputSettings to save
        """
        self.set('output_format', settings.format.value)
        self.set('last_quality', settings.quality)
        self.set('normalize', settings.normalize)
    
    def get_quality_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get quality preset by name.
        
        Args:
            name: Preset name
            
        Returns:
            Preset dict or None
        """
        preset = self._app_config.quality_presets.get(name)
        if preset:
            return {
                'name': preset.name,
                'bitrate': preset.bitrate,
                'channels': preset.channels,
                'sample_rate': preset.sample_rate,
                'description': preset.description
            }
        return None
    
    def list_quality_presets(self) -> List[str]:
        """
        Get list of available quality preset names.
        
        Returns:
            List of preset names
        """
        return list(self._app_config.quality_presets.keys())
    
    def get_audio_config(self) -> AppConfig:
        """
        Get audio configuration.
        
        Returns:
            AppConfig instance
        """
        return self._app_config
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        defaults = {
            'theme_mode': self._app_config.ui.theme_mode,
            'last_speed': self._app_config.audio.default_speed,
            'last_speaker_id': self._app_config.audio.default_speaker_id,
            'use_gpu': False,
            'output_format': self._app_config.audio.default_format,
            'last_quality': 'Medium',
            'normalize': False,
        }
        
        for key, value in defaults.items():
            self.set(key, value)
        
        logger.info("Settings reset to defaults")
    
    def get_max_recent_files(self) -> int:
        """Get maximum number of recent files to track."""
        return self._app_config.ui.max_recent_files
    
    def get_theme_mode(self) -> str:
        """Get current theme mode."""
        return self.get('theme_mode', self._app_config.ui.theme_mode)
    
    def set_theme_mode(self, mode: str) -> None:
        """Set theme mode."""
        self.set('theme_mode', mode)
