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
from tkinterdnd2 import DND_FILES, TkinterDnD
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


class ABMakerApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Window setup - 900x700 is optimal for this layout
        self.title("AB-Maker: Audiobook Creator")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Register Drop Target
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._on_drop)
        
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
        self.custom_cover_path = None  # User-selected custom cover image
        
        # Build UI
        self._create_widgets()
        self._load_settings()
        self._check_ffmpeg()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _on_drop(self, event):
        """Handle file drop event."""
        if event.data:
            # tkinterdnd2 returns path in curly braces if it has spaces {path/to/file}
            file_path = event.data
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            # Handle multiple files - simple logic for now: take first valid EPUB
            # If multiple files are dropped, DND might return them as a list string
            # For robustness, we check if it's an existing file
            if os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.epub':
                    self.selected_epubs = [file_path]
                    self._update_file_label()
                    self.config_mgr.add_recent_file(file_path)
                    self._log(f"Dropped file: {os.path.basename(file_path)}")
                elif ext in ['.jpg', '.jpeg', '.png']:
                    self.custom_cover_path = file_path
                    self.cover_label.configure(text=f"{os.path.basename(file_path)} (Dropped)")
                    self._log(f"Dropped cover: {os.path.basename(file_path)}")

    def _update_file_label(self):
        """Helper to update the file label text."""
        if self.selected_epubs:
            count = len(self.selected_epubs)
            name = os.path.basename(self.selected_epubs[0])
            self.file_label.configure(text=f"{count} file(s): {name}{'...' if count > 1 else ''}")
        else:
            self.file_label.configure(text="No files selected")
    
    def _create_widgets(self):
        # Configure grid layout (1x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === LEFT SIDEBAR ===
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        # Logo / Title
        ctk.CTkLabel(self.sidebar_frame, text="AB-Maker 🎧", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Recent Files Label
        ctk.CTkLabel(self.sidebar_frame, text="Recent Files", text_color="gray", anchor="w").grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        # Recent Files List (Scrollable)
        self.recent_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.recent_scroll.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.recent_scroll.grid_columnconfigure(0, weight=1)
        
        # Theme Toggle (Bottom)
        self.theme_switch = ctk.CTkSwitch(self.sidebar_frame, text="Dark Mode", command=self._toggle_theme)
        self.theme_switch.grid(row=5, column=0, padx=20, pady=20, sticky="s")
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()

        # === MAIN CONTENT (RIGHT) ===
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # CARD 1: Book & Cover
        self.book_card = ctk.CTkFrame(self.main_view)
        self.book_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(self.book_card, text="📖 Book & Cover", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Row 1: EPUB | Drop Target Hint
        row1 = ctk.CTkFrame(self.book_card, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)
        
        self.select_epub_btn = ctk.CTkButton(row1, text="📂 Select EPUB", command=self._select_files, width=140)
        self.select_epub_btn.pack(side="left", padx=5)
        
        self.file_label = ctk.CTkLabel(row1, text="Drag & Drop EPUB here...", text_color="gray")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)
        
        ctk.CTkButton(row1, text="📝 Edit Chapters", command=self._view_chapters, width=120, fg_color="transparent", border_width=1).pack(side="right", padx=5)
        
        # Row 2: Cover | Output
        row2 = ctk.CTkFrame(self.book_card, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(5, 10))
        
        self.select_cover_btn = ctk.CTkButton(row2, text="🖼️ Custom Cover", command=self._select_cover, width=140, fg_color="transparent", border_width=1)
        self.select_cover_btn.pack(side="left", padx=5)
        
        self.cover_label = ctk.CTkLabel(row2, text="Default Cover", text_color="gray")
        self.cover_label.pack(side="left", padx=10)
        
        self.clear_cover_btn = ctk.CTkButton(row2, text="❌", command=self._clear_cover, width=30, fg_color="transparent", text_color="red", hover_color="#fee2e2")
        self.clear_cover_btn.pack(side="left")
        
        ctk.CTkButton(row2, text="📂 Output Folder", command=self._select_output, width=120, fg_color="transparent", border_width=1).pack(side="right", padx=5)
        self.output_label = ctk.CTkLabel(row2, text="", text_color="gray") # Hidden by default until selected
        
        # CARD 2: Voice Strategy
        self.voice_card = ctk.CTkFrame(self.main_view)
        self.voice_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(self.voice_card, text="🗣️ Voice Strategy", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        v_row = ctk.CTkFrame(self.voice_card, fg_color="transparent")
        v_row.pack(fill="x", padx=10, pady=5)
        
        # Model
        # Model
        self.model_var = ctk.StringVar()
        
        # Initialize model data here
        models = self.model_manager.list_available_models()
        self.model_data = {m['name']: m for m in models}
        model_names = list(self.model_data.keys())
        
        self.model_menu = ctk.CTkOptionMenu(v_row, variable=self.model_var, values=model_names, width=220, command=self._on_model_change)
        self.model_menu.pack(side="left", padx=5)
        
        if model_names:
            self.model_var.set(model_names[0])
        
        # Speaker ID
        ctk.CTkLabel(v_row, text="Speaker ID:").pack(side="left", padx=(15, 5))
        self.speaker_entry = ctk.CTkEntry(v_row, width=50)
        self.speaker_entry.pack(side="left")
        self.speaker_entry.insert(0, "0")
        
        # Speed
        ctk.CTkLabel(v_row, text="Speed:").pack(side="left", padx=(15, 5))
        self.speed_var = ctk.DoubleVar(value=1.0)
        self.speed_slider = ctk.CTkSlider(v_row, from_=0.5, to=2.5, width=120, variable=self.speed_var, command=self._on_speed_change)
        self.speed_slider.pack(side="left", padx=5)
        self.speed_label = ctk.CTkLabel(v_row, text="1.0x", font=ctk.CTkFont(weight="bold"))
        self.speed_label.pack(side="left")
        
        # GPU
        self.gpu_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(v_row, text="🚀 GPU", variable=self.gpu_var, command=self._on_gpu_change, width=80).pack(side="right", padx=10)

        # CARD 3: Action & Progress
        self.action_card = ctk.CTkFrame(self.main_view)
        self.action_card.pack(fill="x", pady=(0, 10))
        
        a_row = ctk.CTkFrame(self.action_card, fg_color="transparent")
        a_row.pack(fill="x", padx=10, pady=10)
        
        # Format
        self.format_var = ctk.StringVar(value="m4b")
        ctk.CTkRadioButton(a_row, text="M4B", variable=self.format_var, value="m4b").pack(side="left", padx=10)
        ctk.CTkRadioButton(a_row, text="MP3", variable=self.format_var, value="mp3").pack(side="left", padx=10)
        
        # Start Button
        self.start_btn = ctk.CTkButton(a_row, text="⚡ START CONVERSION", command=self._start_conversion, font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.start_btn.pack(side="right", ipadx=20, padx=5)
        
        self.cancel_btn = ctk.CTkButton(a_row, text="STOP", command=self._cancel_conversion, fg_color="#ef4444", hover_color="#dc2626", width=80, height=40, state="disabled")
        self.cancel_btn.pack(side="right", padx=5)

        # Progress Section
        p_row = ctk.CTkFrame(self.action_card, fg_color="transparent")
        p_row.pack(fill="x", padx=15, pady=(0, 15))
        
        self.progress = ctk.CTkProgressBar(p_row, height=12)
        self.progress.pack(fill="x", pady=(0, 5))
        self.progress.set(0)
        
        # Stats Row
        s_row = ctk.CTkFrame(p_row, fg_color="transparent")
        s_row.pack(fill="x")
        self.status_label = ctk.CTkLabel(s_row, text="Ready to create magic ✨", text_color="gray")
        self.status_label.pack(side="left")
        
        self.eta_label = ctk.CTkLabel(s_row, text="--:-- remaining", text_color="gray")
        self.eta_label.pack(side="right")
        
        # LOG
        self.log_box = ctk.CTkTextbox(self.main_view, height=120, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.pack(fill="both", expand=True)
        self.log_box.configure(state="disabled")

    def _toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
    
    def _log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
    
    def _load_settings(self):
        """Load saved settings and history."""
        # Load recent files
        self._load_recent_files()
        
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

    def _load_recent_files(self):
        """Populate the recent files sidebar."""
        # Clear existing
        for widget in self.recent_scroll.winfo_children():
            widget.destroy()
            
        recent = self.config_mgr.get("recent_files", [])
        if not recent:
            ctk.CTkLabel(self.recent_scroll, text="No recent files", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=10)
            return
            
        for r_path in recent:
            if not os.path.exists(r_path): continue
            
            # Truncate long names
            name = os.path.basename(r_path)
            if len(name) > 20: name = name[:18] + "..."
            
            btn = ctk.CTkButton(
                self.recent_scroll, 
                text=name, 
                command=lambda p=r_path: self._load_recent_book(p),
                fg_color="transparent", 
                border_width=0,
                anchor="w",
                height=28,
                font=ctk.CTkFont(size=11),
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25")
            )
            btn.pack(fill="x", pady=1, padx=2)

    def _load_recent_book(self, path):
        """Load a book from history."""
        if os.path.exists(path):
            self.selected_epubs = [path]
            self.config_mgr.add_recent_file(path)
            self._update_file_label()
            self._load_recent_files() # Refresh order
        else:
            messagebox.showerror("Error", "File not found.")
    
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
    
    def _select_cover(self):
        """Allow user to select a custom cover image."""
        cover_file = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")]
        )
        if cover_file:
            self.custom_cover_path = cover_file
            self.cover_label.configure(text=os.path.basename(cover_file))
            self._log(f"Custom cover selected: {os.path.basename(cover_file)}")
    
    def _clear_cover(self):
        """Clear the custom cover selection."""
        self.custom_cover_path = None
        self.cover_label.configure(text="Default (From EPUB)")
    
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
    
    def _on_worker_status(self, msg, progress=None, eta=None):
        self.after(0, lambda: self.status_label.configure(text=msg))
        if progress is not None:
            self._on_worker_progress(progress)
        if eta is not None:
            self.after(0, lambda: self.eta_label.configure(text=eta))
    
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
        self.eta_label.configure(text="")
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
            self.update()  # Force UI update
            
            last_logged_pct = [0]  # Use list for mutable closure
            
            def dl_progress(current, total):
                if total > 0:
                    pct = int((current / total) * 100)
                    self._on_worker_progress(current / total)
                    
                    # Log every 10%
                    if pct >= last_logged_pct[0] + 10:
                        last_logged_pct[0] = pct
                        mb_current = current / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        self.after(0, lambda: self._log(f"  Download: {mb_current:.1f} MB / {mb_total:.1f} MB ({pct}%)"))
            
            if not self.model_manager.download_model(model_info, dl_progress):
                messagebox.showerror("Error", "Model download failed!")
                return
            self._log("Download complete. Extracting...")
        
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
            epub_processor=self.epub_processor,
            custom_cover_path=self.custom_cover_path
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
