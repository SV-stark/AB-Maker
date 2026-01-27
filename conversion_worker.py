import threading
import time
import os
import logging
import soundfile as sf
import traceback
from exceptions import ABMakerError, ModelDownloadError, TTSGenError, FFmpegError


class ConversionWorker:
    def __init__(self, tts_engine, audio_builder, log_callback, progress_callback, status_callback, done_callback, init_list_callback=None):
        self.tts_engine = tts_engine
        self.audio_builder = audio_builder
        self.log = log_callback
        self.update_progress = progress_callback
        self.update_status = status_callback
        self.on_done = done_callback
        self.init_list = init_list_callback
        
        self._cancel_event = threading.Event()
        self._thread = None
        self.logger = logging.getLogger(__name__)

    def start(self, selected_epubs, model_info, output_dir_root, speed, speaker_id, output_format, use_gpu, epub_processor, custom_cover_path=None, quality="Medium", models_dir=None, normalize=False):
        """Starts the conversion process in a separate thread.
        
        Args:
            custom_cover_path: Optional path to a custom cover image (overrides EPUB cover)
            quality: Audio quality preset (Low, Medium, High, Lossless)
            models_dir: Directory where models are stored
            normalize: Apply audio normalization
        """
        self._cancel_event.clear()
        self._thread = threading.Thread(
            target=self._run_conversion,
            args=(selected_epubs, model_info, output_dir_root, speed, speaker_id, output_format, use_gpu, epub_processor, custom_cover_path, quality, models_dir, normalize),
            daemon=True
        )
        self._thread.start()

    def cancel(self):
        """Signals the worker to cancel."""
        self._cancel_event.set()
        self.log("Stopping... please wait for current task to finish.")

    def _is_cancelled(self):
        return self._cancel_event.is_set()

    def _run_conversion(self, selected_epubs, model_info, output_dir_root, speed, speaker_id, output_format, use_gpu, epub_processor, custom_cover_path=None, quality="Medium", models_dir=None, normalize=False):
        try:
            conversion_start_time = time.time()  # Track total conversion time
            
            # 1. Initialize TTS Model
            self.update_status("Initializing TTS...", 0)
            
            # Setup config for TTS
            from model_manager import ModelManager
            
            # Helper to get models dir relative to this script
            if not models_dir:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                models_dir = os.path.join(base_dir, "models") 
                
            model_path = os.path.join(models_dir, model_info['extracted_dir'])
            
            config = model_info.copy()
            config['model_dir'] = model_path
            config['provider'] = "cuda" if use_gpu else "cpu"
            
            # Check for espeak-ng-data - Critical for quality
            espeak_path = os.path.join(model_path, "espeak-ng-data")
            if not os.path.exists(espeak_path):
                self.log("WARNING: 'espeak-ng-data' folder missing!")
                self.log(">>> Audio quality/intonation will be poor.")
                self.log(">>> Please delete and re-download the model.")

            if use_gpu:
                self.log(f"Initializing TTS with GPU (CUDA)...")
            else:
                self.log(f"Initializing TTS with CPU...")

            if not self.tts_engine.initialize_model(config):
                self.log("Error: Failed to initialize TTS engine.")
                self.on_done()
                return

            total_books = len(selected_epubs)
            
            for b_idx, epub_path in enumerate(selected_epubs):
                if self._is_cancelled(): break
                
                book_name = os.path.basename(epub_path)
                self.log(f"Processing Book {b_idx+1}/{total_books}: {book_name}")
                
                # Extract book metadata (title, author, cover)
                self.update_status(f"Extracting metadata from {book_name}...", 0)
                book_metadata = epub_processor.extract_metadata(epub_path)
                
                # Use custom cover if provided, otherwise use extracted cover
                cover_path = custom_cover_path if custom_cover_path else book_metadata.get('cover_path')
                
                if book_metadata.get('title'):
                    self.log(f"Book: {book_metadata['title']} by {book_metadata.get('author', 'Unknown')}")
                if cover_path:
                    self.log(f"Cover: {os.path.basename(cover_path)}")
                
                # Parse Chapters
                self.update_status(f"Parsing {book_name}...", 0)
                chapters = epub_processor.extract_chapters(epub_path)
                
                if not chapters:
                    self.log(f"Warning: No chapters found in {book_name}")
                    continue
                
                # Update UI List
                if self.init_list:
                    self.init_list(chapters)

                # Prepare Output
                base_name = os.path.splitext(book_name)[0]
                if output_dir_root:
                    output_dir = os.path.join(output_dir_root, f"{base_name}_audiobook")
                else:
                    output_dir = os.path.join(os.path.dirname(epub_path), f"{base_name}_audiobook")
                
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)


                generated_files = []
                total_chapters = len(chapters)
                
                # Estimate Total Duration (Roughly)
                total_chars = sum(len(c.get('content', '')) for c in chapters)
                est_minutes = (total_chars / 900) / speed
                self.log(f"Est. Duration: ~{int(est_minutes)} mins ({total_chapters} chapters)")

                # Process Chapters Concurrently
                import concurrent.futures
                
                # Determine max workers
                # TTS is heavy. If GPU, usually 1 is best to avoid context switching/OOM.
                # If CPU, maybe 2-4 depending on cores. 
                # For safety given "if safe", we default to conservative values.
                max_workers = 1 if use_gpu else min(4, (os.cpu_count() or 1))
                self.log(f"Starting conversion with {max_workers} threads...")

                chapters_done = 0
                progress_lock = threading.Lock()
                start_time = time.time()  # Track start time for ETA

                def process_chapter(idx, chapter):
                    if self._is_cancelled(): return None
                    
                    c_title = chapter['title']
                    c_safe_title = "".join([c for c in c_title if c.isalnum() or c in (' ', '-', '_')]).strip()
                    c_filename = f"{idx+1:03d}_{c_safe_title}.wav"
                    c_filepath = os.path.join(output_dir, c_filename)
                    
                    # Check existing
                    if os.path.exists(c_filepath) and os.path.getsize(c_filepath) > 1024:
                        try:
                            info = sf.info(c_filepath)
                            return idx, c_filepath, info.duration, True # Skipped
                        except: pass
                    
                    # Generate
                    # Update status to processing
                    self.update_status("", chapter_idx=idx, chapter_status="processing")
                    
                    try:
                        if self.tts_engine.generate_audio(chapter['content'], c_filepath, speed=speed, sid=int(speaker_id)):
                             info = sf.info(c_filepath)
                             return idx, c_filepath, info.duration, False # Generated
                        else:
                             raise TTSGenError(f"Generation failed for chapter {idx}")
                    except Exception as e:
                        self.log(f"Error in chapter {idx}: {e}")
                        return idx, None, 0, False # Failed

                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_chapter = {executor.submit(process_chapter, i, ch): i for i, ch in enumerate(chapters)}
                    
                    for future in concurrent.futures.as_completed(future_to_chapter):
                        if self._is_cancelled(): 
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                        
                        try:
                            res_idx, res_path, res_dur, res_skipped = future.result()
                            
                            with progress_lock:
                                chapters_done += 1
                                progress = chapters_done / total_chapters
                                self.update_progress(progress)
                                
                                # Calculate ETA
                                elapsed = time.time() - start_time
                                if chapters_done > 0:
                                    avg_per_chapter = elapsed / chapters_done
                                    remaining_chapters = total_chapters - chapters_done
                                    eta_seconds = int(avg_per_chapter * remaining_chapters)
                                    
                                    if eta_seconds >= 60:
                                        eta_str = f"ETA: {eta_seconds // 60}m {eta_seconds % 60}s"
                                    else:
                                        eta_str = f"ETA: {eta_seconds}s"
                                else:
                                    eta_str = "ETA: Calculating..."
                                
                                ch_title = chapters[res_idx]['title']
                                status_msg = f"Ch {chapters_done}/{total_chapters}: {ch_title[:20]}..."
                                if res_skipped: status_msg += " (Cached)"
                                self.update_status(status_msg, progress, eta_str, chapter_idx=res_idx, chapter_status="done" if res_path else "failed")
                            
                            if res_path:
                                chapters[res_idx]['duration'] = res_dur
                                # We need to maintain order for merging, but generated_files list is append-only
                                # Better to reconstruct generated_files list at the end based on chapters
                                
                        except Exception as exc:
                            self.log(f"Chapter processing generated an exception: {exc}")

                # Reconstruct generated_files in order
                generated_files = []
                for i in range(total_chapters):
                    ch = chapters[i]
                    # We reconstruct the expected path to check existence, 
                    # relying on the fact that if it succeeded, the file is there.
                    safe_title = "".join([c for c in ch['title'] if c.isalnum() or c in (' ', '-', '_')]).strip()
                    fname = f"{i+1:03d}_{safe_title}.wav"
                    fpath = os.path.join(output_dir, fname)
                    if os.path.exists(fpath):
                        generated_files.append(fpath)
                    else:
                        self.log(f"Warning: Chapter {i+1} failed or missing.")
                
                # Post-Processing
                if self._is_cancelled():
                    self.log("Conversion cancelled.")
                elif generated_files:
                    if output_format == "mp3":
                        self.update_status("Converting to MP3...", 1.0)
                        self.log("Converting WAVs to MP3 with metadata...")
                        if not self.audio_builder.check_ffmpeg():
                            self.log("Error: FFmpeg not found, keeping WAV files.")
                        else:
                            total_tracks = len(generated_files)
                            for track_idx, wf in enumerate(generated_files, 1):
                                if self._is_cancelled(): break
                                mp3_file = wf.replace(".wav", ".mp3")
                                
                                # Get chapter title for this track
                                ch_title = chapters[track_idx - 1]['title'] if track_idx <= len(chapters) else f"Chapter {track_idx}"
                                
                                # Prepare metadata for this MP3
                                mp3_metadata = {
                                    'title': book_metadata.get('title'),
                                    'author': book_metadata.get('author'),
                                    'chapter_title': ch_title
                                }
                                
                                try:
                                    if self.audio_builder.convert_to_mp3(
                                        wf, mp3_file, 
                                        metadata=mp3_metadata, 
                                        cover_path=cover_path,
                                        track_num=track_idx,
                                        total_tracks=total_tracks,
                                        quality=quality,
                                        normalize=normalize
                                    ):
                                        self.log(f"Created {os.path.basename(mp3_file)}")
                                        # Delete WAV file if conversion successful
                                        try:
                                            os.remove(wf)
                                        except Exception as e:
                                            self.logger.warning(f"Failed to delete {wf}: {e}")
                                except Exception as conv_err:
                                    self.log(f"Error converting chapter {track_idx}: {conv_err}")

                    elif output_format == "m4b":
                        self.update_status("Merging M4B...", 1.0)
                        self.log("Merging chapters into M4B with metadata...")
                        m4b_path = os.path.join(os.path.dirname(output_dir), f"{base_name}.m4b")
                        metadata_path = os.path.join(output_dir, "metadata.txt")
                        
                        # Create chapter metadata with book info
                        if self.audio_builder.create_chapter_metadata(chapters, metadata_path, book_metadata):
                            if self.audio_builder.merge_chapters_to_m4b(generated_files, m4b_path, metadata_path, cover_path, quality=quality, normalize=normalize):
                                self.log(f"Success! M4B saved to: {m4b_path}")
                                
                                # Delete all WAV files after successful merge
                                self.log("Cleaning up temporary WAV files...")
                                for wf in generated_files:
                                    try:
                                        os.remove(wf)
                                    except Exception as e:
                                        self.logger.warning(f"Failed to delete {wf}: {e}")
                                # Clean up metadata file
                                try:
                                    os.remove(metadata_path)
                                except: pass
                            else:
                                self.log("Error merging M4B (Check FFmpeg).")
                        else:
                            self.log("Error creating metadata.")
                
            # Log total time
            total_elapsed = time.time() - conversion_start_time
            if total_elapsed >= 60:
                time_str = f"{int(total_elapsed // 60)}m {int(total_elapsed % 60)}s"
            else:
                time_str = f"{int(total_elapsed)}s"
            self.log(f"Total conversion time: {time_str}")
            
            self.on_done()

        except Exception as e:
            self.logger.error(f"Worker Error: {e}")
            traceback.print_exc()
            self.log(f"Critical Error: {str(e)}")
            self.on_done()
