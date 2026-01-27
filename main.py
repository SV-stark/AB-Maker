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
import tempfile
from PIL import Image, ImageDraw
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
        self.icons = self._generate_icons()
        
        # Build UI
        self._create_widgets()
        self._load_settings()
        self._check_ffmpeg()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _generate_icons(self):
        """Generates icons programmatically using Pillow."""
        icons = {}
        # Colors suitable for light/dark blue theme
        colors = {"blue": "#3b82f6", "red": "#ef4444", "gray": "#64748b", "white": "#ffffff", "text": "#1e293b"}
        
        def draw_icon(name, color):
            size = (20, 20)
            img = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            if name == "folder":
                draw.polygon([(2,18), (2,6), (9,6), (11,4), (18,4), (18,18)], fill=color)
            
            elif name == "image":
                draw.rectangle([3,5,17,17], outline=color, width=2)
                draw.ellipse([5,7,8,10], fill=color)
                draw.polygon([(4,16), (8,12), (12,16)], fill=color)
                draw.polygon([(10,16), (14,12), (17,16)], fill=color)

            elif name == "list":
                for y in [6, 10, 14]:
                    draw.rectangle([4, y, 16, y+2], fill=color)
                for y in [6, 10, 14]:
                    draw.rectangle([2, y, 3, y+2], fill=color)

            elif name == "trash":
                draw.rectangle([6,6,14,17], fill=color) # bin
                draw.line([(5,5), (15,5)], fill=color, width=2) # lid line
                draw.rectangle([8,3,12,5], fill=color) # handle

            elif name == "save":
                draw.rectangle([4,4,16,16], fill=color)
                draw.rectangle([6,4,14,8], fill="#ffffff") # metal clip
                draw.rectangle([6,12,14,16], fill="#ffffff") # label

            elif name == "play":
                draw.polygon([(6,5), (6,15), (16,10)], fill=color)
                
            elif name == "gear": # settings/manage
                 draw.ellipse([3,3,17,17], outline=color, width=2)
                 draw.ellipse([7,7,13,13], fill=color)

            return ctk.CTkImage(img, size=(16, 16))

        icons['folder'] = draw_icon('folder', colors['blue'])
        icons['image'] = draw_icon('image', colors['gray'])
        icons['list'] = draw_icon('list', colors['gray'])
        icons['trash'] = draw_icon('trash', colors['red'])
        icons['save'] = draw_icon('save', colors['blue'])
        icons['play'] = draw_icon('play', colors['blue'])
        icons['gear'] = draw_icon('gear', colors['gray'])
        
        return icons
        
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
        
        self.file_label = ctk.CTkLabel(row1, text="Drag & Drop EPUB here...", text_color="gray")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)
        # Select Files Button
        self.select_files_btn = ctk.CTkButton(row1, text="Browse", image=self.icons['folder'], compound="left", command=self._select_files, width=100)
        self.select_files_btn.pack(side="right", padx=10)
        
        # Row 2: Cover & Chapters
        row2 = ctk.CTkFrame(self.book_card, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=5)
        
        self.cover_label = ctk.CTkLabel(row2, text="Default Cover", text_color="gray")
        self.cover_label.pack(side="left", padx=5)
        
        # Chapter Edit and Cover Buttons
        self.chapters_btn = ctk.CTkButton(row2, text="", image=self.icons['list'], width=30, command=self._view_chapters, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), hover_color=("gray90", "gray20"))
        self.chapters_btn.pack(side="right", padx=2)
        
        self.clear_cover_btn = ctk.CTkButton(row2, text="", image=self.icons['trash'], width=30, command=self._clear_cover, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), hover_color="#fee2e2")
        self.clear_cover_btn.pack(side="right", padx=2)
        
        self.select_cover_btn = ctk.CTkButton(row2, text="", image=self.icons['image'], width=30, command=self._select_cover, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), hover_color=("gray90", "gray20"))
        self.select_cover_btn.pack(side="right", padx=2)
        
        # Output Folder Button and Label (moved from original Row 2)
        ctk.CTkButton(row2, text="Output Folder", image=self.icons['folder'], compound="left", command=self._select_output, width=120, fg_color="transparent", border_width=1).pack(side="right", padx=5)
        self.output_label = ctk.CTkLabel(row2, text="", text_color="gray") # Hidden by default until selected
        self.output_label.pack(side="right", padx=5) # Pack it here to be next to the output folder button
        
        # CARD 2: Voice Strategy
        self.voice_card = ctk.CTkFrame(self.main_view)
        self.voice_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(self.voice_card, text="🗣️ Voice Strategy", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        v_row = ctk.CTkFrame(self.voice_card, fg_color="transparent")
        v_row.pack(fill="x", padx=10, pady=5)
        
        # Model
        # Model
        self.model_var = ctk.StringVar()
        self.model_menu = ctk.CTkOptionMenu(v_row, variable=self.model_var, values=[], width=220, command=self._on_model_change)
        self.model_menu.pack(side="left", padx=5)
        
        # Preview Button
        self.preview_btn = ctk.CTkButton(v_row, text="", image=self.icons['play'], width=30, command=self._preview_voice, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.preview_btn.pack(side="left", padx=2)
        
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
        
        # Row 2: Options
        v_row2 = ctk.CTkFrame(self.voice_card, fg_color="transparent")
        v_row2.pack(fill="x", padx=10, pady=(0, 5))

        # GPU
        self.gpu_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(v_row2, text="🚀 GPU", variable=self.gpu_var, command=self._on_gpu_change, width=80).pack(side="right", padx=10)
        
        # Advanced Models and Manager
        self.advanced_models_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(v_row2, text="Show All Models", variable=self.advanced_models_var, command=self._refresh_model_list, width=80).pack(side="right", padx=10)
        
        self.manage_models_btn = ctk.CTkButton(v_row2, text="Manage", image=self.icons['gear'], compound="left", width=80, height=24, command=self._open_model_manager, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.manage_models_btn.pack(side="right", padx=5)

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

        # Start initial load after UI is ready
        self._refresh_model_list()

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
        popup.geometry("600x500")
        popup.transient(self)
        popup.grab_set()
        
        # Header
        header = ctk.CTkFrame(popup, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text=f"Edit Chapters ({len(chapters)})", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        # Scrollable frame for chapters
        scroll = ctk.CTkScrollableFrame(popup)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        entries = []
        
        for i, ch in enumerate(chapters):
            row = ctk.CTkFrame(scroll, fg_color=("gray95", "gray20"))
            row.pack(fill="x", pady=2, padx=2)
            
            ctk.CTkLabel(row, text=f"{i+1}.", width=30).pack(side="left", padx=5)
            
            entry = ctk.CTkEntry(row)
            entry.insert(0, ch['title'])
            entry.pack(side="left", fill="x", expand=True, padx=5, pady=2)
            entries.append(entry)
            
            char_count = len(ch['content'])
            ctk.CTkLabel(row, text=f"{char_count} chars", text_color="gray", width=80).pack(side="right", padx=5)
        
        # Actions
        actions = ctk.CTkFrame(popup, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=10)
        
        def save_changes():
            new_titles = [e.get() for e in entries]
            for i, title in enumerate(new_titles):
                chapters[i]['title'] = title
            
            # Save to disk cache
            if self.epub_processor.save_chapters(epub_path, chapters):
                messagebox.showinfo("Success", "Chapter titles saved!")
                popup.destroy()
            else:
                messagebox.showerror("Error", "Failed to save changes.")

        def reset_chapters():
            if messagebox.askyesno("Reset", "Reload from EPUB? This will discard changes."):
                if epub_path in self.chapters_cache:
                    del self.chapters_cache[epub_path]
                popup.destroy()
                self._view_chapters()

        ctk.CTkButton(actions, text="Save Changes", image=self.icons['save'], compound="left", command=save_changes).pack(side="right", padx=5)
        ctk.CTkButton(actions, text="Reset", command=reset_chapters, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right", padx=5)
        ctk.CTkButton(actions, text="Close", command=popup.destroy, fg_color="transparent", text_color="gray").pack(side="left", padx=5)
    
    def _on_speed_change(self, value):
        self.speed_label.configure(text=f"{value:.1f}x")
        self.config_mgr.set("last_speed", value)
    
    def _on_gpu_change(self):
        self.config_mgr.set("use_gpu", self.gpu_var.get())
        
    def _refresh_model_list(self):
        """Refresh the model dropdown based on the advanced toggle."""
        show_all = self.advanced_models_var.get()
        models = self.model_manager.list_available_models(only_recommended=not show_all)
        
        self.model_data = {m['name']: m for m in models}
        model_names = list(self.model_data.keys())
        
        # Update dropdown values
        self.model_menu.configure(values=model_names)
        
        # Reset selection if current not in list (or empty)
        current = self.model_var.get()
        if not current or current not in model_names:
            if model_names:
                self.model_var.set(model_names[0])
                self._on_model_change(model_names[0])
            else:
                self.model_var.set("")
    
    def _on_model_change(self, value):
        self.config_mgr.set("last_model", value)
        model_info = self.model_data.get(value)
        if model_info and not self.model_manager.is_model_installed(model_info):
            self._log(f"NOTE: Model {value} needs to be downloaded.")
    
    def _open_model_manager(self):
        """Show model manager dialog."""
        popup = ctk.CTkToplevel(self)
        popup.title("Model Manager")
        popup.geometry("500x400")
        popup.transient(self)
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="Installed Models", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(popup)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Helper to get size
        def get_size(path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return total_size / (1024 * 1024) # MB

        installed_found = False
        models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        
        # Refresh logic inside popup
        def refresh_popup():
            for w in scroll.winfo_children(): w.destroy()
            populate()

        def populate():
            nonlocal installed_found
            all_models = self.model_manager.list_available_models(only_recommended=False)
            installed_found = False
            
            for m in all_models:
                m_path = os.path.join(models_dir, m['extracted_dir'])
                if os.path.exists(m_path):
                    installed_found = True
                    row = ctk.CTkFrame(scroll, fg_color=("gray95", "gray20"))
                    row.pack(fill="x", pady=2, padx=2)
                    
                    # Icon + Name
                    ctk.CTkLabel(row, text="📦", font=ctk.CTkFont(size=16)).pack(side="left", padx=5)
                    
                    info_frame = ctk.CTkFrame(row, fg_color="transparent")
                    info_frame.pack(side="left", fill="x", expand=True)
                    ctk.CTkLabel(info_frame, text=m['name'], font=ctk.CTkFont(weight="bold")).pack(anchor="w")
                    
                    size_mb = get_size(m_path)
                    ctk.CTkLabel(info_frame, text=f"{size_mb:.1f} MB  •  {m.get('language', 'en')}", text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w")
                    
                    # Delete Action
                    def delete_m(model=m):
                        if messagebox.askyesno("Delete", f"Delete model '{model['name']}'?"):
                            try:
                                import shutil
                                shutil.rmtree(os.path.join(models_dir, model['extracted_dir']))
                                refresh_popup()
                                self._refresh_model_list()
                            except Exception as e:
                                messagebox.showerror("Error", f"Failed to delete: {e}")

                    ctk.CTkButton(row, text="", image=self.icons['trash'], width=30, height=30, command=delete_m, fg_color="transparent", hover_color="#fee2e2").pack(side="right", padx=5)

            if not installed_found:
                ctk.CTkLabel(scroll, text="No models installed.", text_color="gray").pack(pady=20)

        populate()
        
        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=10)

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
    
    def _preview_voice(self):
        """Generates and plays a short audio sample."""
        model_name = self.model_var.get()
        model_info = self.model_data.get(model_name)
        
        if not model_info: return
        
        if not self.model_manager.is_model_installed(model_info):
            messagebox.showinfo("Preview", "Please download the model first (Start Conversion will prompt download).")
            return

        self.preview_btn.configure(state="disabled")
        self.status_label.configure(text="Generating preview...")
        
        def run_preview():
            try:
                # Create temp file
                fd, temp_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                
                text = "This is a preview of the selected voice."
                speed = self.speed_var.get()
                sid = int(self.speaker_entry.get())
                
                # Config for TTS
                base_dir = os.path.dirname(os.path.abspath(__file__))
                models_dir = os.path.join(base_dir, "models")
                model_path = os.path.join(models_dir, model_info['extracted_dir'])
                
                config = model_info.copy()
                config['model_dir'] = model_path
                config['provider'] = "cuda" if self.gpu_var.get() else "cpu"

                # Init temp TTS just for preview (inefficient but safe) or reuse?
                # Reusing self.tts_engine is better but need to ensure it's not busy.
                # simpler to just init on the fly or check if initialized.
                # For now, let's try to use the engine if possible, or re-init.
                # The engine class handles re-init if config changes usually.
                
                if self.tts_engine.initialize_model(config):
                    if self.tts_engine.generate_audio(text, temp_path, speed=speed, sid=sid):
                        # Play
                        if winsound:
                            winsound.PlaySound(temp_path, winsound.SND_FILENAME)
                        
                        self.after(0, lambda: self.status_label.configure(text="Preview playing..."))
                    else:
                        self.after(0, lambda: messagebox.showerror("Error", "Failed to generate preview audio."))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "Failed to initialize TTS for preview."))
                    
                # Cleanup
                try:
                    os.remove(temp_path)
                except: pass
                
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Preview failed: {e}"))
            finally:
                self.after(0, lambda: self.preview_btn.configure(state="normal"))
                self.after(0, lambda: self.status_label.configure(text="Ready"))

        threading.Thread(target=run_preview, daemon=True).start()

    def _start_conversion(self):
        if not self.selected_epubs:
            messagebox.showwarning("No File", "Please select EPUB file(s) first.")
            return
        
        model_name = self.model_var.get()
        model_info = self.model_data.get(model_name)
        if not model_info:
            messagebox.showerror("Error", "Please select a valid model.")
            return
            
        # UI Setup
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        
        # Save format preference
        self.config_mgr.set("output_format", self.format_var.get())
        self.config_mgr.set("last_speaker_id", self.speaker_entry.get())

        def run_async_start():
            # Download model if needed
            if not self.model_manager.is_model_installed(model_info):
                self.after(0, lambda: self._log(f"Downloading {model_name}..."))
                self.after(0, lambda: self.status_label.configure(text="Downloading Model..."))
                
                last_logged_pct = [0]
                
                def dl_progress(current, total):
                    if total > 0:
                        pct = int((current / total) * 100)
                        self._on_worker_progress(current / total)
                        
                        if pct >= last_logged_pct[0] + 10:
                            last_logged_pct[0] = pct
                            mb_current = current / (1024 * 1024)
                            mb_total = total / (1024 * 1024)
                            self.after(0, lambda: self._log(f"  Download: {mb_current:.1f} MB / {mb_total:.1f} MB ({pct}%)"))
                
                success = self.model_manager.download_model(model_info, dl_progress)
                if not success:
                    self.after(0, lambda: messagebox.showerror("Error", "Model download failed!"))
                    self.after(0, self._reset_ui)
                    return
                
                self.after(0, lambda: self._log("Download complete. Extracting..."))
            
            # Start conversion worker
            worker = ConversionWorker(
                self.tts_engine, self.audio_builder,
                log_callback=self._on_worker_log,
                progress_callback=self._on_worker_progress,
                status_callback=self._on_worker_status,
                done_callback=self._on_worker_done
            )
            self.current_worker = worker
            
            # Note: worker.start() actually starts another thread, so we can call it from here.
            # However, since we are already in a thread, we could potentially just run it directly if we changed worker. 
            # But adapting worker.start() is fine.
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

        threading.Thread(target=run_async_start, daemon=True).start()
    
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
