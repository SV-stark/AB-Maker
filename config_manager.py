import json
import os
import logging

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self.config = self._load_from_disk()

    def _load_from_disk(self):
        """Loads config from disk or returns defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        # Default configuration
        return {
            "theme_mode": "system",
            "recent_files": [],
            "last_speed": 1.0,
            "last_speaker_id": "0",
            "use_gpu": False,
            "last_model": None,
            "output_format": "m4b"
        }

    def save(self):
        """Saves current config to disk."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def add_recent_file(self, path):
        """Adds a path to recent files, maintaining a max size of 10."""
        history = self.config.get("recent_files", [])
        
        # Remove if exists to move to top
        if path in history:
            history.remove(path)
            
        history.insert(0, path)
        self.config["recent_files"] = history[:10]
        self.save()

    def get_recent_files(self):
        return self.config.get("recent_files", [])
