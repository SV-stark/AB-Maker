import customtkinter as ctk
import os

class SidebarUI(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        
        # Configure grid
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Logo / Title
        ctk.CTkLabel(self, text="AB-Maker 🎧", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Recent Files Label
        ctk.CTkLabel(self, text="Recent Files", text_color="gray", anchor="w").grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        # Recent Files List (Scrollable)
        self.recent_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.recent_scroll.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.recent_scroll.grid_columnconfigure(0, weight=1)
        
        # Theme Toggle (Bottom)
        self.theme_switch = ctk.CTkSwitch(self, text="Dark Mode", command=self._toggle_theme)
        self.theme_switch.grid(row=5, column=0, padx=20, pady=20, sticky="s")
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()
            
    def _toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
            
    def load_recent_files(self, recent_files):
        """Populate the recent files list."""
        # Clear existing
        for widget in self.recent_scroll.winfo_children():
            widget.destroy()
            
        if not recent_files:
            ctk.CTkLabel(self.recent_scroll, text="No recent files", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=10)
            return
            
        for r_path in recent_files:
            # Lazy validation - we can check existence here or wait until click
            # Checking here provides better UX
            if not os.path.exists(r_path): continue
            
            # Get status icon
            status = self.app.config_mgr.get_file_status(r_path)
            status_icon = ""
            if status == "completed":
                status_icon = "✅ "
            elif status == "in_progress":
                status_icon = "🔄 "
            elif status == "failed":
                status_icon = "❌ "
            
            # Truncate long names
            name = os.path.basename(r_path)
            if len(name) > 20: name = name[:18] + "..."
            
            btn = ctk.CTkButton(
                self.recent_scroll, 
                text=f"{status_icon}{name}", 
                command=lambda p=r_path: self.app.load_book(p),
                fg_color="transparent", 
                border_width=0,
                anchor="w",
                height=28,
                font=ctk.CTkFont(size=11),
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25")
            )
            btn.pack(fill="x", pady=1, padx=2)
