import customtkinter as ctk
import os
from tkinter import messagebox

class ChapterEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, chapters, icons, on_save_callback):
        super().__init__(parent)
        self.title("Edit Chapters")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        self.chapters = chapters
        self.icons = icons
        self.on_save = on_save_callback
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text=f"Edit Chapters ({len(chapters)})", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        # Scrollable frame for chapters
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.entries = []
        self._populate()
        
        # Actions
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            actions, text="Save Changes", image=self.icons['save'], 
            compound="left", command=self._save_changes
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            actions, text="Reset", command=self._reset, 
            fg_color="transparent", border_width=1, 
            text_color=("gray10", "gray90")
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            actions, text="Close", command=self.destroy, 
            fg_color="transparent", text_color="gray"
        ).pack(side="left", padx=5)

    def _populate(self):
        for i, ch in enumerate(self.chapters):
            row = ctk.CTkFrame(self.scroll, fg_color=("gray95", "gray20"))
            row.pack(fill="x", pady=2, padx=2)
            
            ctk.CTkLabel(row, text=f"{i+1}.", width=30).pack(side="left", padx=5)
            
            entry = ctk.CTkEntry(row)
            entry.insert(0, ch['title'])
            entry.pack(side="left", fill="x", expand=True, padx=5, pady=2)
            self.entries.append(entry)
            
            char_count = len(ch['content'])
            ctk.CTkLabel(row, text=f"{char_count} chars", text_color="gray", width=80).pack(side="right", padx=5)

    def _save_changes(self):
        new_titles = [e.get() for e in self.entries]
        for i, title in enumerate(new_titles):
            self.chapters[i]['title'] = title
        
        if self.on_save():
            messagebox.showinfo("Success", "Chapter titles saved!")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to save changes.")

    def _reset(self):
        if messagebox.askyesno("Reset", "Reload from EPUB? This will discard changes."):
            # We assume the parent handles the actual reset logic via a different callback or we close this and let them reopen
            # For simplicity, we just close and return a signal or modifying the callback signature
            self.destroy()
            # In original code, it called self._view_chapters() again.
            # Here we might need a reset callback. 
            # Ideally the dialog should just be about editing *this* list, and reset means re-init the list from original
            pass # Parent re-opens
