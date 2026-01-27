import customtkinter as ctk
from ui.tooltip import CTkToolTip

class VoiceCardUI(ctk.CTkFrame):
    def __init__(self, parent, app, icons, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.icons = icons
        
        ctk.CTkLabel(self, text="🗣️ Voice Strategy", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        v_row = ctk.CTkFrame(self, fg_color="transparent")
        v_row.pack(fill="x", padx=10, pady=5)
        
        # Model
        self.model_var = ctk.StringVar()
        self.model_menu = ctk.CTkOptionMenu(
            v_row, 
            variable=self.model_var, 
            values=[], 
            width=220, 
            command=self.app.on_model_change
        )
        self.model_menu.pack(side="left", padx=5)
        CTkToolTip(self.model_menu, text="Select TTS model")
        
        # Preview Button
        self.preview_btn = ctk.CTkButton(
            v_row, 
            text="", 
            image=self.icons['play'], 
            width=30, 
            command=self.app.preview_voice, 
            fg_color="transparent", 
            border_width=1, 
            text_color=("gray10", "gray90")
        )
        self.preview_btn.pack(side="left", padx=2)
        CTkToolTip(self.preview_btn, text="Preview voice with current settings")
        
        # Speaker ID
        ctk.CTkLabel(v_row, text="Speaker ID:").pack(side="left", padx=(15, 5))
        self.speaker_entry = ctk.CTkEntry(v_row, width=50)
        self.speaker_entry.pack(side="left")
        self.speaker_entry.insert(0, "0")
        CTkToolTip(self.speaker_entry, text="Speaker/Voice ID (0 for default)")
        
        # Speed
        ctk.CTkLabel(v_row, text="Speed:").pack(side="left", padx=(15, 5))
        self.speed_var = ctk.DoubleVar(value=1.0)
        self.speed_slider = ctk.CTkSlider(
            v_row, 
            from_=0.5, 
            to=2.5, 
            width=120, 
            variable=self.speed_var, 
            command=self.app.on_speed_change
        )
        self.speed_slider.pack(side="left", padx=5)
        CTkToolTip(self.speed_slider, text="Adjust playback speed (0.5x - 2.5x)")
        
        self.speed_label = ctk.CTkLabel(v_row, text="1.0x", font=ctk.CTkFont(weight="bold"))
        self.speed_label.pack(side="left")
        
        # Row 2: Options
        v_row2 = ctk.CTkFrame(self, fg_color="transparent")
        v_row2.pack(fill="x", padx=10, pady=(0, 5))

        # GPU
        self.gpu_var = ctk.BooleanVar(value=False)
        self.gpu_switch = ctk.CTkSwitch(v_row2, text="🚀 GPU", variable=self.gpu_var, command=self.app.on_gpu_change, width=80)
        self.gpu_switch.pack(side="right", padx=10)
        CTkToolTip(self.gpu_switch, text="Use CUDA GPU for faster processing")
        
        # Advanced Models and Manager
        self.advanced_models_var = ctk.BooleanVar(value=False)
        self.advanced_switch = ctk.CTkSwitch(v_row2, text="Show All Models", variable=self.advanced_models_var, command=self.app.refresh_model_list, width=80)
        self.advanced_switch.pack(side="right", padx=10)
        CTkToolTip(self.advanced_switch, text="Show all available models (not just recommended)")
        
        self.manage_models_btn = ctk.CTkButton(
            v_row2, 
            text="Manage", 
            image=self.icons['gear'], 
            compound="left", 
            width=80, 
            height=24, 
            command=self.app.open_model_manager, 
            fg_color="transparent", 
            border_width=1, 
            text_color=("gray10", "gray90")
        )
        self.manage_models_btn.pack(side="right", padx=5)
        CTkToolTip(self.manage_models_btn, text="Download and manage TTS models")

    def update_speed_label(self, value):
        self.speed_label.configure(text=f"{value:.1f}x")
        
    def update_model_list(self, model_names, current_selection):
        self.model_menu.configure(values=model_names)
        if current_selection:
            self.model_var.set(current_selection)
        elif model_names:
            self.model_var.set(model_names[0])
