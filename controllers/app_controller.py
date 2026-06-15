"""
App Controller
Main controller coordinating all services and UI interactions
"""
from typing import Optional, List, Callable, Any
from pathlib import Path
import logging

from core.event_bus import EventBus
from services import (
    SettingsService, FileService, AudioService,
    ConversionService, ModelService
)
from models.domain import (
    VoiceSettings, OutputSettings, ConversionStatus,
    RecentFile, ModelInfo
)

logger = logging.getLogger(__name__)


class AppController:
    """Main application controller."""
    
    def __init__(
        self,
        config_manager,
        model_manager,
        epub_processor,
        tts_engine,
        audio_builder,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize app controller.
        
        Args:
            config_manager: ConfigManager instance
            model_manager: ModelManager instance
            epub_processor: EpubProcessor instance
            tts_engine: TTSEngine instance
            audio_builder: AudioBuilder instance
            event_bus: Optional EventBus instance
        """
        self._event_bus = event_bus or EventBus()
        
        # Initialize services
        self.settings_service = SettingsService(config_manager)
        self.file_service = FileService(config_manager)
        self.audio_service = AudioService(tts_engine, config_manager)
        self.model_service = ModelService(model_manager, config_manager)
        self.conversion_service = ConversionService(
            tts_engine, audio_builder, epub_processor,
            model_manager, config_manager, event_bus
        )
        
        # UI callbacks
        self._log_callback: Optional[Callable[[str], None]] = None
        self._progress_callback: Optional[Callable[[float], None]] = None
        self._status_callback: Optional[Callable[[str], None]] = None
        
        logger.info("AppController initialized")
    
    def set_ui_callbacks(
        self,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Set UI callback functions."""
        self._log_callback = log_callback
        self._progress_callback = progress_callback
        self._status_callback = status_callback
    
    def log(self, message: str) -> None:
        """Log message to UI."""
        logger.info(message)
        if self._log_callback:
            self._log_callback(message)
    
    def update_progress(self, progress: float) -> None:
        """Update progress in UI."""
        if self._progress_callback:
            self._progress_callback(progress)
    
    def update_status(self, status: str) -> None:
        """Update status in UI."""
        if self._status_callback:
            self._status_callback(status)
    
    # --- File Operations ---
    
    def load_epub_file(self, file_path: Path) -> tuple:
        """
        Load an EPUB file.
        
        Args:
            file_path: Path to EPUB file
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        is_valid, error = self.file_service.validate_epub_file(file_path)
        
        if not is_valid:
            self.log(f"Error: {error}")
            return False, error
        
        # Add to recent files
        self.file_service.add_recent_file(file_path)
        
        self.log(f"Loaded: {file_path.name}")
        return True, None
    
    def get_recent_files(self) -> List[RecentFile]:
        """Get list of recent files."""
        return self.file_service.get_recent_files()
    
    def update_file_status(self, file_path: Path, status: ConversionStatus) -> None:
        """Update file conversion status."""
        self.file_service.update_file_status(file_path, status)
    
    def set_output_directory(self, dir_path: Path) -> tuple:
        """
        Set output directory.
        
        Args:
            dir_path: Path to output directory
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        is_valid, error = self.file_service.validate_output_directory(dir_path)
        
        if not is_valid:
            self.log(f"Error: {error}")
            return False, error
        
        return True, None
    
    def set_cover_image(self, image_path: Path) -> tuple:
        """
        Set cover image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        is_valid, error = self.file_service.validate_cover_image(image_path)
        
        if not is_valid:
            self.log(f"Error: {error}")
            return False, error
        
        return True, None
    
    # --- Settings Operations ---
    
    def get_voice_settings(self) -> VoiceSettings:
        """Get current voice settings."""
        return self.settings_service.get_voice_settings()
    
    def set_voice_settings(self, settings: VoiceSettings) -> None:
        """Save voice settings."""
        self.settings_service.set_voice_settings(settings)
    
    def get_output_settings(self) -> OutputSettings:
        """Get current output settings."""
        return self.settings_service.get_output_settings()
    
    def set_output_settings(self, settings: OutputSettings) -> None:
        """Save output settings."""
        self.settings_service.set_output_settings(settings)
    
    def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        self.settings_service.reset_to_defaults()
        self.log("Settings reset to defaults")
    
    def get_quality_presets(self) -> List[str]:
        """Get list of quality preset names."""
        return self.settings_service.list_quality_presets()
    
    # --- Model Operations ---
    
    def get_available_models(self, only_recommended: bool = False) -> List[ModelInfo]:
        """Get list of available TTS models."""
        return self.model_service.get_available_models(only_recommended=only_recommended)
    
    def is_model_installed(self, model_name: str) -> bool:
        """Check if a model is installed."""
        return self.model_service.is_model_installed(model_name)
    
    def download_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """Download a TTS model."""
        def on_complete(success):
            if success:
                self.log(f"Model downloaded: {model_name}")
            else:
                self.log(f"Failed to download model: {model_name}")
        
        def on_error(error):
            self.log(f"Download error: {error}")
        
        return self.model_service.download_model(
            model_name,
            progress_callback=progress_callback,
            complete_callback=on_complete,
            error_callback=on_error
        )
    
    # --- Audio Operations ---
    
    def validate_speed(self, speed: float) -> float:
        """Validate and clamp speed value."""
        return self.audio_service.validate_speed(speed)
    
    def get_speed_range(self) -> tuple:
        """Get valid speed range."""
        return self.audio_service.get_speed_range()
    
    def preview_voice(
        self,
        voice_settings: VoiceSettings,
        model_info: dict,
        on_complete: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_play_progress: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Preview voice with current settings.
        
        Args:
            voice_settings: Voice configuration
            model_info: Model information
            on_complete: Optional completion callback
            on_error: Optional error callback
            on_play_progress: Optional playback progress callback
            
        Returns:
            True if preview started
        """
        if not self.model_service.is_model_installed(voice_settings.model_name):
            self.log("Please download the model first")
            return False
        
        self.update_status("Generating preview...")
        
        def play_complete():
            self.update_status("Ready")
            if on_complete:
                on_complete()
        
        def play_error(error):
            self.log(f"Playback error: {error}")
            self.update_status("Ready")
            if on_error:
                on_error(error)
        
        def on_audio_generated(audio_path):
            if audio_path:
                self.update_status("Playing preview...")
                self.audio_service.play_audio(
                    audio_path,
                    on_complete=play_complete,
                    on_error=play_error,
                    on_progress=on_play_progress
                )
        
        def on_error_gen(error):
            self.log(f"Preview generation failed: {error}")
            self.update_status("Ready")
            if on_error:
                on_error(error)
        
        return self.audio_service.generate_preview(
            voice_settings,
            model_info,
            progress_callback=lambda p: self.update_progress(p),
            complete_callback=on_audio_generated,
            error_callback=on_error_gen
        ) is not None
    
    def stop_preview(self) -> None:
        """Stop voice preview playback."""
        self.audio_service.stop_playback()
        self.update_status("Ready")
    
    # --- Conversion Operations ---
    
    def start_conversion(
        self,
        epub_paths: List[Path],
        voice_settings: VoiceSettings,
        output_settings: OutputSettings
    ) -> Optional[str]:
        """
        Start audiobook conversion.
        
        Args:
            epub_paths: List of EPUB file paths
            voice_settings: Voice configuration
            output_settings: Output configuration
            
        Returns:
            Job ID or None if failed
        """
        if not epub_paths:
            self.log("No EPUB files selected")
            return None
        
        # For now, handle single file (can be extended for batch)
        epub_path = epub_paths[0]
        
        # Create job
        job = self.conversion_service.create_job(
            epub_path, voice_settings, output_settings
        )
        
        # Set up callbacks
        def on_progress(progress):
            self.update_progress(progress.overall_progress / 100.0)
            self.update_status(progress.status_message)
        
        def on_complete(completed_job):
            self.update_progress(1.0)
            self.update_status("Conversion complete!")
            self.file_service.update_file_status(epub_path, ConversionStatus.COMPLETED)
            self.log(f"Conversion complete: {completed_job.output_path}")
        
        def on_error(error):
            self.update_status("Conversion failed")
            self.log(f"Conversion error: {error}")
            self.file_service.update_file_status(epub_path, ConversionStatus.FAILED)
        
        # Update file status
        self.file_service.update_file_status(epub_path, ConversionStatus.IN_PROGRESS)
        
        # Start job
        success = self.conversion_service.start_job(
            job.id,
            progress_callback=on_progress,
            complete_callback=on_complete,
            error_callback=on_error
        )
        
        if success:
            self.log(f"Started conversion: {epub_path.name}")
            return job.id
        else:
            self.log("Failed to start conversion")
            return None
    
    def cancel_conversion(self, job_id: str) -> bool:
        """Cancel a running conversion."""
        return self.conversion_service.cancel_job(job_id)
    
    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        from audio_builder import AudioBuilder
        builder = AudioBuilder()
        return builder.check_ffmpeg()
    
    def emit_event(self, event_name: str, **kwargs) -> None:
        """Emit event through event bus."""
        self._event_bus.emit(event_name, **kwargs)
    
    def subscribe_to_event(self, event_name: str, callback: Callable) -> None:
        """Subscribe to event."""
        self._event_bus.subscribe(event_name, callback)
