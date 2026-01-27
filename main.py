"""
AB-Maker: Audiobook Creator
CustomTkinter UI Implementation
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import logging
from model_manager import ModelManager
from epub_processor import EpubProcessor
from tts_engine import TTSEngine
from audio_builder import AudioBuilder
from config_manager import ConfigManager
from conversion_worker import ConversionWorker

try:
    import winsound
except ImportError:
    winsound = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set appearance mode
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class ABMakerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window setup - 900x700 is optimal for this layout
        self.title("AB-Maker: Audiobook Creator")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Initialize managers
        self.config_mgr = ConfigManager()
        self.model_manager = ModelManager()
        self.epub_processor = EpubProcessor()
        self.tts_engine = TTSEngine()
        self.audio_builder = AudioBuilder()
        
        # State
        self.selected_epubs = []
        self.output_dir = None
        self.current_worker = None
        self.chapters_cache = {}
        
        # Build UI
        self._create_widgets()
        self._load_settings()
        self._check_ffmpeg()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === SECTION 1: Input & Output ===
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(self.input_frame, text="1. Input & Output", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # File selection row
        file_row = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        file_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkButton(file_row, text="Select EPUB", command=self._select_files, width=120).pack(side="left", padx=(0, 10))
        self.file_label = ctk.CTkLabel(file_row, text="No files selected", text_color="gray")
        self.file_label.pack(side="left", fill="x", expand=True)
        
        # Output folder row
        output_row = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        output_row.pack(fill="x", padx=15, pady=(5, 10))
        
        ctk.CTkButton(output_row, text="Output Folder", command=self._select_output, width=120).pack(side="left", padx=(0, 10))
        self.output_label = ctk.CTkLabel(output_row, text="Default (Same as Book)", text_color="gray")
        self.output_label.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(output_row, text="Edit Chapters", command=self._view_chapters, width=100).pack(side="right")
        
        # === SECTION 2: Voice Configuration ===
        self.config_frame = ctk.CTkFrame(self.main_frame)
        self.config_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(self.config_frame, text="2. Voice Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Model selection row
        model_row = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        model_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(model_row, text="Voice Model:").pack(side="left", padx=(0, 10))
        
        models = self.model_manager.list_available_models()
        model_names = [m['name'] for m in models]
        self.model_data = {m['name']: m for m in models}
        
        self.model_var = ctk.StringVar(value=model_names[0] if model_names else "")
        self.model_menu = ctk.CTkOptionMenu(model_row, variable=self.model_var, values=model_names, width=300, command=self._on_model_change)
        self.model_menu.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(model_row, text="Speaker ID:").pack(side="left", padx=(0, 5))
        self.speaker_entry = ctk.CTkEntry(model_row, width=60)
        self.speaker_entry.insert(0, "0")
        self.speaker_entry.pack(side="left")
        
        # Speed slider row
        speed_row = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        speed_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(speed_row, text="Speed:").pack(side="left", padx=(0, 10))
        
        self.speed_var = ctk.DoubleVar(value=1.0)
        self.speed_slider = ctk.CTkSlider(speed_row, from_=0.5, to=2.5, variable=self.speed_var, command=self._on_speed_change, width=300)
        self.speed_slider.pack(side="left", padx=(0, 10))
        
        self.speed_label = ctk.CTkLabel(speed_row, text="1.0x", font=ctk.CTkFont(weight="bold"))
        self.speed_label.pack(side="left")
        
        # GPU switch row
        gpu_row = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        gpu_row.pack(fill="x", padx=15, pady=(5, 10))
        
        self.gpu_var = ctk.BooleanVar(value=False)
        self.gpu_switch = ctk.CTkSwitch(gpu_row, text="Use GPU (CUDA)", variable=self.gpu_var, command=self._on_gpu_change)
        self.gpu_switch.pack(side="left")
        
        # === SECTION 3: Finalize ===
        self.action_frame = ctk.CTkFrame(self.main_frame)
        self.action_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(self.action_frame, text="3. Finalize", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Format selection
        format_row = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        format_row.pack(fill="x", padx=15, pady=5)
        
        self.format_var = ctk.StringVar(value="m4b")
        ctk.CTkRadioButton(format_row, text="M4B Audiobook (Recommended)", variable=self.format_var, value="m4b").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(format_row, text="MP3 Files", variable=self.format_var, value="mp3").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(format_row, text="WAV (Lossless)", variable=self.format_var, value="wav").pack(side="left")
        
        # Action buttons
        btn_row = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=10)
        
        self.start_btn = ctk.CTkButton(btn_row, text="Start Conversion", command=self._start_conversion, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.cancel_btn = ctk.CTkButton(btn_row, text="Cancel", command=self._cancel_conversion, height=40, state="disabled", fg_color="gray")
        self.cancel_btn.pack(side="left", width=100)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self.action_frame)
        self.progress.pack(fill="x", padx=15, pady=(0, 5))
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self.action_frame, text="Ready", text_color="gray")
        self.status_label.pack(padx=15, pady=(0, 10))
        
        # === LOG VIEW ===
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        ctk.CTkLabel(log_frame, text="Log", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.log_box = ctk.CTkTextbox(log_frame, height=150, state="disabled", font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 10))
    
    def _log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
    
    def _load_settings(self):
        # Load persisted settings
        self.speed_var.set(self.config_mgr.get("last_speed", 1.0))
        self._on_speed_change(self.speed_var.get())
        
        self.speaker_entry.delete(0, "end")
        self.speaker_entry.insert(0, self.config_mgr.get("last_speaker_id", "0"))
        
        self.gpu_var.set(self.config_mgr.get("use_gpu", False))
        
        last_model = self.config_mgr.get("last_model")
        if last_model and last_model in self.model_data:
            self.model_var.set(last_model)
        
        self.format_var.set(self.config_mgr.get("output_format", "m4b"))
    
    def _check_ffmpeg(self):
        if not self.audio_builder.check_ffmpeg():
            self._log("WARNING: FFmpeg not found! M4B/MP3 output may fail.")
    
    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="Select EPUB Files",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        if files:
            self.selected_epubs = list(files)
            count = len(self.selected_epubs)
            name = os.path.basename(self.selected_epubs[0])
            self.file_label.configure(text=f"{count} file(s): {name}{'...' if count > 1 else ''}")
            self.config_mgr.add_recent_file(self.selected_epubs[0])
    
    def _select_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir = folder
            self.output_label.configure(text=folder)
    
    def _view_chapters(self):
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
        
        chapters = self.chapters_cache[epub_path]
        
        # Create popup
        popup = ctk.CTkToplevel(self)
        popup.title(f"Chapters: {os.path.basename(epub_path)}")
        popup.geometry("500x400")
        popup.transient(self)
        popup.grab_set()
        
        # Scrollable frame for chapters
        scroll = ctk.CTkScrollableFrame(popup)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        for i, ch in enumerate(chapters):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{i+1}.", width=30).pack(side="left")
            entry = ctk.CTkEntry(row, width=350)
            entry.insert(0, ch['title'])
            entry.pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{len(ch['content'])} chars", text_color="gray").pack(side="left")
        
        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=10)
    
    def _on_speed_change(self, value):
        self.speed_label.configure(text=f"{value:.1f}x")
        self.config_mgr.set("last_speed", value)
    
    def _on_gpu_change(self):
        self.config_mgr.set("use_gpu", self.gpu_var.get())
    
    def _on_model_change(self, value):
        self.config_mgr.set("last_model", value)
        model_info = self.model_data.get(value)
        if model_info and not self.model_manager.is_model_installed(model_info):
            self._log(f"NOTE: Model {value} needs to be downloaded.")
    
    def _on_worker_log(self, msg):
        self.after(0, lambda: self._log(msg))
    
    def _on_worker_progress(self, val):
        self.after(0, lambda: self.progress.set(val))
    
    def _on_worker_status(self, msg, progress=None):
        self.after(0, lambda: self.status_label.configure(text=msg))
        if progress is not None:
            self._on_worker_progress(progress)
    
    def _on_worker_done(self):
        self.current_worker = None
        self.after(0, self._reset_ui)
        
        if winsound:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except:
                pass
    
    def _reset_ui(self):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.progress.set(0)
        self.status_label.configure(text="Ready")
        self._log("Process finished.")
    
    def _start_conversion(self):
        if not self.selected_epubs:
            messagebox.showwarning("No File", "Please select EPUB file(s) first.")
            return
        
        model_name = self.model_var.get()
        model_info = self.model_data.get(model_name)
        if not model_info:
            messagebox.showerror("Error", "Please select a valid model.")
            return
        
        # Download model if needed
        if not self.model_manager.is_model_installed(model_info):
            self._log(f"Downloading {model_name}...")
            self.status_label.configure(text="Downloading Model...")
            
            def dl_progress(current, total):
                if total > 0:
                    self._on_worker_progress(current / total)
            
            if not self.model_manager.download_model(model_info, dl_progress):
                messagebox.showerror("Error", "Model download failed!")
                return
            self._log("Download complete.")
        
        # Setup UI
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        
        # Save format preference
        self.config_mgr.set("output_format", self.format_var.get())
        self.config_mgr.set("last_speaker_id", self.speaker_entry.get())
        
        # Create and start worker
        worker = ConversionWorker(
            self.tts_engine, self.audio_builder,
            log_callback=self._on_worker_log,
            progress_callback=self._on_worker_progress,
            status_callback=self._on_worker_status,
            done_callback=self._on_worker_done
        )
        self.current_worker = worker
        
        worker.start(
            selected_epubs=self.selected_epubs,
            model_info=model_info,
            output_dir_root=self.output_dir or os.path.dirname(self.selected_epubs[0]),
            speed=self.speed_var.get(),
            speaker_id=self.speaker_entry.get(),
            output_format=self.format_var.get(),
            use_gpu=self.gpu_var.get(),
            epub_processor=self.epub_processor
        )
    
    def _cancel_conversion(self):
        if self.current_worker:
            self.current_worker.cancel()
            self.cancel_btn.configure(state="disabled")
    
    def _on_closing(self):
        if self.current_worker:
            if messagebox.askyesno("Confirm Exit", "Conversion in progress. Exit anyway?"):
                self.current_worker.cancel()
                self.destroy()
        else:
            self.destroy()


if __name__ == "__main__":
    app = ABMakerApp()
    app.mainloop()
