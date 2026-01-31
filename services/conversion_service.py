"""
Conversion Service
Orchestrates the audiobook conversion process
"""
from typing import Optional, List, Callable, Dict, Any
from pathlib import Path
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.domain import (
    ConversionJob, BookMetadata, VoiceSettings, OutputSettings,
    ConversionStatus, ConversionProgress
)
from config.constants import get_config

logger = logging.getLogger(__name__)


class ConversionService:
    """Service for managing audiobook conversions."""
    
    def __init__(
        self,
        tts_engine,
        audio_builder,
        epub_processor,
        model_manager,
        config_manager,
        event_bus=None
    ):
        """
        Initialize conversion service.
        
        Args:
            tts_engine: TTSEngine instance
            audio_builder: AudioBuilder instance
            epub_processor: EpubProcessor instance
            model_manager: ModelManager instance
            config_manager: ConfigManager instance
            event_bus: Optional EventBus instance
        """
        self._tts_engine = tts_engine
        self._audio_builder = audio_builder
        self._epub_processor = epub_processor
        self._model_manager = model_manager
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._app_config = get_config()
        
        # Active jobs
        self._active_jobs: Dict[str, ConversionJob] = {}
        self._job_progress: Dict[str, ConversionProgress] = {}
        
        # Callbacks
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        self._completion_callbacks: Dict[str, List[Callable]] = {}
    
    def create_job(
        self,
        epub_path: Path,
        voice_settings: VoiceSettings,
        output_settings: OutputSettings
    ) -> ConversionJob:
        """
        Create a new conversion job.
        
        Args:
            epub_path: Path to EPUB file
            voice_settings: Voice configuration
            output_settings: Output configuration
            
        Returns:
            ConversionJob instance
        """
        # Extract metadata
        try:
            chapters = self._epub_processor.extract_chapters(str(epub_path))
            metadata = BookMetadata(
                title=epub_path.stem,
                file_path=epub_path,
                cover_image=output_settings.custom_cover,
                chapters=chapters
            )
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            metadata = BookMetadata(
                title=epub_path.stem,
                file_path=epub_path,
                cover_image=output_settings.custom_cover
            )
        
        job = ConversionJob(
            id=str(uuid.uuid4()),
            book_metadata=metadata,
            voice_settings=voice_settings,
            output_settings=output_settings
        )
        
        self._active_jobs[job.id] = job
        
        if self._event_bus:
            self._event_bus.emit("job_created", job=job)
        
        logger.info(f"Created conversion job: {job.id}")
        return job
    
    def start_job(
        self,
        job_id: str,
        progress_callback: Optional[Callable[[ConversionProgress], None]] = None,
        complete_callback: Optional[Callable[[ConversionJob], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Start a conversion job.
        
        Args:
            job_id: Job ID
            progress_callback: Optional progress callback
            complete_callback: Optional completion callback
            error_callback: Optional error callback
            
        Returns:
            True if job started successfully
        """
        if job_id not in self._active_jobs:
            logger.error(f"Job not found: {job_id}")
            return False
        
        job = self._active_jobs[job_id]
        
        if job.status != ConversionStatus.PENDING:
            logger.warning(f"Job already started: {job_id}")
            return False
        
        # Register callbacks
        if progress_callback:
            self._progress_callbacks.setdefault(job_id, []).append(progress_callback)
        if complete_callback:
            self._completion_callbacks.setdefault(job_id, []).append(complete_callback)
        
        job.start()
        
        if self._event_bus:
            self._event_bus.emit("job_started", job=job)
        
        # Start conversion in background
        import threading
        thread = threading.Thread(
            target=self._run_conversion,
            args=(job_id, error_callback),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started conversion job: {job_id}")
        return True
    
    def _run_conversion(self, job_id: str, error_callback: Optional[Callable] = None):
        """Run the conversion process."""
        job = self._active_jobs.get(job_id)
        if not job:
            return
        
        try:
            # Check if model needs download
            model_info = self._get_model_info(job.voice_settings.model_name)
            if model_info and not self._model_manager.is_model_installed(model_info):
                logger.info(f"Downloading model: {job.voice_settings.model_name}")
                # TODO: Implement model download with progress
            
            # Process chapters
            total_chapters = len(job.book_metadata.chapters)
            
            for i, chapter in enumerate(job.book_metadata.chapters):
                # Update progress
                progress = ConversionProgress(
                    job_id=job_id,
                    current_chapter=i + 1,
                    total_chapters=total_chapters,
                    current_chapter_title=chapter.title,
                    chapter_progress=0.0,
                    overall_progress=(i / total_chapters) * 100,
                    status_message=f"Processing chapter {i + 1}/{total_chapters}: {chapter.title}"
                )
                
                self._job_progress[job_id] = progress
                self._notify_progress(job_id, progress)
                
                # TODO: Generate audio for chapter
                # TODO: Save chapter audio
            
            # Finalize
            output_path = self._finalize_job(job)
            job.complete(output_path)
            
            self._notify_completion(job_id, job)
            
            if self._event_bus:
                self._event_bus.emit("job_completed", job=job)
            
            logger.info(f"Conversion completed: {job_id}")
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            job.fail(str(e))
            
            if error_callback:
                error_callback(str(e))
            
            if self._event_bus:
                self._event_bus.emit("job_failed", job=job, error=str(e))
    
    def _get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get model information by name."""
        # TODO: Get from model manager
        return None
    
    def _finalize_job(self, job: ConversionJob) -> Path:
        """Finalize conversion and create output file."""
        # TODO: Implement finalization with audio_builder
        output_path = Path("output.m4b")
        return output_path
    
    def _notify_progress(self, job_id: str, progress: ConversionProgress):
        """Notify progress callbacks."""
        callbacks = self._progress_callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def _notify_completion(self, job_id: str, job: ConversionJob):
        """Notify completion callbacks."""
        callbacks = self._completion_callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                callback(job)
            except Exception as e:
                logger.error(f"Completion callback error: {e}")
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if job cancelled
        """
        if job_id not in self._active_jobs:
            return False
        
        job = self._active_jobs[job_id]
        job.cancel()
        
        if self._event_bus:
            self._event_bus.emit("job_cancelled", job=job)
        
        logger.info(f"Cancelled job: {job_id}")
        return True
    
    def get_job(self, job_id: str) -> Optional[ConversionJob]:
        """Get job by ID."""
        return self._active_jobs.get(job_id)
    
    def get_job_progress(self, job_id: str) -> Optional[ConversionProgress]:
        """Get job progress."""
        return self._job_progress.get(job_id)
    
    def get_all_jobs(self) -> List[ConversionJob]:
        """Get all jobs."""
        return list(self._active_jobs.values())
    
    def cleanup_job(self, job_id: str) -> bool:
        """
        Remove a job from tracking.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if job removed
        """
        if job_id in self._active_jobs:
            del self._active_jobs[job_id]
        
        if job_id in self._job_progress:
            del self._job_progress[job_id]
        
        if job_id in self._progress_callbacks:
            del self._progress_callbacks[job_id]
        
        if job_id in self._completion_callbacks:
            del self._completion_callbacks[job_id]
        
        return True
    
    def estimate_duration(
        self,
        epub_path: Path,
        voice_settings: VoiceSettings
    ) -> Optional[float]:
        """
        Estimate conversion duration.
        
        Args:
            epub_path: Path to EPUB
            voice_settings: Voice settings
            
        Returns:
            Estimated duration in seconds or None
        """
        try:
            chapters = self._epub_processor.extract_chapters(str(epub_path))
            total_chars = sum(len(ch.content) for ch in chapters)
            
            # Rough estimate: ~15 chars per second at 1.0 speed
            base_rate = 15.0
            estimated_seconds = total_chars / (base_rate * voice_settings.speed)
            
            return estimated_seconds
            
        except Exception as e:
            logger.error(f"Failed to estimate duration: {e}")
            return None
