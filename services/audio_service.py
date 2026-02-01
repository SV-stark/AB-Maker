"""
Audio Service
Handles audio-related operations including playback and format support
"""
from typing import Optional, Callable, Any
from pathlib import Path
import tempfile
import os
import logging
import time
import threading

from config.constants import get_config
from models.domain import VoiceSettings

logger = logging.getLogger(__name__)


class AudioService:
    """Service for audio operations and playback."""
    
    def __init__(self, tts_engine, config_manager):
        """
        Initialize audio service.
        
        Args:
            tts_engine: TTSEngine instance
            config_manager: ConfigManager instance
        """
        self._tts_engine = tts_engine
        self._config_manager = config_manager
        self._app_config = get_config()
        
        # Playback state
        self._is_playing = False
        self._current_stream = None
        self._cancel_playback = False
        self._playback_lock = threading.Lock()
    
    def get_speed_range(self) -> tuple:
        """Get valid speed range (min, max, default)."""
        return (
            self._app_config.audio.min_speed,
            self._app_config.audio.max_speed,
            self._app_config.audio.default_speed
        )
    
    def validate_speed(self, speed: float) -> float:
        """
        Validate and clamp speed value.
        
        Args:
            speed: Requested speed
            
        Returns:
            Clamped speed value
        """
        min_speed, max_speed, _ = self.get_speed_range()
        return max(min_speed, min(max_speed, speed))
    
    def generate_preview(
        self,
        voice_settings: VoiceSettings,
        model_info: dict,
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[Path], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[Path]:
        """
        Generate audio preview.
        
        Args:
            voice_settings: Voice configuration
            model_info: Model information dict
            progress_callback: Optional progress callback (0.0-1.0)
            complete_callback: Optional completion callback with path
            error_callback: Optional error callback with message
            
        Returns:
            Path to generated audio file or None
        """
        try:
            # Create temp file
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            temp_path = Path(temp_path)
            
            # Configure TTS
            config = model_info.copy()
            config['model_dir'] = os.path.join(
                self._config_manager.get_models_dir(),
                model_info.get('extracted_dir', '')
            )
            config['provider'] = "cuda" if voice_settings.use_gpu else "cpu"
            
            # Initialize model
            if not self._tts_engine.initialize_model(config):
                raise RuntimeError("Failed to initialize TTS model")
            
            # Generate audio
            text = self._app_config.audio.preview_text
            if progress_callback:
                progress_callback(0.5)
            
            success = self._tts_engine.generate_audio(
                text=text,
                output_path=str(temp_path),
                speed=voice_settings.speed,
                sid=voice_settings.speaker_id
            )
            
            if not success:
                raise RuntimeError("Failed to generate audio")
            
            if progress_callback:
                progress_callback(1.0)
            
            if complete_callback:
                complete_callback(temp_path)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            if error_callback:
                error_callback(str(e))
            return None
    
    def play_audio(
        self,
        audio_path: Path,
        on_complete: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Play audio file.
        
        Args:
            audio_path: Path to audio file
            on_complete: Optional callback when playback completes
            on_error: Optional callback on error
            
        Returns:
            True if playback started successfully
        """
        with self._playback_lock:
            if self._is_playing:
                logger.warning("Audio already playing")
                return False
            
            self._is_playing = True
            self._cancel_playback = False
        
        def _play():
            try:
                import sounddevice as sd
                import soundfile as sf
                
                data, samplerate = sf.read(str(audio_path))
                
                with self._playback_lock:
                    if self._cancel_playback:
                        return
                
                sd.play(data, samplerate)
                
                # Wait for playback
                while sd.get_stream().active:
                    with self._playback_lock:
                        if self._cancel_playback:
                            sd.stop()
                            break
                    time.sleep(0.1)
                
                with self._playback_lock:
                    self._is_playing = False
                
                if on_complete and not self._cancel_playback:
                    on_complete()
                    
            except Exception as e:
                logger.error(f"Playback error: {e}")
                with self._playback_lock:
                    self._is_playing = False
                if on_error:
                    on_error(str(e))
        
        threading.Thread(target=_play, daemon=True).start()
        return True
    
    def stop_playback(self) -> None:
        """Stop current audio playback."""
        with self._playback_lock:
            self._cancel_playback = True
            self._is_playing = False
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        with self._playback_lock:
            return self._is_playing
    
    def cleanup_temp_file(self, file_path: Path, max_retries: int = None) -> bool:
        """
        Clean up temporary audio file with retries.
        
        Args:
            file_path: Path to temp file
            max_retries: Maximum retry attempts (default from config)
            
        Returns:
            True if successfully deleted
        """
        if max_retries is None:
            max_retries = self._app_config.cache.temp_file_cleanup_retries
        
        for i in range(max_retries):
            try:
                if file_path.exists():
                    os.remove(file_path)
                return True
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file (attempt {i+1}): {e}")
                time.sleep(self._app_config.cache.temp_file_cleanup_delay)
        
        return False
    
    def get_supported_formats(self) -> list:
        """Get list of supported output formats."""
        return self._app_config.audio.supported_formats.copy()
    
    def get_default_format(self) -> str:
        """Get default output format."""
        return self._app_config.audio.default_format
