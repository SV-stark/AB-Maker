"""
Chapter Editor Dialog with Selection Support
Edit chapter titles and select which chapters to convert
"""
import customtkinter as ctk
import os
from tkinter import messagebox


class ChapterEditorDialog(ctk.CTkToplevel):
    """Dialog for editing chapters and selecting which to include in conversion."""
    
    def __init__(self, parent, chapters, icons, on_save_callback):
        super().__init__(parent)
        self.title("Edit Chapters")
        self.geometry("700x550")
        self.transient(parent)
        self.grab_set()
        
        self.chapters = chapters
        self.icons = icons
        self.on_save = on_save_callback
        self.checkboxes = []
        self.entries = []
        
        self._create_ui()
        self._update_selection_count()

    def _create_ui(self):
        """Create the dialog UI with selection support."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)
        
        # Title and count
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        
        ctk.CTkLabel(
            title_row, 
            text=f"Edit Chapters ({len(self.chapters)})", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        self.selection_label = ctk.CTkLabel(
            title_row,
            text="0 selected",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.selection_label.pack(side="right")
        
        # Selection controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            controls,
            text="Select All",
            width=90,
            height=24,
            command=self._select_all
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            controls,
            text="Deselect All",
            width=90,
            height=24,
            command=self._deselect_all
        ).pack(side="left", padx=2)
        
        ctk.CTkLabel(
            controls,
            text="💡 Uncheck chapters to exclude them from conversion",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="left", padx=(15, 0))
        
        # Column headers
        headers = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        headers.pack(fill="x", padx=15, pady=(5, 0))
        
        ctk.CTkLabel(headers, text="✓", width=30, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="#", width=30, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Chapter Title", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Length", width=80, font=ctk.CTkFont(weight="bold")).pack(side="right", padx=5)
        
        # Scrollable frame for chapters
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=5)
        
        self._populate_chapters()
        
        # Actions
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkButton(
            actions, 
            text="Save Changes", 
            image=self.icons.get('save'), 
            compound="left", 
            command=self._save_changes,
            width=120
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            actions, 
            text="Reset", 
            command=self._reset, 
            fg_color="transparent", 
            border_width=1, 
            text_color=("gray10", "gray90"),
            width=80
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            actions, 
            text="Close", 
            command=self.destroy, 
            fg_color="transparent", 
            text_color="gray",
            width=80
        ).pack(side="left", padx=5)

    def _populate_chapters(self):
        """Populate the scrollable area with chapter rows."""
        for i, ch in enumerate(self.chapters):
            row = ctk.CTkFrame(self.scroll, fg_color=("gray95", "gray20"))
            row.pack(fill="x", pady=2, padx=2)
            
            # Checkbox for selection
            selected_var = ctk.BooleanVar(value=ch.get('selected', True))
            checkbox = ctk.CTkCheckBox(
                row, 
                text="", 
                variable=selected_var,
                width=30,
                command=self._update_selection_count
            )
            checkbox.pack(side="left", padx=5)
            self.checkboxes.append(selected_var)
            
            # Chapter number
            ctk.CTkLabel(row, text=f"{i+1}.", width=30).pack(side="left", padx=5)
            
            # Title entry
            entry = ctk.CTkEntry(row)
            entry.insert(0, ch['title'])
            entry.pack(side="left", fill="x", expand=True, padx=5, pady=2)
            self.entries.append(entry)
            
            # Character count
            char_count = len(ch.get('content', ''))
            ctk.CTkLabel(
                row, 
                text=f"{char_count:,} chars", 
                text_color="gray", 
                width=80
            ).pack(side="right", padx=5)

    def _update_selection_count(self):
        """Update the selection counter label."""
        selected_count = sum(1 for cb in self.checkboxes if cb.get())
        total_count = len(self.checkboxes)
        self.selection_label.configure(text=f"{selected_count} of {total_count} selected")

    def _select_all(self):
        """Select all chapters."""
        for cb in self.checkboxes:
            cb.set(True)
        self._update_selection_count()

    def _deselect_all(self):
        """Deselect all chapters."""
        for cb in self.checkboxes:
            cb.set(False)
        self._update_selection_count()

    def _save_changes(self):
        """Save chapter titles and selection states."""
        # Update chapters with new titles and selections
        for i, (entry, checkbox) in enumerate(zip(self.entries, self.checkboxes)):
            self.chapters[i]['title'] = entry.get()
            self.chapters[i]['selected'] = checkbox.get()
        
        # Check if at least one chapter is selected
        selected_count = sum(1 for ch in self.chapters if ch.get('selected', True))
        if selected_count == 0:
            messagebox.showwarning("Warning", "At least one chapter must be selected for conversion.")
            return
        
        if self.on_save():
            messagebox.showinfo("Success", f"Chapter settings saved! ({selected_count} chapters selected)")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to save changes.")

    def _reset(self):
        """Reset chapters to their original state."""
        if messagebox.askyesno("Reset", "Reload from EPUB? This will discard all changes."):
            self.destroy()
            # Parent should reopen dialog with fresh data
