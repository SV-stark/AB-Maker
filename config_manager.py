import json
import os
import logging
import shutil
import threading
import sys

class ConfigManager:
    APP_NAME = "AB-Maker"

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_data_dir = self._get_app_data_dir()
        self.config_file = os.path.join(self.app_data_dir, "config.json")
        
        # Ensure directory
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
            
        self._migrate_legacy_data()
        self.config = self._load_from_disk()
        
        # Debouncing
        self._save_timer = None
        self._lock = threading.Lock()

    def _get_app_data_dir(self):
        """Returns standard AppData path."""
        if sys.platform == "win32":
            base = os.getenv('APPDATA')
        else:
            base = os.path.join(os.path.expanduser("~"), ".local", "share")
        
        if not base:
             base = os.path.expanduser("~")
             
        return os.path.join(base, self.APP_NAME)
    
    def get_app_data_path(self):
        return self.app_data_dir
        
    def get_models_dir(self):
        path = os.path.join(self.app_data_dir, "models")
        if not os.path.exists(path): os.makedirs(path)
        return path

    def get_cache_dir(self):
        path = os.path.join(self.app_data_dir, ".cache")
        if not os.path.exists(path): os.makedirs(path)
        return path
    
    def get_logs_dir(self):
        path = os.path.join(self.app_data_dir, "logs")
        if not os.path.exists(path): os.makedirs(path)
        return path

    def _migrate_legacy_data(self):
        """Moves data from current working dir to AppData if found."""
        cwd = os.getcwd()
        if cwd == self.app_data_dir: return

        # Files/Folders to migrate
        items = {
            "config.json": self.config_file,
            "models": os.path.join(self.app_data_dir, "models"),
            ".cache": os.path.join(self.app_data_dir, ".cache"),
        }

        for src_name, dest_path in items.items():
            src_path = os.path.join(cwd, src_name)
            
            # Only migrate if source exists AND dest does NOT
            if os.path.exists(src_path) and not os.path.exists(dest_path):
                try:
                    self.logger.info(f"Migrating {src_name} to {dest_path}...")
                    if os.path.isdir(src_path):
                        # Move directory
                        shutil.move(src_path, dest_path)
                    else:
                        # Move file
                        shutil.move(src_path, dest_path)
                    self.logger.info("Migration successful.")
                except Exception as e:
                    self.logger.error(f"Migration failed for {src_name}: {e}")

    def _load_from_disk(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        return {
            "theme_mode": "system",
            "recent_files": [],
            "last_speed": 1.0,
            "last_speaker_id": "0",
            "use_gpu": False,
            "last_model": None,
            "output_format": "m4b",
            "last_quality": "Medium",
            "pause_sentence": 700,
            "pause_clause": 250,
            "pause_paragraph": 1500,
            "pause_dialogue": 400
        }

    def save(self):
        """Immediate save."""
        self._flush_save()

    def _flush_save(self):
        try:
            with self._lock:
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        with self._lock:
            if self.config.get(key) == value:
                return # No change
            
            self.config[key] = value
            
            # Cancel existing timer
            if self._save_timer:
                self._save_timer.cancel()
            
            # Schedule new save (Debounce 1.0s)
            self._save_timer = threading.Timer(1.0, self._flush_save)
            self._save_timer.start()

    def add_recent_file(self, path):
        history = self.config.get("recent_files", [])
        if path in history:
            history.remove(path)
        history.insert(0, path)
        self.set("recent_files", history[:10])

    def get_recent_files(self):
        return self.config.get("recent_files", [])
    
    # File Status Tracking
    def set_file_status(self, file_path, status):
        """
        Set the conversion status for a file.
        status: 'in_progress', 'completed', 'failed'
        """
        if "file_status" not in self.config:
            self.config["file_status"] = {}
        self.config["file_status"][file_path] = status
        self.save()
    
    def get_file_status(self, file_path):
        """Get the conversion status for a file."""
        return self.config.get("file_status", {}).get(file_path, None)
    
    def clear_file_status(self, file_path):
        """Clear the status for a file."""
        if "file_status" in self.config and file_path in self.config["file_status"]:
            del self.config["file_status"][file_path]
            self.save()

