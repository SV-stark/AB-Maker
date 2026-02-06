import customtkinter as ctk
from ui.tooltip import CTkToolTip

class ActionCardUI(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.chapter_widgets = {}
        self.log_expanded = False
        
        # Card Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 12))
        
        ctk.CTkLabel(
            header, 
            text="⚡ Conversion", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Output Settings Section
        settings_frame = ctk.CTkFrame(self, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
        settings_frame.pack(fill="x", padx=20, pady=(0, 12))
        
        settings_header = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_header.pack(fill="x", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            settings_header,
            text="Output Settings",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        # Settings Grid
        settings_grid = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_grid.pack(fill="x", padx=16, pady=(0, 12))
        
        # Row 1: Format & Quality
        row1 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        
        # Format Selection
        format_frame = ctk.CTkFrame(row1, fg_color="transparent")
        format_frame.pack(side="left", padx=(0, 24))
        
        ctk.CTkLabel(
            format_frame,
            text="Format:",
            font=ctk.CTkFont(size=11),
            width=50,
            anchor="w"
        ).pack(side="left")
        
        self.format_var = ctk.StringVar(value="m4b")
        
        self.m4b_radio = ctk.CTkRadioButton(
            format_frame,
            text="M4B",
            variable=self.format_var,
            value="m4b",
            width=60
        )
        self.m4b_radio.pack(side="left", padx=(0, 12))
        CTkToolTip(self.m4b_radio, text="M4B format with chapter support (recommended)")
        
        self.mp3_radio = ctk.CTkRadioButton(
            format_frame,
            text="MP3",
            variable=self.format_var,
            value="mp3",
            width=60
        )
        self.mp3_radio.pack(side="left", padx=(0, 12))
        CTkToolTip(self.mp3_radio, text="MP3 format (compatible with all devices)")
        
        self.wav_radio = ctk.CTkRadioButton(
            format_frame,
            text="WAV",
            variable=self.format_var,
            value="wav",
            width=60
        )
        self.wav_radio.pack(side="left")
        CTkToolTip(self.wav_radio, text="WAV format (uncompressed, largest files)")
        
        # Quality Selection
        quality_frame = ctk.CTkFrame(row1, fg_color="transparent")
        quality_frame.pack(side="right")
        
        ctk.CTkLabel(
            quality_frame,
            text="Quality:",
            font=ctk.CTkFont(size=11),
            width=50,
            anchor="w"
        ).pack(side="left")
        
        self.quality_var = ctk.StringVar(value="Medium")
        self.quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.quality_var,
            values=["Low", "Medium", "High", "Lossless", "Podcast", "Audible"],
            width=120,
            height=32
        )
        self.quality_menu.pack(side="left")
        CTkToolTip(self.quality_menu, text="Audio quality preset (bitrate)")
        
        # Row 2: Options
        row2 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        
        self.normalize_var = ctk.BooleanVar(value=False)
        self.normalize_switch = ctk.CTkSwitch(
            row2,
            text="Normalize Audio",
            variable=self.normalize_var
        )
        self.normalize_switch.pack(side="left")
        CTkToolTip(self.normalize_switch, text="Normalize audio volume for consistent loudness")
        
        self.reset_btn = ctk.CTkButton(
            row2,
            text="↺ Reset to Defaults",
            command=self.app.reset_to_defaults,
            fg_color="transparent",
            border_width=1,
            width=130,
            height=28
        )
        self.reset_btn.pack(side="right")
        CTkToolTip(self.reset_btn, text="Reset all settings to defaults (Ctrl+R)")
        
        # Action Buttons Section
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(0, 12))
        
        self.start_btn = ctk.CTkButton(
            action_frame,
            text="🚀 Start Conversion",
            command=self.app.start_conversion,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            width=200
        )
        self.start_btn.pack(side="left", padx=(0, 12))
        CTkToolTip(self.start_btn, text="Start converting EPUB to audiobook (Enter)")
        
        self.cancel_btn = ctk.CTkButton(
            action_frame,
            text="⏹ Stop",
            command=self.app.cancel_conversion,
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=48,
            width=100,
            state="disabled"
        )
        self.cancel_btn.pack(side="left")
        CTkToolTip(self.cancel_btn, text="Cancel current conversion (Esc)")
        
        # Progress Section
        progress_frame = ctk.CTkFrame(self, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
        progress_frame.pack(fill="x", padx=20, pady=(0, 12))
        
        progress_header = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_header.pack(fill="x", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            progress_header,
            text="Progress",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        self.status_label = ctk.CTkLabel(
            progress_header,
            text="Ready to convert",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8")
        )
        self.status_label.pack(side="right")
        
        # Progress Bar
        self.progress = ctk.CTkProgressBar(
            progress_frame,
            height=10,
            corner_radius=5
        )
        self.progress.pack(fill="x", padx=16, pady=(0, 8))
        self.progress.set(0)
        
        # Stats Row
        stats_row = ctk.CTkFrame(progress_frame, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=(0, 12))
        
        self.progress_percent = ctk.CTkLabel(
            stats_row,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=40
        )
        self.progress_percent.pack(side="left")
        
        self.eta_label = ctk.CTkLabel(
            stats_row,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8")
        )
        self.eta_label.pack(side="right")
        
        # Chapter Progress (Collapsible)
        self.chapter_section = ctk.CTkFrame(self, fg_color="transparent")
        
        chapter_header = ctk.CTkFrame(self.chapter_section, fg_color="transparent")
        chapter_header.pack(fill="x", padx=20, pady=(0, 8))
        
        ctk.CTkLabel(
            chapter_header,
            text="Chapter Progress",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        self.chapter_count_label = ctk.CTkLabel(
            chapter_header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8")
        )
        self.chapter_count_label.pack(side="right")
        
        self.chapter_scroll = ctk.CTkScrollableFrame(
            self.chapter_section,
            height=180,
            fg_color=("#f8fafc", "#0f172a")
        )
        self.chapter_scroll.pack(fill="x", padx=20)
        
        # Log Section (Collapsible)
        self.log_header = ctk.CTkFrame(self, fg_color="transparent")
        self.log_header.pack(fill="x", padx=20, pady=(8, 4))
        
        log_title_row = ctk.CTkFrame(self.log_header, fg_color="transparent")
        log_title_row.pack(fill="x")
        
        ctk.CTkLabel(
            log_title_row,
            text="📝 Activity Log",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        self.log_toggle_btn = ctk.CTkButton(
            log_title_row,
            text="Show",
            width=60,
            height=24,
            fg_color="transparent",
            border_width=1,
            command=self._toggle_log
        )
        self.log_toggle_btn.pack(side="right")
        
        self.log_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.log_box = ctk.CTkTextbox(
            self.log_frame,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=10),
            wrap="word"
        )
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.log_box.configure(state="disabled")

    def _toggle_log(self):
        """Toggle log visibility"""
        if self.log_expanded:
            self.log_frame.pack_forget()
            self.log_toggle_btn.configure(text="Show")
            self.log_expanded = False
        else:
            self.log_frame.pack(fill="x", expand=True, pady=(0, 8))
            self.log_toggle_btn.configure(text="Hide")
            self.log_expanded = True

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        
        # Auto-expand log on error
        if "error" in message.lower() or "failed" in message.lower():
            if not self.log_expanded:
                self._toggle_log()

    def init_chapter_list(self, chapters):
        """Initialize chapter progress list"""
        # Clear existing
        for w in self.chapter_scroll.winfo_children():
            w.destroy()
        self.chapter_widgets = {}
        
        if not chapters:
            return
        
        # Show chapter section
        self.chapter_section.pack(fill="x", pady=(0, 8), before=self.log_header)
        self.chapter_count_label.configure(text=f"{len(chapters)} chapters")
        
        for i, ch in enumerate(chapters):
            row = ctk.CTkFrame(self.chapter_scroll, fg_color="transparent", height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            # Status indicator (colored dot)
            status_frame = ctk.CTkFrame(row, fg_color="transparent", width=24)
            status_frame.pack(side="left")
            status_frame.pack_propagate(False)
            
            status_dot = ctk.CTkLabel(
                status_frame,
                text="○",
                font=ctk.CTkFont(size=10),
                text_color=("#cbd5e1", "#475569"),
                width=20
            )
            status_dot.pack()
            
            # Chapter number
            lbl_idx = ctk.CTkLabel(
                row,
                text=f"{i+1:3d}.",
                width=35,
                anchor="w",
                font=ctk.CTkFont(family="Consolas", size=10),
                text_color=("#64748b", "#94a3b8")
            )
            lbl_idx.pack(side="left")
            
            # Chapter title
            title = ch.get('title', f'Chapter {i+1}')
            if len(title) > 45:
                title = title[:42] + "..."
            
            lbl_title = ctk.CTkLabel(
                row,
                text=title,
                anchor="w",
                font=ctk.CTkFont(size=11)
            )
            lbl_title.pack(side="left", fill="x", expand=True, padx=(4, 0))
            
            # Status text
            lbl_status = ctk.CTkLabel(
                row,
                text="Pending",
                width=70,
                font=ctk.CTkFont(size=10),
                text_color=("#64748b", "#94a3b8")
            )
            lbl_status.pack(side="right")
            
            self.chapter_widgets[i] = (status_dot, lbl_status)

    def update_chapter_status(self, idx, status_type):
        """Update chapter status with visual indicators"""
        if idx in self.chapter_widgets:
            status_dot, lbl_status = self.chapter_widgets[idx]
            
            if status_type == "processing":
                status_dot.configure(text="◐", text_color="#3b82f6")
                lbl_status.configure(text="Processing...", text_color="#3b82f6")
            elif status_type == "done":
                status_dot.configure(text="✓", text_color="#22c55e")
                lbl_status.configure(text="Complete", text_color="#22c55e")
            elif status_type == "cached":
                status_dot.configure(text="✓", text_color="#a8a29e")
                lbl_status.configure(text="Cached", text_color="#a8a29e")
            elif status_type == "failed":
                status_dot.configure(text="✗", text_color="#ef4444")
                lbl_status.configure(text="Failed", text_color="#ef4444")

    def reset_ui(self):
        """Reset UI to ready state"""
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.progress.set(0)
        self.progress_percent.configure(text="0%")
        self.status_label.configure(text="Ready to convert")
        self.eta_label.configure(text="")
        
    def set_converting_state(self):
        """Set UI to converting state"""
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress.set(0)
        self.progress_percent.configure(text="0%")
        
        # Expand log during conversion
        if not self.log_expanded:
            self._toggle_log()
