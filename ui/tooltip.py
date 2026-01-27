"""
Tooltip utilities for CustomTkinter widgets
"""
import customtkinter as ctk

class CTkToolTip:
    """
    Simple tooltip implementation for CustomTkinter widgets.
    
    Usage:
        button = ctk.CTkButton(parent, text="Click me")
        CTkToolTip(button, text="This button does something cool")
    """
    
    def __init__(self, widget, text="", delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None
        
        # Bind events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Button-1>", self._on_leave)
    
    def _on_enter(self, event=None):
        """Schedule tooltip to appear after delay."""
        self._cancel_scheduled()
        self.after_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event=None):
        """Hide tooltip and cancel scheduled appearance."""
        self._cancel_scheduled()
        self._hide_tooltip()
    
    def _cancel_scheduled(self):
        """Cancel scheduled tooltip appearance."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
    
    def _show_tooltip(self):
        """Display the tooltip."""
        if self.tooltip_window or not self.text:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create label
        label = ctk.CTkLabel(
            self.tooltip_window,
            text=self.text,
            fg_color=("gray85", "gray20"),
            corner_radius=6,
            padx=8,
            pady=4,
            font=ctk.CTkFont(size=11)
        )
        label.pack()
    
    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
