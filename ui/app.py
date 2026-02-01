import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import threading
import logging
import tempfile
import time

# Core imports
from model_manager import ModelManager
from epub_processor import EpubProcessor
from tts_engine import TTSEngine
from audio_builder import AudioBuilder
from config_manager import ConfigManager
from conversion_worker import ConversionWorker

# UI imports
from ui.icons import generate_icons
from ui.sidebar import SidebarUI
from ui.book_card import BookCardUI
from ui.voice_card import VoiceCardUI
from ui.action_card import ActionCardUI
from ui.dialogs.chapter_editor import ChapterEditorDialog
from ui.dialogs.model_manager import ModelManagerDialog
from ui.dialogs.about import AboutDialog

class ABMakerApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, 
                 config_manager=None,
                 model_manager=None,
                 epub_processor=None,
                 tts_engine=None,
                 audio_builder=None):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Audio playback state
        self.audio_stream = None
        self.audio_playing = False
            
        # Window setup
        self.title("AB-Maker: Audiobook Creator")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Register Drop Target
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._on_drop)
        
        # Initialize managers with dependency injection
        self.config_mgr = config_manager or ConfigManager()
        self._setup_logging()
        
        self.model_manager = model_manager or ModelManager(models_dir=self.config_mgr.get_models_dir())
        self.epub_processor = epub_processor or EpubProcessor(cache_dir=self.config_mgr.get_cache_dir())
        self.tts_engine = tts_engine or TTSEngine()
        self.audio_builder = audio_builder or AudioBuilder()
        
        # State
        self.selected_epubs = []
        self.output_dir = None
        self.current_worker = None
        self.chapters_cache = {}
        self.custom_cover_path = None
        self.icons = generate_icons()
        self.model_data = {}
        self._preview_cancelled = False
        
        # Build UI
        self._create_widgets()
        self._load_settings()
        self._check_ffmpeg()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_logging(self):
        log_dir = self.config_mgr.get_logs_dir()
        log_file = os.path.join(log_dir, "app.log")
        from logging.handlers import RotatingFileHandler
        
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Keep existing handlers if any to avoid duplication on reload (not issue usually)
        if not logger.handlers:
           file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3, encoding='utf-8')
           file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
           file_handler.setFormatter(file_formatter)
           logger.addHandler(file_handler)
           logging.info("Logging initialized.")

    def _create_widgets(self):
        # Configure layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = SidebarUI(self, self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Main View
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Cards
        self.book_card = BookCardUI(self.main_view, self, self.icons)
        self.book_card.pack(fill="x", pady=(0, 15))
        
        self.voice_card = VoiceCardUI(self.main_view, self, self.icons)
        self.voice_card.pack(fill="x", pady=(0, 15))
        
        self.action_card = ActionCardUI(self.main_view, self)
        self.action_card.pack(fill="x", pady=(0, 10))
        
        # Load initial model list
        self.refresh_model_list()

    def _load_settings(self):
        # Sidebar History
        self.sidebar.load_recent_files(self.config_mgr.get_recent_files())
        
        # Voice Settings
        speed = self.config_mgr.get("last_speed", 1.0)
        self.voice_card.speed_var.set(speed)
        self.on_speed_change(speed)
        
        self.voice_card.speaker_entry.delete(0, "end")
        self.voice_card.speaker_entry.insert(0, self.config_mgr.get("last_speaker_id", "0"))
        
        self.voice_card.gpu_var.set(self.config_mgr.get("use_gpu", False))
        
        last_model = self.config_mgr.get("last_model")
        if last_model and last_model in self.model_data:
            self.voice_card.model_var.set(last_model)
            
        # Action Settings
        self.action_card.format_var.set(self.config_mgr.get("output_format", "m4b"))
        self.action_card.quality_var.set(self.config_mgr.get("last_quality", "Medium"))
        self.action_card.normalize_var.set(self.config_mgr.get("normalize", False))

    def _check_ffmpeg(self):
        if not self.audio_builder.check_ffmpeg():
            self._log("WARNING: FFmpeg not found! M4B/MP3 output may fail.")

    def _log(self, message):
        self.action_card.log(message)

    # --- Actions (Delegated from UI modules) ---
    
    def on_speed_change(self, value):
        self.voice_card.update_speed_label(value)
        self.config_mgr.set("last_speed", value)
        
    def on_gpu_change(self):
        self.config_mgr.set("use_gpu", self.voice_card.gpu_var.get())
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        # Voice settings
        self.voice_card.speed_var.set(1.0)
        self.voice_card.update_speed_label(1.0)
        self.voice_card.speaker_entry.delete(0, "end")
        self.voice_card.speaker_entry.insert(0, "0")
        self.voice_card.gpu_var.set(False)
        
        # Action settings
        self.action_card.format_var.set("m4b")
        self.action_card.quality_var.set("Medium")
        self.action_card.normalize_var.set(False)
        
        # Save to config
        self.config_mgr.set("last_speed", 1.0)
        self.config_mgr.set("last_speaker_id", "0")
        self.config_mgr.set("use_gpu", False)
        self.config_mgr.set("output_format", "m4b")
        self.config_mgr.set("last_quality", "Medium")
        self.config_mgr.set("normalize", False)
        
        self._log("Settings reset to defaults")
        
    def refresh_model_list(self):
        show_all = self.voice_card.advanced_models_var.get()
        models = self.model_manager.list_available_models(only_recommended=not show_all)
        self.model_data = {m['name']: m for m in models}
        model_names = list(self.model_data.keys())
        self.voice_card.update_model_list(model_names, self.voice_card.model_var.get())
        
    def on_model_change(self, value):
        self.config_mgr.set("last_model", value)
        model_info = self.model_data.get(value)
        if model_info and not self.model_manager.is_model_installed(model_info):
            self._log(f"NOTE: Model {value} needs to be downloaded.")
        
        # Update Character Voices button visibility based on model capabilities
        if model_info:
            num_speakers = model_info.get('num_speakers', 1)
            self.voice_card.update_character_voices_button(num_speakers)
            
    def open_model_manager(self):
        ModelManagerDialog(self, self.model_manager, self.icons, self.refresh_model_list)
        
    def open_pause_settings(self):
        from ui.dialogs.pause_settings import PauseSettingsDialog
        PauseSettingsDialog(self, self.config_mgr, self.icons)
        
    def open_character_voices(self):
        from ui.dialogs.character_voices import CharacterVoiceDialog
        
        if not self.selected_epubs:
            messagebox.showwarning("No Book", "Please select a book first.")
            return
        
        epub_path = self.selected_epubs[0]
        if epub_path not in self.chapters_cache:
            try:
                self.chapters_cache[epub_path] = self.epub_processor.extract_chapters(epub_path)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to read chapters: {ex}")
                return
        
        model_name = self.voice_card.model_var.get()
        model_info = self.model_data.get(model_name)
        
        if not model_info:
            messagebox.showerror("Error", "Please select a model first.")
            return
        
        def on_save_assignments(assignments):
            # Store character voice assignments in config
            book_id = os.path.basename(epub_path)
            self.config_mgr.set(f"character_voices_{book_id}", assignments)
            self._log(f"Character voice assignments saved: {len(assignments)} characters")
        
        CharacterVoiceDialog(
            self, 
            self.chapters_cache[epub_path], 
            model_info, 
            self.icons, 
            on_save_assignments
        )
        
    def open_about(self):
        AboutDialog(self, self.icons)
            
    def load_book(self, path):
        if os.path.exists(path):
            self.selected_epubs = [path]
            self.config_mgr.add_recent_file(path)
            self.book_card.update_file_label(self.selected_epubs)
            self.sidebar.load_recent_files(self.config_mgr.get_recent_files())
        else:
            messagebox.showerror("Error", "File not found.")

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select EPUB Files",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        if files:
            self.selected_epubs = list(files)
            self.config_mgr.add_recent_file(self.selected_epubs[0])
            self.book_card.update_file_label(self.selected_epubs)
            self.sidebar.load_recent_files(self.config_mgr.get_recent_files())

    def _on_drop(self, event):
        if event.data:
            file_path = event.data
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            if os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.epub':
                    self.load_book(file_path)
                    self._log(f"Dropped file: {os.path.basename(file_path)}")
                elif ext in ['.jpg', '.jpeg', '.png']:
                    self.custom_cover_path = file_path
                    self.book_card.update_cover_label(file_path)
                    self._log(f"Dropped cover: {os.path.basename(file_path)}")

    def select_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir = folder
            self.book_card.update_output_label(folder)
            
    def select_cover(self):
        cover_file = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")]
        )
        if cover_file:
            self.custom_cover_path = cover_file
            self.book_card.update_cover_label(cover_file)
            self._log(f"Custom cover selected: {os.path.basename(cover_file)}")
            
    def clear_cover(self):
        self.custom_cover_path = None
        self.book_card.update_cover_label(None)
        
    def view_chapters(self):
        if not self.selected_epubs:
            messagebox.showwarning("No File", "Please select an EPUB first.")
            return
        
        epub_path = self.selected_epubs[0]
        if epub_path not in self.chapters_cache:
            try:
                self.chapters_cache[epub_path] = self.epub_processor.extract_chapters(epub_path)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to read chapters: {ex}")
                return
        
        def save_callback():
             return self.epub_processor.save_chapters(epub_path, self.chapters_cache[epub_path])
             
        ChapterEditorDialog(self, self.chapters_cache[epub_path], self.icons, save_callback)

    # --- Worker Callbacks ---
    def _on_worker_log(self, msg):
        self.after(0, lambda: self._log(msg))
    
    def _on_worker_progress(self, val):
        self.after(0, lambda: self.action_card.progress.set(val))
    
    def _on_worker_status(self, msg, progress=None, eta=None, chapter_idx=None, chapter_status=None):
        self.after(0, lambda: self.action_card.status_label.configure(text=msg))
        if progress is not None:
             self._on_worker_progress(progress)
        if eta is not None:
             self.after(0, lambda: self.action_card.eta_label.configure(text=eta))
        if chapter_idx is not None and chapter_status:
             self.after(0, lambda: self.action_card.update_chapter_status(chapter_idx, chapter_status))

    def _on_worker_done(self):
        self.current_worker = None
        self.after(0, self.action_card.reset_ui)
        # Beep notification
        print('\a')
        
        # Mark files as completed
        for epub_path in self.selected_epubs:
            self.config_mgr.set_file_status(epub_path, "completed")
        self.sidebar.load_recent_files(self.config_mgr.get_recent_files())
            
    def _init_chapter_list(self, chapters):
        self.after(0, lambda: self.action_card.init_chapter_list(chapters))

    # --- Main Logic ---
    def start_conversion(self):
        if not self.selected_epubs:
            messagebox.showwarning("No File", "Please select EPUB file(s) first.")
            return
        
        model_name = self.voice_card.model_var.get()
        model_info = self.model_data.get(model_name)
        if not model_info:
            messagebox.showerror("Error", "Please select a valid model.")
            return
            
        # UI Setup
        self.action_card.set_converting_state()
        
        # Save settings
        self.config_mgr.set("output_format", self.action_card.format_var.get())
        self.config_mgr.set("last_quality", self.action_card.quality_var.get())
        self.config_mgr.set("last_speaker_id", self.voice_card.speaker_entry.get())
        self.config_mgr.set("normalize", self.action_card.normalize_var.get())
        
        # Mark files as in_progress
        for epub_path in self.selected_epubs:
            self.config_mgr.set_file_status(epub_path, "in_progress")
        self.sidebar.load_recent_files(self.config_mgr.get_recent_files())

        def run_async_start():
            # Download flow
            if not self.model_manager.is_model_installed(model_info):
                self.after(0, lambda: self._log(f"Downloading {model_name}..."))
                self.after(0, lambda: self.action_card.status_label.configure(text="Downloading Model..."))
                
                last_logged_pct = [0]
                def dl_progress(current, total):
                    if total > 0:
                        pct = int((current / total) * 100)
                        self._on_worker_progress(current / total)
                        if pct >= last_logged_pct[0] + 10:
                            last_logged_pct[0] = pct
                            self.after(0, lambda: self._log(f"  DL: {pct}%"))
                
                success = self.model_manager.download_model(model_info, dl_progress)
                if not success:
                    self.after(0, lambda: messagebox.showerror("Error", "Model download failed!"))
                    self.after(0, self.action_card.reset_ui)
                    return
            
            # Start Worker
            worker = ConversionWorker(
                self.tts_engine, self.audio_builder,
                log_callback=self._on_worker_log,
                progress_callback=self._on_worker_progress,
                status_callback=self._on_worker_status,
                done_callback=self._on_worker_done,
                init_list_callback=self._init_chapter_list
            )
            self.current_worker = worker
            
            # Load pause settings from config
            pause_settings = {
                'sentence_pause_ms': self.config_mgr.get("pause_sentence", 700),
                'clause_pause_ms': self.config_mgr.get("pause_clause", 250),
                'paragraph_pause_ms': self.config_mgr.get("pause_paragraph", 1500),
                'dialogue_pause_ms': self.config_mgr.get("pause_dialogue", 400)
            }
            
            # Load character voice assignments if available for multi-speaker models
            character_voices = None
            if model_info.get('num_speakers', 1) > 1:
                book_id = os.path.basename(self.selected_epubs[0])
                character_voices = self.config_mgr.get(f"character_voices_{book_id}", None)
                if character_voices:
                    self._log(f"Using character voice assignments: {len(character_voices)} characters")
            
            worker.start(
                selected_epubs=self.selected_epubs,
                model_info=model_info,
                output_dir_root=self.output_dir or os.path.dirname(self.selected_epubs[0]),
                speed=self.voice_card.speed_var.get(),
                speaker_id=self.voice_card.speaker_entry.get(),
                output_format=self.action_card.format_var.get(),
                quality=self.action_card.quality_var.get(),
                use_gpu=self.voice_card.gpu_var.get(),
                epub_processor=self.epub_processor,
                custom_cover_path=self.custom_cover_path,
                models_dir=self.config_mgr.get_models_dir(),
                normalize=self.action_card.normalize_var.get(),
                pause_settings=pause_settings,
                character_voices=character_voices
            )

        threading.Thread(target=run_async_start, daemon=True).start()

    def cancel_conversion(self):
        if self.current_worker:
            self.current_worker.cancel()
            self.action_card.cancel_btn.configure(state="disabled")

    def preview_voice(self):
        model_name = self.voice_card.model_var.get()
        model_info = self.model_data.get(model_name)
        
        if not model_info: return
        if not self.model_manager.is_model_installed(model_info):
            messagebox.showinfo("Preview", "Please download the model first.")
            return

        if self.current_worker:
            messagebox.showwarning("Busy", "Cannot preview while conversion is in progress.")
            return

        self.voice_card.preview_btn.configure(state="disabled")
        self.action_card.status_label.configure(text="Generating preview...")
        self._preview_cancelled = False
        
        def run_preview():
            try:
                fd, temp_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                
                # Get preview text - either from random chapter or default
                preview_text = "This is a preview of the selected voice and speed settings."
                preview_source = "default"
                
                # Check if we have chapters loaded and can do a random preview
                if self.selected_epubs and self.selected_epubs[0] in self.chapters_cache:
                    try:
                        import random
                        chapters = self.chapters_cache[self.selected_epubs[0]]
                        
                        # Filter to only selected chapters
                        selected_chapters = [ch for ch in chapters if ch.get('selected', True)]
                        
                        if selected_chapters:
                            # Randomly select a chapter
                            random_chapter = random.choice(selected_chapters)
                            chapter_title = random_chapter.get('title', 'Unknown Chapter')
                            chapter_content = random_chapter.get('content', '')
                            
                            # Split into sentences and pick 2 random consecutive ones
                            sentences = self.tts_engine._split_into_sentences(chapter_content)
                            
                            if len(sentences) >= 2:
                                # Pick 2 consecutive sentences for better context
                                max_start = len(sentences) - 2
                                start_idx = random.randint(0, max_start) if max_start > 0 else 0
                                preview_text = " ".join(sentences[start_idx:start_idx + 2])
                                preview_source = f"from '{chapter_title}'"
                            elif len(sentences) == 1:
                                preview_text = sentences[0]
                                preview_source = f"from '{chapter_title}'"
                            else:
                                # No sentences found, use first 200 chars
                                preview_text = chapter_content[:200].strip()
                                preview_source = f"from '{chapter_title}'"
                    except Exception as e:
                        self._log(f"Could not generate random preview: {e}")
                
                text = preview_text
                speed = self.voice_card.speed_var.get()
                sid = int(self.voice_card.speaker_entry.get())
                
                # Update status with preview source
                status_msg = f"Previewing {preview_source}..."
                self.after(0, lambda: self.action_card.status_label.configure(text=status_msg))
                self._log(f"Preview: {preview_source}")
                
                config = model_info.copy()
                config['model_dir'] = os.path.join(self.config_mgr.get_models_dir(), model_info['extracted_dir'])
                config['provider'] = "cuda" if self.voice_card.gpu_var.get() else "cpu"

                if self.tts_engine.initialize_model(config):
                    if self.tts_engine.generate_audio(text, temp_path, speed=speed, sid=sid):
                        # Play audio using sounddevice
                        try:
                            import sounddevice as sd
                            import soundfile as sf
                            
                            data, samplerate = sf.read(temp_path)
                            self.audio_playing = True
                            sd.play(data, samplerate)
                            
                            self.after(0, lambda: self.action_card.status_label.configure(text=f"Playing preview {preview_source}..."))
                            
                            # Wait for playback to finish (non-blocking)
                            while sd.get_stream().active and not self._preview_cancelled:
                                time.sleep(0.1)
                            
                            if self._preview_cancelled:
                                sd.stop()
                            
                            self.audio_playing = False
                        except Exception as pe:
                            self._log(f"Playback error: {pe}")
                    else:
                        self.after(0, lambda: messagebox.showerror("Error", "Failed to generate preview audio."))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "Failed to initialize TTS model."))
                    
                # Cleanup
                for _ in range(3):
                    try:
                        os.remove(temp_path)
                        break
                    except: time.sleep(0.5)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Preview failed: {e}"))
            finally:
                self.after(0, lambda: self.voice_card.preview_btn.configure(state="normal"))
                self.after(0, lambda: self.action_card.status_label.configure(text="Ready"))

        threading.Thread(target=run_preview, daemon=True).start()

    def _on_closing(self):
        if self.current_worker:
            if messagebox.askyesno("Confirm Exit", "Conversion in progress. Exit anyway?"):
                self.current_worker.cancel()
                self.destroy()
        else:
            self.destroy()
