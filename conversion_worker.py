import threading
import time
import os
import logging
import soundfile as sf
import traceback

class ConversionWorker:
    def __init__(self, tts_engine, audio_builder, log_callback, progress_callback, status_callback, done_callback):
        self.tts_engine = tts_engine
        self.audio_builder = audio_builder
        self.log = log_callback
        self.update_progress = progress_callback
        self.update_status = status_callback
        self.on_done = done_callback
        
        self._cancel_event = threading.Event()
        self._thread = None
        self.logger = logging.getLogger(__name__)

    def start(self, selected_epubs, model_info, output_dir_root, speed, speaker_id, output_format, use_gpu, epub_processor):
        """Starts the conversion process in a separate thread."""
        self._cancel_event.clear()
        self._thread = threading.Thread(
            target=self._run_conversion,
            args=(selected_epubs, model_info, output_dir_root, speed, speaker_id, output_format, use_gpu, epub_processor),
            daemon=True
        )
        self._thread.start()

    def cancel(self):
        """Signals the worker to cancel."""
        self._cancel_event.set()
        self.log("Stopping... please wait for current task to finish.")

    def _is_cancelled(self):
        return self._cancel_event.is_set()

    def _run_conversion(self, selected_epubs, model_info, output_dir_root, speed, speaker_id, output_format, use_gpu, epub_processor):
        try:
            # 1. Initialize TTS Model
            self.update_status("Initializing TTS...", 0)
            
            # Setup config for TTS
            from model_manager import ModelManager # Imported here to avoid circular dependency if any, though none currently
            # Assuming model_info has paths relative to models_dir, we need absolute paths or correct relative ones
            # For now passing the config as is, relying on tts_engine to handle valid paths if they are correct
            # But tts_engine expects model_dir to be set.
            
            # We need to construct the model_dir path. 
            # In main.py it was: os.path.join(model_manager.models_dir, model_info['extracted_dir'])
            # We'll assume the caller (main UI) has pre-validated this or passed full paths.
            # Actually, let's just do it here to be safe if model_info is raw from config.
            
            # Helper to get models dir (assuming standard layout)
            models_dir = os.path.join(os.getcwd(), "models") 
            model_path = os.path.join(models_dir, model_info['extracted_dir'])
            
            config = model_info.copy()
            config['model_dir'] = model_path
            config['provider'] = "cuda" if use_gpu else "cpu"

            if use_gpu:
                self.log(f"Initializing TTS with GPU (CUDA)...")
            else:
                self.log(f"Initializing TTS with CPU...")

            if not self.tts_engine.initialize_model(config):
                self.log("Error: Failed to initialize TTS engine.")
                self.on_done() # Signal completion with error
                return

            total_books = len(selected_epubs)
            
            for b_idx, epub_path in enumerate(selected_epubs):
                if self._is_cancelled(): break
                
                book_name = os.path.basename(epub_path)
                self.log(f"Processing Book {b_idx+1}/{total_books}: {book_name}")
                
                # Parse Chapters
                self.update_status(f"Parsing {book_name}...", 0)
                chapters = epub_processor.extract_chapters(epub_path)
                
                if not chapters:
                    self.log(f"Warning: No chapters found in {book_name}")
                    continue

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
                    if self.tts_engine.generate_audio(chapter['content'], c_filepath, speed=speed, sid=int(speaker_id)):
                         info = sf.info(c_filepath)
                         return idx, c_filepath, info.duration, False # Generated
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
                                
                                ch_title = chapters[res_idx]['title']
                                status_msg = f"Completed Ch {res_idx+1}: {ch_title[:20]}..."
                                if res_skipped: status_msg += " (Cached)"
                                self.update_status(status_msg, progress)
                            
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
                        self.log("Converting WAVs to MP3...")
                        if not self.audio_builder.check_ffmpeg():
                            self.log("Error: FFmpeg not found, keeping WAV files.")
                        else:
                            for wf in generated_files:
                                if self._is_cancelled(): break
                                mp3_file = wf.replace(".wav", ".mp3")
                                if self.audio_builder.convert_to_mp3(wf, mp3_file):
                                    self.log(f"Created {os.path.basename(mp3_file)}")
                                    # Optional: Delete WAV
                                    # os.remove(wf) 

                    elif output_format == "m4b":
                        self.update_status("Merging M4B...", 1.0)
                        self.log("Merging chapters into M4B...")
                        m4b_path = os.path.join(os.path.dirname(output_dir), f"{base_name}.m4b")
                        metadata_path = os.path.join(output_dir, "metadata.txt")
                        
                        # Re-verify durations if we skipped generation
                        # (Actually we did that in loop, so `chapters` should have duration)
                        
                        if self.audio_builder.create_chapter_metadata(chapters, metadata_path):
                            if self.audio_builder.merge_chapters_to_m4b(generated_files, m4b_path, metadata_path):
                                self.log(f"Success! M4B saved to: {m4b_path}")
                            else:
                                self.log("Error merging M4B (Check FFmpeg).")
                        else:
                            self.log("Error creating metadata.")
                
            self.on_done()

        except Exception as e:
            self.logger.error(f"Worker Error: {e}")
            traceback.print_exc()
            self.log(f"Critical Error: {str(e)}")
            self.on_done()
