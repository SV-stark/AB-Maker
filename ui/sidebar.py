import customtkinter as ctk
import os

class SidebarUI(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        
        # Configure grid
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Logo Section
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=16, pady=(20, 16), sticky="ew")
        
        logo_icon = ctk.CTkLabel(
            logo_frame, 
            text="🎧",
            font=ctk.CTkFont(size=28)
        )
        logo_icon.pack(side="left", padx=(0, 10))
        
        logo_text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_text_frame.pack(side="left")
        
        ctk.CTkLabel(
            logo_text_frame, 
            text="AB-Maker", 
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            logo_text_frame, 
            text="Audiobook Creator", 
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w")
        
        # Quick Stats Section
        stats_frame = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
        stats_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        
        stats_header = ctk.CTkLabel(
            stats_frame,
            text="Quick Stats",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        )
        stats_header.pack(anchor="w", padx=12, pady=(10, 4))
        
        self.stats_content = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_content.pack(fill="x", padx=12, pady=(0, 10))
        
        self.stats_label = ctk.CTkLabel(
            self.stats_content,
            text="Ready to convert",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.stats_label.pack(fill="x")
        
        # Recent Files Section
        recent_header = ctk.CTkFrame(self, fg_color="transparent")
        recent_header.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        
        ctk.CTkLabel(
            recent_header,
            text="Recent Files",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        self.clear_recent_btn = ctk.CTkButton(
            recent_header,
            text="Clear",
            font=ctk.CTkFont(size=9),
            width=50,
            height=20,
            fg_color="transparent",
            hover_color=("#e2e8f0", "#334155")
        )
        self.clear_recent_btn.pack(side="right")
        
        # Recent Files List
        self.recent_container = ctk.CTkFrame(self, fg_color="transparent")
        self.recent_container.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="nsew")
        
        self.recent_scroll = ctk.CTkScrollableFrame(
            self.recent_container,
            fg_color="transparent",
            corner_radius=0
        )
        self.recent_scroll.pack(fill="both", expand=True)
        
        # Empty state label
        self.empty_label = ctk.CTkLabel(
            self.recent_scroll,
            text="No recent files",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.empty_label.pack(pady=20)
        
        # Bottom Actions
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, padx=16, pady=(0, 16), sticky="s")
        
        # About Button
        self.about_btn = ctk.CTkButton(
            bottom_frame,
            text="ℹ️ About AB-Maker",
            command=self.app.open_about,
            fg_color="transparent",
            border_width=1,
            height=32
        )
        self.about_btn.pack(fill="x", pady=(0, 8))
        
        # Theme Toggle
        theme_frame = ctk.CTkFrame(bottom_frame, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
        theme_frame.pack(fill="x", pady=(0, 8))
        
        theme_inner = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_inner.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            theme_inner,
            text="🌙 Dark Mode",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        self.theme_switch = ctk.CTkSwitch(
            theme_inner,
            text="",
            width=40,
            command=self._toggle_theme
        )
        self.theme_switch.pack(side="right")
        
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()
        
        # Keyboard Shortcuts Hint
        shortcuts_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        shortcuts_frame.pack(fill="x")
        
        shortcuts_text = "Shortcuts: Ctrl+O (Open) | Enter (Start) | Esc (Stop)"
        ctk.CTkLabel(
            shortcuts_frame,
            text=shortcuts_text,
            font=ctk.CTkFont(size=9),
            text_color=("#94a3b8", "#64748b"),
            wraplength=180
        ).pack()
            
    def _toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
            
    def load_recent_files(self, recent_files):
        """Populate the recent files list with enhanced display"""
        # Clear existing widgets
        for widget in self.recent_scroll.winfo_children():
            widget.destroy()
            
        if not recent_files:
            self.empty_label = ctk.CTkLabel(
                self.recent_scroll,
                text="No recent files",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            self.empty_label.pack(pady=20)
            return
            
        for r_path in recent_files:
            # Check if file exists
            if not os.path.exists(r_path):
                continue
            
            # Get file info
            name = os.path.basename(r_path)
            display_name = name if len(name) < 28 else name[:25] + "..."
            
            # Get status icon and color
            status = self.app.config_mgr.get_file_status(r_path)
            status_data = self._get_status_display(status)
            
            # Create file entry frame
            file_frame = ctk.CTkFrame(self.recent_scroll, fg_color="transparent")
            file_frame.pack(fill="x", pady=2)
            
            # Status indicator
            status_label = ctk.CTkLabel(
                file_frame,
                text=status_data['icon'],
                font=ctk.CTkFont(size=12),
                text_color=status_data['color'],
                width=24
            )
            status_label.pack(side="left")
            
            # File button
            btn = ctk.CTkButton(
                file_frame,
                text=display_name,
                command=lambda p=r_path: self.app.load_book(p),
                fg_color="transparent",
                border_width=0,
                anchor="w",
                height=32,
                font=ctk.CTkFont(size=11),
                text_color=("#334155", "#cbd5e1"),
                hover_color=("#e2e8f0", "#334155")
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
            
            # Tooltip with full path
            from ui.tooltip import CTkToolTip
            CTkToolTip(btn, text=f"{r_path}\n\nStatus: {status_data['label']}")
    
    def _get_status_display(self, status):
        """Get display data for file status"""
        if status == "completed":
            return {
                'icon': '✓',
                'color': '#22c55e',
                'label': 'Completed'
            }
        elif status == "in_progress":
            return {
                'icon': '◐',
                'color': '#3b82f6',
                'label': 'In Progress'
            }
        elif status == "failed":
            return {
                'icon': '✗',
                'color': '#ef4444',
                'label': 'Failed'
            }
        else:
            return {
                'icon': '○',
                'color': ('#94a3b8', '#64748b'),
                'label': 'Not Started'
            }
    
    def update_stats(self, message):
        """Update the stats display"""
        self.stats_label.configure(text=message)
