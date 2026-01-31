"""
Refactored AB-Maker Main Application
Clean architecture with Controller and Service layers
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
from pathlib import Path
from typing import List, Optional

# Core imports
from model_manager import ModelManager
from epub_processor import EpubProcessor
from tts_engine import TTSEngine
from audio_builder import AudioBuilder
from config_manager import ConfigManager
from core.event_bus import EventBus

# Controller
from controllers.app_controller import AppController

# Models
from models.domain import VoiceSettings, OutputSettings, ConversionStatus, AudioFormat

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
    """
    Refactored main application class.
    
    Responsibilities:
    - UI initialization and layout
    - Event handling from UI components
    - Delegating business logic to AppController
    - Managing UI state only
    """
    
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Initialize controller (which initializes all services)
        self._init_controller()
        
        # Window setup
        self._setup_window()
        
        # State (UI-only)
        self.selected_epubs: List[Path] = []
        self.output_dir: Optional[Path] = None
        self.custom_cover_path: Optional[Path] = None
        self.icons = generate_icons()
        self.model_data: dict = {}
        
        # Build UI
        self._create_widgets()
        
        # Load settings through controller
        self._load_settings()
        
        # Check dependencies
        self._check_dependencies()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _init_controller(self):
        """Initialize the application controller with all dependencies."""
        # Create managers
        config_manager = ConfigManager()
        model_manager = ModelManager(models_dir=config_manager.get_models_dir())
        epub_processor = EpubProcessor(cache_dir=config_manager.get_cache_dir())
        tts_engine = TTSEngine()
        audio_builder = AudioBuilder()
        
        # Create event bus for decoupled communication
        event_bus = EventBus()
        
        # Create controller
        self.controller = AppController(
            config_manager=config_manager,
            model_manager=model_manager,
            epub_processor=epub_processor,
            tts_engine=tts_engine,
            audio_builder=audio_builder,
            event_bus=event_bus
        )
        
        # Set up UI callbacks
        self.controller.set_ui_callbacks(
            log_callback=self._on_log_message,
            progress_callback=self._on_progress_update,
            status_callback=self._on_status_update
        )
    
    def _setup_window(self):
        """Configure main window."""
        self.title("AB-Maker: Audiobook Creator")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Register Drop Target
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._on_drop)
    
    def _create_widgets(self):
        """Create UI components."""
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
        self._refresh_model_list()
    
    def _load_settings(self):
        """Load and apply settings via controller."""
        # Load recent files
        recent_files = self.controller.get_recent_files()
        self.sidebar.load_recent_files([str(f.path) for f in recent_files])
        
        # Voice settings
        voice_settings = self.controller.get_voice_settings()
        self.voice_card.speed_var.set(voice_settings.speed)
        self.voice_card.update_speed_label(voice_settings.speed)
        self.voice_card.speaker_entry.delete(0, "end")
        self.voice_card.speaker_entry.insert(0, str(voice_settings.speaker_id))
        self.voice_card.gpu_var.set(voice_settings.use_gpu)
        
        # Output settings
        output_settings = self.controller.get_output_settings()
        self.action_card.format_var.set(output_settings.format.value)
        self.action_card.quality_var.set(output_settings.quality)
        self.action_card.normalize_var.set(output_settings.normalize)
    
    def _check_dependencies(self):
        """Check required dependencies."""
        if not self.controller.check_ffmpeg():
            self.controller.log("WARNING: FFmpeg not found! M4B/MP3 output may fail.")
    
    # --- UI Callbacks ---
    
    def _on_log_message(self, message: str):
        """Handle log message from controller."""
        self.action_card.log(message)
    
    def _on_progress_update(self, progress: float):
        """Handle progress update from controller."""
        self.action_card.progress.set(progress)
    
    def _on_status_update(self, status: str):
        """Handle status update from controller."""
        self.action_card.status_label.configure(text=status)
    
    # --- Event Handlers (Delegated to Controller) ---
    
    def on_speed_change(self, value):
        """Handle speed slider change."""
        speed = self.controller.validate_speed(value)
        self.voice_card.update_speed_label(speed)
        
        # Update settings via controller
        settings = self.controller.get_voice_settings()
        settings.speed = speed
        self.controller.set_voice_settings(settings)
    
    def on_gpu_change(self):
        """Handle GPU toggle change."""
        settings = self.controller.get_voice_settings()
        settings.use_gpu = self.voice_card.gpu_var.get()
        self.controller.set_voice_settings(settings)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        # Reset UI elements
        self.voice_card.speed_var.set(1.0)
        self.voice_card.update_speed_label(1.0)
        self.voice_card.speaker_entry.delete(0, "end")
        self.voice_card.speaker_entry.insert(0, "0")
        self.voice_card.gpu_var.set(False)
        
        self.action_card.format_var.set("m4b")
        self.action_card.quality_var.set("Medium")
        self.action_card.normalize_var.set(False)
        
        # Reset via controller
        self.controller.reset_settings()
    
    def _refresh_model_list(self):
        """Refresh available model list."""
        show_all = self.voice_card.advanced_models_var.get()
        models = self.controller.get_available_models(only_recommended=not show_all)
        
        self.model_data = {m.name: m.to_dict() for m in models}
        model_names = list(self.model_data.keys())
        self.voice_card.update_model_list(model_names, self.voice_card.model_var.get())
    
    def on_model_change(self, value):
        """Handle model selection change."""
        settings = self.controller.get_voice_settings()
        settings.model_name = value
        self.controller.set_voice_settings(settings)
        
        # Check if model needs download
        if not self.controller.is_model_installed(value):
            self.controller.log(f"NOTE: Model {value} needs to be downloaded.")
    
    def open_model_manager(self):
        """Open model manager dialog."""
        ModelManagerDialog(self, self.controller.model_service._model_manager, self.icons, self._refresh_model_list)
    
    def open_about(self):
        """Open about dialog."""
        AboutDialog(self, self.icons)
    
    def load_book(self, path: str):
        """Load an EPUB book file."""
        file_path = Path(path)
        success, error = self.controller.load_epub_file(file_path)
        
        if success:
            self.selected_epurbs = [file_path]
            self.book_card.update_file_label([str(p) for p in self.selected_epurbs])
            
            # Refresh recent files
            recent_files = self.controller.get_recent_files()
            self.sidebar.load_recent_files([str(f.path) for f in recent_files])
        else:
            messagebox.showerror("Error", error or "Failed to load file")
    
    def select_files(self):
        """Select EPUB files via dialog."""
        files = filedialog.askopenfilenames(
            title="Select EPUB Files",
            filetypes=self.controller.file_service.get_file_dialog_filters("epub")
        )
        
        if files:
            self.selected_epurbs = [Path(f) for f in files]
            
            # Load first file
            success, _ = self.controller.load_epub_file(self.selected_epurbs[0])
            
            if success:
                self.book_card.update_file_label([str(p) for p in self.selected_epurbs])
                
                # Refresh recent files
                recent_files = self.controller.get_recent_files()
                self.sidebar.load_recent_files([str(f.path) for f in recent_files])
    
    def _on_drop(self, event):
        """Handle drag-and-drop file."""
        if event.data:
            file_path = event.data
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            path = Path(file_path)
            
            if path.exists():
                ext = path.suffix.lower()
                if ext == '.epub':
                    self.load_book(file_path)
                    self.controller.log(f"Dropped file: {path.name}")
                elif ext in ['.jpg', '.jpeg', '.png']:
                    success, error = self.controller.set_cover_image(path)
                    if success:
                        self.custom_cover_path = path
                        self.book_card.update_cover_label(str(path))
                        self.controller.log(f"Dropped cover: {path.name}")
                    else:
                        messagebox.showerror("Error", error)
    
    def select_output(self):
        """Select output directory."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            dir_path = Path(folder)
            success, error = self.controller.set_output_directory(dir_path)
            
            if success:
                self.output_dir = dir_path
                self.book_card.update_output_label(folder)
            else:
                messagebox.showerror("Error", error)
    
    def select_cover(self):
        """Select cover image file."""
        cover_file = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=self.controller.file_service.get_file_dialog_filters("image")
        )
        
        if cover_file:
            path = Path(cover_file)
            success, error = self.controller.set_cover_image(path)
            
            if success:
                self.custom_cover_path = path
                self.book_card.update_cover_label(cover_file)
                self.controller.log(f"Custom cover selected: {path.name}")
            else:
                messagebox.showerror("Error", error)
    
    def clear_cover(self):
        """Clear custom cover selection."""
        self.custom_cover_path = None
        self.book_card.update_cover_label(None)
    
    def view_chapters(self):
        """Open chapter editor dialog."""
        if not self.selected_epurbs:
            messagebox.showwarning("No File", "Please select an EPUB first.")
            return
        
        # TODO: Implement chapter extraction through controller
        messagebox.showinfo("Info", "Chapter editor not yet implemented in refactored version")
    
    def start_conversion(self):
        """Start audiobook conversion."""
        if not self.selected_epurbs:
            messagebox.showwarning("No File", "Please select EPUB file(s) first.")
            return
        
        # Get voice settings from UI
        settings = VoiceSettings(
            model_name=self.voice_card.model_var.get(),
            speed=self.voice_card.speed_var.get(),
            speaker_id=int(self.voice_card.speaker_entry.get()),
            use_gpu=self.voice_card.gpu_var.get()
        )
        
        # Get output settings from UI
        output = OutputSettings(
            format=AudioFormat(self.action_card.format_var.get()),
            quality=self.action_card.quality_var.get(),
            output_dir=self.output_dir,
            normalize=self.action_card.normalize_var.get(),
            custom_cover=self.custom_cover_path
        )
        
        # Update UI state
        self.action_card.set_converting_state()
        
        # Start conversion via controller
        job_id = self.controller.start_conversion(
            self.selected_epurbs,
            settings,
            output
        )
        
        if job_id:
            self.controller.log(f"Conversion started: {self.selected_epurbs[0].name}")
        else:
            self.action_card.reset_ui()
    
    def cancel_conversion(self):
        """Cancel running conversion."""
        # TODO: Track active job ID and cancel via controller
        self.controller.log("Cancel not yet implemented in refactored version")
    
    def preview_voice(self):
        """Preview voice with current settings."""
        model_name = self.voice_card.model_var.get()
        
        if not model_name:
            messagebox.showwarning("No Model", "Please select a model first.")
            return
        
        # Get settings
        settings = VoiceSettings(
            model_name=model_name,
            speed=self.voice_card.speed_var.get(),
            speaker_id=int(self.voice_card.speaker_entry.get()),
            use_gpu=self.voice_card.gpu_var.get()
        )
        
        model_info = self.model_data.get(model_name, {})
        
        # Disable preview button
        self.voice_card.preview_btn.configure(state="disabled")
        
        # Start preview via controller
        success = self.controller.preview_voice(
            settings,
            model_info,
            on_complete=lambda: self.voice_card.preview_btn.configure(state="normal"),
            on_error=lambda e: self.voice_card.preview_btn.configure(state="normal")
        )
        
        if not success:
            self.voice_card.preview_btn.configure(state="normal")
    
    def _on_closing(self):
        """Handle application close."""
        # TODO: Check if conversion is in progress
        self.destroy()


# For backward compatibility - redirect to controller
class ABMakerAppLegacy:
    """
    Legacy compatibility wrapper.
    Redirects all calls to new controller-based implementation.
    """
    pass  # This would wrap the old API if needed for migration
