"""
Conversion Service
Orchestrates the audiobook conversion process
"""
from typing import Optional, List, Callable, Dict, Any
from pathlib import Path
import uuid
import logging
import os
import json
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
        self._active_workers: Dict[str, Any] = {}
        
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
        
        # Get model info
        model_info = self._get_model_info(job.voice_settings.model_name)
        if not model_info:
            err_msg = f"Model not found: {job.voice_settings.model_name}"
            logger.error(err_msg)
            if error_callback:
                error_callback(err_msg)
            return False
            
        # Register callbacks
        if progress_callback:
            self._progress_callbacks.setdefault(job_id, []).append(progress_callback)
        if complete_callback:
            self._completion_callbacks.setdefault(job_id, []).append(complete_callback)
        
        # Load pause settings from config
        pause_settings = {
            'sentence_pause_ms': self._config_manager.get("pause_sentence", 700) or 700,
            'clause_pause_ms': self._config_manager.get("pause_clause", 250) or 250,
            'paragraph_pause_ms': self._config_manager.get("pause_paragraph", 1500) or 1500,
            'dialogue_pause_ms': self._config_manager.get("pause_dialogue", 400) or 400
        }
        
        # Load character voice assignments if multi-speaker model
        character_voices = None
        if model_info.get('num_speakers', 1) > 1:
            book_id = os.path.basename(job.book_metadata.file_path)
            character_voices = self._config_manager.get(f"character_voices_{book_id}", None)
            if character_voices:
                logger.info(f"Using character voice assignments: {len(character_voices)} characters")
        
        # Callbacks for ConversionWorker
        last_progress_pct = [0.0]  # Use list for nonlocal mutation
        
        def worker_log(msg):
            logger.info(f"[{job_id}] {msg}")
            if self._event_bus:
                self._event_bus.emit("job_log", job_id=job_id, message=msg)
                
        def worker_progress(p_val):
            last_progress_pct[0] = p_val * 100.0
            p_obj = ConversionProgress(
                job_id=job_id,
                current_chapter=0,
                total_chapters=len(job.book_metadata.chapters),
                current_chapter_title="",
                chapter_progress=0.0,
                overall_progress=last_progress_pct[0],
                status_message=f"Converting... {int(last_progress_pct[0])}%"
            )
            self._job_progress[job_id] = p_obj
            self._notify_progress(job_id, p_obj)

        def worker_status(msg, progress=None, eta=None, chapter_idx=None, chapter_status=None):
            overall = last_progress_pct[0]
            if progress is not None:
                overall = progress * 100.0
                
            status_text = msg
            if eta:
                status_text = f"{msg} ({eta})"
                
            p_obj = ConversionProgress(
                job_id=job_id,
                current_chapter=chapter_idx + 1 if chapter_idx is not None else 0,
                total_chapters=len(job.book_metadata.chapters),
                current_chapter_title=job.book_metadata.chapters[chapter_idx]['title'] if (chapter_idx is not None and chapter_idx < len(job.book_metadata.chapters)) else "",
                chapter_progress=0.0,
                overall_progress=overall,
                status_message=status_text
            )
            self._job_progress[job_id] = p_obj
            self._notify_progress(job_id, p_obj)

        def worker_done():
            is_cancelled = job.status == ConversionStatus.CANCELLED or (job_id in self._active_workers and self._active_workers[job_id]._is_cancelled())
            
            if is_cancelled:
                logger.info(f"Worker done (cancelled): {job_id}")
                if job.status != ConversionStatus.CANCELLED:
                    job.cancel()
                if self._event_bus:
                    self._event_bus.emit("job_cancelled", job=job)
            else:
                base_name = job.book_metadata.file_path.stem
                output_dir_root = job.output_settings.output_dir or job.book_metadata.file_path.parent
                
                # Check formatting
                fmt = job.output_settings.format.value
                success = False
                out_path = None
                
                if fmt == "m4b":
                    out_path = Path(output_dir_root) / f"{base_name}.m4b"
                    success = out_path.exists()
                elif fmt in ("mp3", "wav"):
                    out_path = Path(output_dir_root) / f"{base_name}_audiobook"
                    success = out_path.exists() and len(os.listdir(out_path)) > 0
                
                if success:
                    logger.info(f"Worker done (success): {job_id}. Output: {out_path}")
                    job.complete(out_path)
                    self._notify_completion(job_id, job)
                    if self._event_bus:
                        self._event_bus.emit("job_completed", job=job)
                else:
                    logger.error(f"Worker done (failed - output missing): {job_id}")
                    err_msg = "Conversion completed but output file was not generated."
                    job.fail(err_msg)
                    if error_callback:
                        error_callback(err_msg)
                    if self._event_bus:
                        self._event_bus.emit("job_failed", job=job, error=err_msg)
            
            # Clean up active worker reference
            if job_id in self._active_workers:
                del self._active_workers[job_id]

        from conversion_worker import ConversionWorker
        worker = ConversionWorker(
            tts_engine=self._tts_engine,
            audio_builder=self._audio_builder,
            log_callback=worker_log,
            progress_callback=worker_progress,
            status_callback=worker_status,
            done_callback=worker_done
        )
        
        self._active_workers[job_id] = worker
        job.start()
        
        if self._event_bus:
            self._event_bus.emit("job_started", job=job)
            
        # Start conversion worker in its own thread
        output_dir_root = str(job.output_settings.output_dir) if job.output_settings.output_dir else str(job.book_metadata.file_path.parent)
        worker.start(
            selected_epubs=[str(job.book_metadata.file_path)],
            model_info=model_info,
            output_dir_root=output_dir_root,
            speed=job.voice_settings.speed,
            speaker_id=str(job.voice_settings.speaker_id),
            output_format=job.output_settings.format.value,
            use_gpu=job.voice_settings.use_gpu,
            epub_processor=self._epub_processor,
            custom_cover_path=str(job.output_settings.custom_cover) if job.output_settings.custom_cover else None,
            quality=job.output_settings.quality,
            models_dir=str(self._config_manager.get_models_dir()),
            normalize=job.output_settings.normalize,
            pause_settings=pause_settings,
            character_voices=character_voices
        )
        
        logger.info(f"Started conversion job: {job_id}")
        return True
    
    def _get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get model information by name."""
        for m in self._model_manager.list_available_models():
            if m.get('name') == model_name:
                return m
        return None
    
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
        
        if job_id in self._active_workers:
            self._active_workers[job_id].cancel()
        
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
