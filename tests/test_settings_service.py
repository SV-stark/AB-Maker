import unittest
from unittest.mock import MagicMock
from services.settings_service import SettingsService
from models.domain import VoiceSettings, OutputSettings, AudioFormat


class TestSettingsService(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock()
        # Mock simple key-value store for ConfigManager mock
        self.store = {}
        self.config_manager.get.side_effect = lambda key, default=None: self.store.get(key, default)
        self.config_manager.set.side_effect = lambda key, value: self.store.__setitem__(key, value)
        
        self.service = SettingsService(self.config_manager)

    def test_load_cache_and_get(self):
        # Default theme mode should be returned from constants config
        self.assertEqual(self.service.get_theme_mode(), "system")
        
        # Test basic set/get
        self.service.set("theme_mode", "dark")
        self.assertEqual(self.service.get_theme_mode(), "dark")
        self.config_manager.set.assert_called_with("theme_mode", "dark")

    def test_voice_settings_get_and_set(self):
        settings = VoiceSettings(
            model_name="en_US-amy-low",
            speed=1.2,
            speaker_id=5,
            use_gpu=True
        )
        self.service.set_voice_settings(settings)
        
        # Retrieve settings
        retrieved = self.service.get_voice_settings()
        self.assertEqual(retrieved.model_name, "en_US-amy-low")
        self.assertEqual(retrieved.speed, 1.2)
        self.assertEqual(retrieved.speaker_id, 5)
        self.assertTrue(retrieved.use_gpu)

    def test_output_settings_get_and_set(self):
        settings = OutputSettings(
            format=AudioFormat.MP3,
            quality="High",
            normalize=True
        )
        self.service.set_output_settings(settings)
        
        retrieved = self.service.get_output_settings()
        self.assertEqual(retrieved.format, AudioFormat.MP3)
        self.assertEqual(retrieved.quality, "High")
        self.assertTrue(retrieved.normalize)

    def test_reset_to_defaults(self):
        self.service.set("theme_mode", "dark")
        self.service.set("normalize", True)
        
        self.service.reset_to_defaults()
        self.assertEqual(self.service.get_theme_mode(), "system")
        self.assertFalse(self.service.get("normalize"))


if __name__ == '__main__':
    unittest.main()
