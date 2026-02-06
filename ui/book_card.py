import customtkinter as ctk
import os
from ui.tooltip import CTkToolTip

class BookCardUI(ctk.CTkFrame):
    def __init__(self, parent, app, icons, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.icons = icons
        
        # Card Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        
        ctk.CTkLabel(
            header, 
            text="📖 Book Selection", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Drag & Drop Zone
        self.drop_frame = ctk.CTkFrame(
            self, 
            fg_color=("#f1f5f9", "#1e293b"),
            border_width=2,
            border_color=("#cbd5e1", "#334155"),
            corner_radius=12
        )
        self.drop_frame.pack(fill="x", padx=20, pady=8)
        
        # Drop content
        self.drop_content = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        self.drop_content.pack(fill="x", padx=24, pady=20)
        
        # Icon and text
        self.drop_icon = ctk.CTkLabel(
            self.drop_content, 
            text="📁",
            font=ctk.CTkFont(size=32)
        )
        self.drop_icon.pack()
        
        self.drop_label = ctk.CTkLabel(
            self.drop_content,
            text="Drag & drop EPUB files here",
            font=ctk.CTkFont(size=14),
            text_color=("#64748b", "#94a3b8")
        )
        self.drop_label.pack(pady=(8, 4))
        
        self.drop_hint = ctk.CTkLabel(
            self.drop_content,
            text="or click Browse to select files",
            font=ctk.CTkFont(size=11),
            text_color=("#94a3b8", "#64748b")
        )
        self.drop_hint.pack()
        
        # Browse button centered
        self.browse_btn = ctk.CTkButton(
            self.drop_content,
            text="Browse Files",
            image=self.icons.get('folder'),
            compound="left",
            command=self.app.select_files,
            width=140,
            height=36
        )
        self.browse_btn.pack(pady=(12, 0))
        
        # File info section (hidden by default)
        self.file_info_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # Selected file display
        self.file_header = ctk.CTkFrame(self.file_info_frame, fg_color="transparent")
        self.file_header.pack(fill="x", pady=(8, 4))
        
        self.file_status_icon = ctk.CTkLabel(
            self.file_header,
            text="✓",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#22c55e"
        )
        self.file_status_icon.pack(side="left", padx=(0, 8))
        
        self.file_name_label = ctk.CTkLabel(
            self.file_header,
            text="No file selected",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self.file_name_label.pack(side="left", fill="x", expand=True)
        
        self.change_file_btn = ctk.CTkButton(
            self.file_header,
            text="Change",
            command=self.app.select_files,
            width=80,
            height=28,
            fg_color="transparent",
            border_width=1
        )
        self.change_file_btn.pack(side="right")
        
        # Metadata display
        self.metadata_frame = ctk.CTkFrame(
            self.file_info_frame,
            fg_color=("#f8fafc", "#0f172a"),
            corner_radius=8
        )
        self.metadata_frame.pack(fill="x", pady=8)
        
        # Metadata grid
        self.metadata_grid = ctk.CTkFrame(self.metadata_frame, fg_color="transparent")
        self.metadata_grid.pack(fill="x", padx=16, pady=12)
        
        # Row 1: Title & Author
        row1 = ctk.CTkFrame(self.metadata_grid, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row1, text="Title:", font=ctk.CTkFont(weight="bold"), width=60, anchor="w").pack(side="left")
        self.meta_title = ctk.CTkLabel(row1, text="—", anchor="w")
        self.meta_title.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        row2 = ctk.CTkFrame(self.metadata_grid, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row2, text="Author:", font=ctk.CTkFont(weight="bold"), width=60, anchor="w").pack(side="left")
        self.meta_author = ctk.CTkLabel(row2, text="—", anchor="w")
        self.meta_author.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        # Row 3: Chapters & Est. Duration
        row3 = ctk.CTkFrame(self.metadata_grid, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row3, text="Chapters:", font=ctk.CTkFont(weight="bold"), width=60, anchor="w").pack(side="left")
        self.meta_chapters = ctk.CTkLabel(row3, text="—", anchor="w")
        self.meta_chapters.pack(side="left", padx=(8, 24))
        
        ctk.CTkLabel(row3, text="Est. Duration:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.meta_duration = ctk.CTkLabel(row3, text="—", anchor="w")
        self.meta_duration.pack(side="left", padx=(8, 0))
        
        # Output & Cover Section
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=8)
        
        # Left: Output Folder
        output_section = ctk.CTkFrame(options_frame, fg_color="transparent")
        output_section.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ctk.CTkLabel(
            output_section,
            text="Output Location",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        
        output_row = ctk.CTkFrame(output_section, fg_color="transparent")
        output_row.pack(fill="x", pady=(4, 0))
        
        self.output_label = ctk.CTkLabel(
            output_row,
            text="Same as input file",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8"),
            anchor="w"
        )
        self.output_label.pack(side="left", fill="x", expand=True)
        
        self.output_btn = ctk.CTkButton(
            output_row,
            text="Change",
            command=self.app.select_output,
            width=80,
            height=28,
            fg_color="transparent",
            border_width=1
        )
        self.output_btn.pack(side="right")
        CTkToolTip(self.output_btn, text="Choose where to save audiobooks")
        
        # Right: Cover Image
        cover_section = ctk.CTkFrame(options_frame, fg_color="transparent")
        cover_section.pack(side="right", padx=(8, 0))
        
        ctk.CTkLabel(
            cover_section,
            text="Cover Image",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        
        cover_row = ctk.CTkFrame(cover_section, fg_color="transparent")
        cover_row.pack(fill="x", pady=(4, 0))
        
        self.cover_label = ctk.CTkLabel(
            cover_row,
            text="Use EPUB cover",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8")
        )
        self.cover_label.pack(side="left", padx=(0, 8))
        
        self.select_cover_btn = ctk.CTkButton(
            cover_row,
            text="",
            image=self.icons.get('image'),
            width=32,
            height=28,
            command=self.app.select_cover,
            fg_color="transparent",
            border_width=1
        )
        self.select_cover_btn.pack(side="left", padx=(0, 4))
        CTkToolTip(self.select_cover_btn, text="Select custom cover image")
        
        self.clear_cover_btn = ctk.CTkButton(
            cover_row,
            text="",
            image=self.icons.get('trash'),
            width=32,
            height=28,
            command=self.app.clear_cover,
            fg_color="transparent",
            border_width=1,
            hover_color="#fee2e2"
        )
        self.clear_cover_btn.pack(side="left")
        CTkToolTip(self.clear_cover_btn, text="Remove custom cover")
        
        # Chapters button (prominent)
        self.chapters_btn = ctk.CTkButton(
            self,
            text="Edit Chapters & Content",
            image=self.icons.get('list'),
            compound="left",
            command=self.app.view_chapters,
            height=36,
            fg_color="transparent",
            border_width=1
        )
        self.chapters_btn.pack(fill="x", padx=20, pady=(8, 16))
        CTkToolTip(self.chapters_btn, text="View and edit chapter titles before conversion")
    
    def set_drag_hover(self, hovering):
        """Visual feedback during drag operations"""
        if hovering:
            self.drop_frame.configure(
                border_color="#3b82f6",
                fg_color=("#eff6ff", "#1e3a8a")
            )
            self.drop_label.configure(text="Drop EPUB file here")
        else:
            self.drop_frame.configure(
                border_color=("#cbd5e1", "#334155"),
                fg_color=("#f1f5f9", "#1e293b")
            )
            self.drop_label.configure(text="Drag & drop EPUB files here")
    
    def update_file_label(self, selected_epubs):
        if selected_epubs:
            count = len(selected_epubs)
            name = os.path.basename(selected_epubs[0])
            display_name = name if len(name) < 50 else name[:47] + "..."
            
            if count > 1:
                self.file_name_label.configure(text=f"{display_name} (+{count-1} more)")
            else:
                self.file_name_label.configure(text=display_name)
            
            # Show file info frame, hide drop zone
            self.drop_frame.pack_forget()
            self.file_info_frame.pack(fill="x", padx=20, pady=8, before=self.chapters_btn)
        else:
            self.file_name_label.configure(text="No file selected")
            self.file_info_frame.pack_forget()
            self.drop_frame.pack(fill="x", padx=20, pady=8, before=self.chapters_btn)
    
    def update_metadata(self, metadata, chapter_count=0):
        """Update metadata display"""
        title = metadata.get('title', 'Unknown Title')
        author = metadata.get('author', 'Unknown Author')
        
        # Estimate duration (rough calculation: ~150 words per minute)
        # Assuming average chapter has ~3000 words
        est_minutes = chapter_count * 20  # ~20 minutes per chapter
        hours = est_minutes // 60
        minutes = est_minutes % 60
        
        if hours > 0:
            duration_text = f"~{hours}h {minutes}m"
        else:
            duration_text = f"~{minutes}m"
        
        self.meta_title.configure(text=title if len(title) < 50 else title[:47] + "...")
        self.meta_author.configure(text=author if len(author) < 40 else author[:37] + "...")
        self.meta_chapters.configure(text=str(chapter_count))
        self.meta_duration.configure(text=duration_text)
    
    def update_cover_label(self, path=None):
        if path:
            filename = os.path.basename(path)
            display = filename if len(filename) < 25 else filename[:22] + "..."
            self.cover_label.configure(text=display, text_color="#22c55e")
        else:
            self.cover_label.configure(text="Use EPUB cover", text_color=("#64748b", "#94a3b8"))
            
    def update_output_label(self, path):
        if path:
            display = path if len(path) < 40 else "..." + path[-37:]
            self.output_label.configure(text=display, text_color="#22c55e")
        else:
            self.output_label.configure(text="Same as input file", text_color=("#64748b", "#94a3b8"))
