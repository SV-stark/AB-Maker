import unittest
import os
import json
from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_config = "tests/test_config.json"
        # Ensure clean state
        if os.path.exists(self.test_config):
            os.remove(self.test_config)
        self.mgr = ConfigManager(self.test_config)

    def tearDown(self):
        if os.path.exists(self.test_config):
            os.remove(self.test_config)

    def test_defaults(self):
        self.assertEqual(self.mgr.get("theme_mode"), "system")
        self.assertEqual(self.mgr.get("last_speed"), 1.0)

    def test_save_and_load(self):
        self.mgr.set("theme_mode", "dark")
        self.mgr.set("last_speed", 1.5)
        self.mgr.save()
        
        # Reload
        new_mgr = ConfigManager(self.test_config)
        self.assertEqual(new_mgr.get("theme_mode"), "dark")
        self.assertEqual(new_mgr.get("last_speed"), 1.5)

    def test_recent_files_limit(self):
        # Add 12 files
        for i in range(12):
            self.mgr.add_recent_file(f"file_{i}.epub")
            
        history = self.mgr.get_recent_files()
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0], "file_11.epub") # Most recent on top

    def test_recent_files_deduplication(self):
        self.mgr.add_recent_file("a.epub")
        self.mgr.add_recent_file("b.epub")
        self.mgr.add_recent_file("a.epub") # Add 'a' again
        
        history = self.mgr.get_recent_files()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], "a.epub") # moved to top

if __name__ == '__main__':
    unittest.main()
