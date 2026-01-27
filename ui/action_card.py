import customtkinter as ctk
from ui.tooltip import CTkToolTip

class ActionCardUI(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        
        a_row = ctk.CTkFrame(self, fg_color="transparent")
        a_row.pack(fill="x", padx=10, pady=10)
        
        # Format
        self.format_var = ctk.StringVar(value="m4b")
        self.m4b_radio = ctk.CTkRadioButton(a_row, text="M4B", variable=self.format_var, value="m4b")
        self.m4b_radio.pack(side="left", padx=10)
        CTkToolTip(self.m4b_radio, text="M4B format with chapter support")
        
        self.mp3_radio = ctk.CTkRadioButton(a_row, text="MP3", variable=self.format_var, value="mp3")
        self.mp3_radio.pack(side="left", padx=10)
        CTkToolTip(self.mp3_radio, text="MP3 format (compatible with all devices)")
        
        # Quality
        ctk.CTkLabel(a_row, text="Quality:").pack(side="left", padx=(15, 5))
        self.quality_var = ctk.StringVar(value="Medium")
        self.quality_menu = ctk.CTkOptionMenu(
            a_row, 
            variable=self.quality_var, 
            values=["Low", "Medium", "High", "Lossless", "Podcast", "Audible"], 
            width=100
        )
        self.quality_menu.pack(side="left", padx=5)
        CTkToolTip(self.quality_menu, text="Audio quality preset")
        
        # Normalize
        self.normalize_var = ctk.BooleanVar(value=False)
        self.normalize_switch = ctk.CTkSwitch(a_row, text="Normalize", variable=self.normalize_var)
        self.normalize_switch.pack(side="left", padx=15)
        CTkToolTip(self.normalize_switch, text="Normalize audio volume levels")
        
        # Reset Button
        self.reset_btn = ctk.CTkButton(
            a_row,
            text="↺ Reset",
            command=self.app.reset_to_defaults,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            width=80,
            height=28
        )
        self.reset_btn.pack(side="left", padx=5)
        CTkToolTip(self.reset_btn, text="Reset all settings to defaults")
        
        # Start Button
        self.start_btn = ctk.CTkButton(
            a_row, 
            text="⚡ START CONVERSION", 
            command=self.app.start_conversion, 
            font=ctk.CTkFont(size=14, weight="bold"), 
            height=40
        )
        self.start_btn.pack(side="right", ipadx=20, padx=5)
        CTkToolTip(self.start_btn, text="Start converting EPUB to audiobook")
        
        self.cancel_btn = ctk.CTkButton(
            a_row, 
            text="STOP", 
            command=self.app.cancel_conversion, 
            fg_color="#ef4444", 
            hover_color="#dc2626", 
            width=80, 
            height=40, 
            state="disabled"
        )
        self.cancel_btn.pack(side="right", padx=5)
        CTkToolTip(self.cancel_btn, text="Cancel current conversion")

        # Progress Section
        p_row = ctk.CTkFrame(self, fg_color="transparent")
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
        
        # Chapter Progress List
        ctk.CTkLabel(self, text="Detailed Progress", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(5,0))
        self.detail_scroll = ctk.CTkScrollableFrame(self, height=150, label_text="Chapters")
        self.detail_scroll.pack(fill="x", padx=15, pady=5)
        self.chapter_widgets = {}
        
        # LOG
        self.log_box = ctk.CTkTextbox(self, height=120, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.pack(fill="both", expand=True, padx=15, pady=5)
        self.log_box.configure(state="disabled")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def init_chapter_list(self, chapters):
        for w in self.detail_scroll.winfo_children():
            w.destroy()
        self.chapter_widgets = {}
        
        for i, ch in enumerate(chapters):
            row = ctk.CTkFrame(self.detail_scroll, fg_color="transparent", height=24)
            row.pack(fill="x", pady=1)
            
            lbl_idx = ctk.CTkLabel(row, text=f"{i+1}.", width=30, anchor="w", text_color="gray")
            lbl_idx.pack(side="left")
            
            lbl_title = ctk.CTkLabel(row, text=ch['title'], anchor="w")
            lbl_title.pack(side="left", fill="x", expand=True)
            
            lbl_status = ctk.CTkLabel(row, text="Pending", width=80, text_color="gray")
            lbl_status.pack(side="right")
            
            self.chapter_widgets[i] = lbl_status

    def update_chapter_status(self, idx, status_type):
        if idx in self.chapter_widgets:
            lbl = self.chapter_widgets[idx]
            if status_type == "processing":
                lbl.configure(text="Processing...", text_color="#3b82f6") # Blue
            elif status_type == "done":
                lbl.configure(text="Done", text_color="#22c55e") # Green
            elif status_type == "cached":
                lbl.configure(text="Cached", text_color="#a8a29e") # Gray
            elif status_type == "failed":
                lbl.configure(text="Failed", text_color="#ef4444") # Red

    def reset_ui(self):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.progress.set(0)
        self.status_label.configure(text="Ready")
        self.eta_label.configure(text="")
        
    def set_converting_state(self):
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
