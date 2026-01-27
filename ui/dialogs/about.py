import customtkinter as ctk
import webbrowser
from PIL import Image, ImageDraw

class AboutDialog(ctk.CTkToplevel):
    def __init__(self, parent, icons):
        super().__init__(parent)
        self.title("About AB-Maker")
        self.geometry("400x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create a large logo
        logo_img = self._create_large_logo()
        
        # Logo Display
        self.logo_label = ctk.CTkLabel(self, text="", image=logo_img)
        self.logo_label.pack(pady=(30, 20))
        
        # App name and Version
        ctk.CTkLabel(self, text="AB-Maker", font=ctk.CTkFont(size=24, weight="bold")).pack()
        ctk.CTkLabel(self, text="Version 1.1.0", font=ctk.CTkFont(size=12), text_color="gray").pack()
        
        # Description
        desc_text = "A professional, offline audiobook creator that\ntransforms your EPUBs into high-quality audio."
        ctk.CTkLabel(self, text=desc_text, font=ctk.CTkFont(size=13), pady=20).pack()
        
        # Info Table
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=10)
        
        # Author
        ctk.CTkLabel(info_frame, text="Author:", font=ctk.CTkFont(weight="bold"), anchor="e").grid(row=0, column=0, padx=10, pady=2)
        ctk.CTkLabel(info_frame, text="SV-Stark", anchor="w").grid(row=0, column=1, padx=10, pady=2)
        
        # License
        ctk.CTkLabel(info_frame, text="License:", font=ctk.CTkFont(weight="bold"), anchor="e").grid(row=1, column=0, padx=10, pady=2)
        ctk.CTkLabel(info_frame, text="AGPL v3", anchor="w").grid(row=1, column=1, padx=10, pady=2)
        
        # GitHub Button
        self.github_button = ctk.CTkButton(
            self, 
            text="GitHub Repository", 
            command=lambda: webbrowser.open("https://github.com/SV-Stark/AB-Maker"),
            fg_color="#3b82f6",
            hover_color="#2563eb"
        )
        self.github_button.pack(pady=20)
        
        # Footer
        ctk.CTkLabel(self, text="© 2026 AB-Maker Project", font=ctk.CTkFont(size=10), text_color="gray").pack(side="bottom", pady=10)

    def _create_large_logo(self):
        size = (120, 120)
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Scale factor (original was 20x20)
        s = size[0] / 20
        
        # Outer circle
        draw.ellipse([0, 0, size[0]-1, size[1]-1], fill="#3b82f6")
        # Headphone band
        draw.arc([4*s, 4*s, 15*s, 15*s], start=180, end=0, fill="white", width=int(2*s))
        # Book
        draw.rectangle([7*s, 8*s, 13*s, 16*s], fill="white")
        # Earcups
        draw.rectangle([3*s, 11*s, 5*s, 15*s], fill="white")
        draw.rectangle([14*s, 11*s, 16*s, 15*s], fill="white")
        
        return ctk.CTkImage(img, size=size)
