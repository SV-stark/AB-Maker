import customtkinter as ctk
from ui.tooltip import CTkToolTip

class VoiceCardUI(ctk.CTkFrame):
    def __init__(self, parent, app, icons, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.icons = icons
        
        # Card Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 12))
        
        ctk.CTkLabel(
            header, 
            text="🎙️ Voice Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Quick Actions (right side of header)
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")
        
        self.manage_models_btn = ctk.CTkButton(
            actions,
            text="Manage Models",
            image=self.icons.get('gear'),
            compound="left",
            width=110,
            height=28,
            command=self.app.open_model_manager,
            fg_color="transparent",
            border_width=1
        )
        self.manage_models_btn.pack(side="left", padx=(0, 8))
        CTkToolTip(self.manage_models_btn, text="Download and manage TTS models")
        
        self.advanced_models_var = ctk.BooleanVar(value=False)
        self.advanced_switch = ctk.CTkSwitch(
            actions,
            text="Show All",
            variable=self.advanced_models_var,
            command=self.app.refresh_model_list,
            width=60
        )
        self.advanced_switch.pack(side="left")
        CTkToolTip(self.advanced_switch, text="Show all available models (not just recommended)")
        
        # Main Content - Two Column Layout
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=(0, 8))
        
        # Left Column: Model & Voice
        left_col = ctk.CTkFrame(content, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        # Model Selection Section
        model_section = ctk.CTkFrame(left_col, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
        model_section.pack(fill="x", pady=(0, 12))
        
        model_header = ctk.CTkFrame(model_section, fg_color="transparent")
        model_header.pack(fill="x", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            model_header,
            text="Voice Model",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        self.model_var = ctk.StringVar()
        self.model_menu = ctk.CTkOptionMenu(
            model_section,
            variable=self.model_var,
            values=[],
            width=280,
            height=36,
            command=self.app.on_model_change
        )
        self.model_menu.pack(fill="x", padx=16, pady=(0, 12))
        CTkToolTip(self.model_menu, text="Select TTS model for narration")
        
        # Speaker & Speed Section
        voice_section = ctk.CTkFrame(left_col, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
        voice_section.pack(fill="x")
        
        voice_header = ctk.CTkFrame(voice_section, fg_color="transparent")
        voice_header.pack(fill="x", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            voice_header,
            text="Voice Configuration",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        # Speaker ID
        speaker_row = ctk.CTkFrame(voice_section, fg_color="transparent")
        speaker_row.pack(fill="x", padx=16, pady=(0, 8))
        
        ctk.CTkLabel(
            speaker_row,
            text="Speaker ID:",
            font=ctk.CTkFont(size=11),
            width=80,
            anchor="w"
        ).pack(side="left")
        
        self.speaker_entry = ctk.CTkEntry(
            speaker_row,
            width=60,
            height=32
        )
        self.speaker_entry.pack(side="left")
        self.speaker_entry.insert(0, "0")
        CTkToolTip(self.speaker_entry, text="Speaker/Voice ID for multi-speaker models (0 = default)")
        
        self.character_voices_btn = ctk.CTkButton(
            speaker_row,
            text="Character Voices",
            width=120,
            height=28,
            command=self.app.open_character_voices,
            fg_color="transparent",
            border_width=1
        )
        self.character_voices_btn.pack(side="right")
        CTkToolTip(self.character_voices_btn, text="Assign different voices to characters (multi-speaker models only)")
        
        # Speed Slider
        speed_row = ctk.CTkFrame(voice_section, fg_color="transparent")
        speed_row.pack(fill="x", padx=16, pady=(0, 12))
        
        ctk.CTkLabel(
            speed_row,
            text="Speed:",
            font=ctk.CTkFont(size=11),
            width=80,
            anchor="w"
        ).pack(side="left")
        
        self.speed_var = ctk.DoubleVar(value=1.0)
        self.speed_slider = ctk.CTkSlider(
            speed_row,
            from_=0.5,
            to=2.5,
            number_of_steps=20,
            width=140,
            variable=self.speed_var,
            command=self.app.on_speed_change
        )
        self.speed_slider.pack(side="left", padx=(0, 12))
        CTkToolTip(self.speed_slider, text="Adjust playback speed (0.5x - 2.5x)")
        
        self.speed_label = ctk.CTkLabel(
            speed_row,
            text="1.0x",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=45
        )
        self.speed_label.pack(side="left")
        
        # Right Column: Preview & Performance
        right_col = ctk.CTkFrame(content, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(12, 0))
        
        # Preview Section
        preview_section = ctk.CTkFrame(right_col, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
        preview_section.pack(fill="x", pady=(0, 12))
        
        preview_header = ctk.CTkFrame(preview_section, fg_color="transparent")
        preview_header.pack(fill="x", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            preview_header,
            text="🔊 Preview",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        preview_desc = ctk.CTkLabel(
            preview_section,
            text="Test the voice before converting",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8")
        )
        preview_desc.pack(anchor="w", padx=16)
        
        self.preview_btn = ctk.CTkButton(
            preview_section,
            text="▶ Play Preview",
            image=self.icons.get('play'),
            compound="left",
            command=self.app.preview_voice,
            height=40,
            width=160
        )
        self.preview_btn.pack(padx=16, pady=(8, 12))
        CTkToolTip(self.preview_btn, text="Preview voice with current settings (F5)")
        
        # Performance Section
        perf_section = ctk.CTkFrame(right_col, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
        perf_section.pack(fill="x")
        
        perf_header = ctk.CTkFrame(perf_section, fg_color="transparent")
        perf_header.pack(fill="x", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            perf_header,
            text="⚡ Performance",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        # GPU Toggle
        gpu_row = ctk.CTkFrame(perf_section, fg_color="transparent")
        gpu_row.pack(fill="x", padx=16, pady=(0, 8))
        
        self.gpu_var = ctk.BooleanVar(value=False)
        self.gpu_switch = ctk.CTkSwitch(
            gpu_row,
            text="Enable GPU Acceleration",
            variable=self.gpu_var,
            command=self.app.on_gpu_change
        )
        self.gpu_switch.pack(side="left")
        CTkToolTip(self.gpu_switch, text="Use CUDA GPU for 10-50x faster processing")
        
        # Pause Settings
        pause_row = ctk.CTkFrame(perf_section, fg_color="transparent")
        pause_row.pack(fill="x", padx=16, pady=(0, 12))
        
        self.pause_settings_btn = ctk.CTkButton(
            pause_row,
            text="Configure Pauses",
            width=140,
            height=28,
            command=self.app.open_pause_settings,
            fg_color="transparent",
            border_width=1
        )
        self.pause_settings_btn.pack(side="left")
        CTkToolTip(self.pause_settings_btn, text="Adjust pause durations between sentences and paragraphs")

    def update_speed_label(self, value):
        self.speed_label.configure(text=f"{value:.1f}x")
        
    def update_model_list(self, model_names, current_selection):
        self.model_menu.configure(values=model_names)
        if current_selection:
            self.model_var.set(current_selection)
        elif model_names:
            self.model_var.set(model_names[0])
    
    def update_character_voices_button(self, num_speakers: int):
        """Show or hide the Character Voices button based on model capabilities."""
        if num_speakers > 1:
            self.character_voices_btn.configure(state="normal")
            self.character_voices_btn.configure(text_color=("gray10", "gray90"))
        else:
            self.character_voices_btn.configure(state="disabled")
            self.character_voices_btn.configure(text_color="gray")
