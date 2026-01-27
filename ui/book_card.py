import customtkinter as ctk
import os
from ui.tooltip import CTkToolTip

class BookCardUI(ctk.CTkFrame):
    def __init__(self, parent, app, icons, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.icons = icons
        
        ctk.CTkLabel(self, text="📖 Book & Cover", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Row 1: EPUB | Drop Target Hint
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)
        
        self.file_label = ctk.CTkLabel(row1, text="Drag & Drop EPUB here...", text_color="gray")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)
        # Select Files Button
        self.select_files_btn = ctk.CTkButton(
            row1, 
            text="Browse", 
            image=self.icons['folder'], 
            compound="left", 
            command=self.app.select_files, 
            width=100
        )
        self.select_files_btn.pack(side="right", padx=10)
        CTkToolTip(self.select_files_btn, text="Browse for EPUB files")
        
        # Row 2: Cover & Chapters
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=5)
        
        self.cover_label = ctk.CTkLabel(row2, text="Default Cover", text_color="gray")
        self.cover_label.pack(side="left", padx=5)
        
        # Tools
        # Chapter Edit
        self.chapters_btn = ctk.CTkButton(
            row2, text="", image=self.icons['list'], width=30, 
            command=self.app.view_chapters, 
            fg_color="transparent", border_width=1, 
            text_color=("gray10", "gray90"), hover_color=("gray90", "gray20")
        )
        self.chapters_btn.pack(side="right", padx=2)
        CTkToolTip(self.chapters_btn, text="Edit chapter titles")
        
        # Clear Cover
        self.clear_cover_btn = ctk.CTkButton(
            row2, text="", image=self.icons['trash'], width=30, 
            command=self.app.clear_cover, 
            fg_color="transparent", border_width=1, 
            text_color=("gray10", "gray90"), hover_color="#fee2e2"
        )
        self.clear_cover_btn.pack(side="right", padx=2)
        CTkToolTip(self.clear_cover_btn, text="Remove custom cover")
        
        # Select Cover
        self.select_cover_btn = ctk.CTkButton(
            row2, text="", image=self.icons['image'], width=30, 
            command=self.app.select_cover, 
            fg_color="transparent", border_width=1, 
            text_color=("gray10", "gray90"), hover_color=("gray90", "gray20")
        )
        self.select_cover_btn.pack(side="right", padx=2)
        CTkToolTip(self.select_cover_btn, text="Select custom cover image")
        
        # Output Folder
        self.output_btn = ctk.CTkButton(
            row2, text="Output Folder", image=self.icons['folder'], compound="left", 
            command=self.app.select_output, width=120, 
            fg_color="transparent", border_width=1
        )
        self.output_btn.pack(side="right", padx=5)
        CTkToolTip(self.output_btn, text="Choose where to save audiobooks")
        
        self.output_label = ctk.CTkLabel(row2, text="", text_color="gray") # Hidden by default until selected
        self.output_label.pack(side="right", padx=5)
        
    def update_file_label(self, selected_epubs):
        if selected_epubs:
            count = len(selected_epubs)
            name = os.path.basename(selected_epubs[0])
            self.file_label.configure(text=f"{count} file(s): {name}{'...' if count > 1 else ''}")
        else:
            self.file_label.configure(text="No files selected")
            
    def update_cover_label(self, path=None):
        if path:
            self.cover_label.configure(text=os.path.basename(path))
        else:
            self.cover_label.configure(text="Default (From EPUB)")
            
    def update_output_label(self, path):
        if path:
            self.output_label.configure(text=path)
