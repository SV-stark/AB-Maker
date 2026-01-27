import customtkinter as ctk
import os
from tkinter import messagebox

class ModelManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent, model_manager, icons, on_change_callback):
        super().__init__(parent)
        self.title("Model Manager")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self.model_manager = model_manager
        self.icons = icons
        self.on_change = on_change_callback
        
        ctk.CTkLabel(self, text="Installed Models", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._populate()
        
        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=10)
        
    def _populate(self):
        # Clear existing
        for w in self.scroll.winfo_children(): w.destroy()
        
        all_models = self.model_manager.list_available_models(only_recommended=False)
        models_dir = self.model_manager.models_dir
        installed_found = False
        
        for m in all_models:
            m_path = os.path.join(models_dir, m['extracted_dir'])
            if os.path.exists(m_path):
                installed_found = True
                row = ctk.CTkFrame(self.scroll, fg_color=("gray95", "gray20"))
                row.pack(fill="x", pady=2, padx=2)
                
                # Icon + Name
                ctk.CTkLabel(row, text="📦", font=ctk.CTkFont(size=16)).pack(side="left", padx=5)
                
                info_frame = ctk.CTkFrame(row, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(info_frame, text=m['name'], font=ctk.CTkFont(weight="bold")).pack(anchor="w")
                
                size_mb = self._get_size(m_path)
                ctk.CTkLabel(info_frame, text=f"{size_mb:.1f} MB  •  {m.get('language', 'en')}", text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w")
                
                # Delete Action
                def delete_m(model=m):
                    if messagebox.askyesno("Delete", f"Delete model '{model['name']}'?"):
                        try:
                            import shutil
                            shutil.rmtree(os.path.join(models_dir, model['extracted_dir']))
                            self._populate() # Refresh self
                            self.on_change() # Notify app
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to delete: {e}")

                ctk.CTkButton(
                    row, text="", image=self.icons['trash'], width=30, height=30, 
                    command=delete_m, fg_color="transparent", hover_color="#fee2e2"
                ).pack(side="right", padx=5)

        if not installed_found:
            ctk.CTkLabel(self.scroll, text="No models installed.", text_color="gray").pack(pady=20)

    def _get_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size / (1024 * 1024) # MB
