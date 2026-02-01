"""
Pause Settings Dialog
Configure pause durations between sentences, clauses, paragraphs, and dialogue
"""
import customtkinter as ctk
from tkinter import messagebox


class PauseSettingsDialog(ctk.CTkToplevel):
    """Dialog for configuring TTS pause durations."""
    
    # Default pause values in milliseconds
    DEFAULTS = {
        'sentence': 700,
        'clause': 250,
        'paragraph': 1500,
        'dialogue': 400
    }
    
    # Min/Max range for sliders
    MIN_PAUSE = 0
    MAX_PAUSE = 3000
    
    def __init__(self, parent, config_manager, icons=None):
        super().__init__(parent)
        self.title("Pause Settings")
        self.geometry("500x550")
        self.transient(parent)
        self.grab_set()
        
        self.config_manager = config_manager
        self.icons = icons or {}
        
        # Load current settings
        self.pauses = self._load_settings()
        
        self._create_ui()
        self._update_labels()
        
    def _load_settings(self):
        """Load pause settings from config or use defaults."""
        return {
            'sentence': self.config_manager.get("pause_sentence", self.DEFAULTS['sentence']),
            'clause': self.config_manager.get("pause_clause", self.DEFAULTS['clause']),
            'paragraph': self.config_manager.get("pause_paragraph", self.DEFAULTS['paragraph']),
            'dialogue': self.config_manager.get("pause_dialogue", self.DEFAULTS['dialogue'])
        }
    
    def _create_ui(self):
        """Create the dialog UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            header, 
            text="Configure Pauses", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Adjust pause durations between different text elements (0-3000ms)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        # Scrollable content
        content = ctk.CTkScrollableFrame(self)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sentence Pause
        self._create_pause_control(
            content, "Sentence Pause",
            "Pause after sentences (periods, exclamation marks, question marks)",
            'sentence'
        )
        
        # Clause Pause
        self._create_pause_control(
            content, "Clause Pause",
            "Pause after clauses (commas, semicolons, colons)",
            'clause'
        )
        
        # Paragraph Pause
        self._create_pause_control(
            content, "Paragraph Pause",
            "Pause between paragraphs (longer breaks between sections)",
            'paragraph'
        )
        
        # Dialogue Pause
        self._create_pause_control(
            content, "Dialogue Pause",
            "Pause after dialogue before attribution (e.g., ...\" said John)",
            'dialogue'
        )
        
        # Info box
        info_frame = ctk.CTkFrame(content, fg_color=("gray95", "gray20"))
        info_frame.pack(fill="x", pady=15, padx=5)
        
        info_text = ("💡 Tip: Longer pauses make narration sound more natural and "
                    "give listeners time to process information.\n\n"
                    "Recommended settings:\n"
                    "• Sentence: 500-1000ms\n"
                    "• Clause: 200-400ms\n"
                    "• Paragraph: 1000-2000ms\n"
                    "• Dialogue: 300-500ms")
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            wraplength=400,
            justify="left"
        ).pack(padx=10, pady=10)
        
        # Actions
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            actions,
            text="Reset to Defaults",
            command=self._reset_defaults,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            actions,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            text_color="gray",
            width=80
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            actions,
            text="Save Changes",
            command=self._save_changes,
            width=100
        ).pack(side="right", padx=5)
    
    def _create_pause_control(self, parent, title, description, key):
        """Create a pause control with slider and label."""
        frame = ctk.CTkFrame(parent, fg_color=("gray95", "gray20"))
        frame.pack(fill="x", pady=8, padx=5)
        
        # Title row
        title_row = ctk.CTkFrame(frame, fg_color="transparent")
        title_row.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(
            title_row,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        value_label = ctk.CTkLabel(
            title_row,
            text="0 ms",
            font=ctk.CTkFont(size=12),
            width=60
        )
        value_label.pack(side="right")
        setattr(self, f'{key}_value_label', value_label)
        
        # Description
        ctk.CTkLabel(
            frame,
            text=description,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=400
        ).pack(anchor="w", padx=10, pady=(5, 0))
        
        # Slider
        slider = ctk.CTkSlider(
            frame,
            from_=self.MIN_PAUSE,
            to=self.MAX_PAUSE,
            number_of_steps=60,  # 50ms increments
            command=lambda val, k=key: self._on_slider_change(k, val)
        )
        slider.pack(fill="x", padx=10, pady=10)
        slider.set(self.pauses[key])
        setattr(self, f'{key}_slider', slider)
    
    def _on_slider_change(self, key, value):
        """Handle slider value change."""
        self.pauses[key] = int(value)
        self._update_labels()
    
    def _update_labels(self):
        """Update all value labels."""
        for key in self.pauses:
            label = getattr(self, f'{key}_value_label', None)
            if label:
                label.configure(text=f"{self.pauses[key]} ms")
    
    def _reset_defaults(self):
        """Reset all pauses to default values."""
        if messagebox.askyesno("Reset", "Reset all pause settings to defaults?"):
            self.pauses = self.DEFAULTS.copy()
            for key, value in self.pauses.items():
                slider = getattr(self, f'{key}_slider', None)
                if slider:
                    slider.set(value)
            self._update_labels()
    
    def _save_changes(self):
        """Save pause settings to config."""
        try:
            self.config_manager.set("pause_sentence", self.pauses['sentence'])
            self.config_manager.set("pause_clause", self.pauses['clause'])
            self.config_manager.set("pause_paragraph", self.pauses['paragraph'])
            self.config_manager.set("pause_dialogue", self.pauses['dialogue'])
            
            messagebox.showinfo("Success", "Pause settings saved successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def get_pauses(self):
        """Get current pause settings as dict."""
        return self.pauses.copy()
