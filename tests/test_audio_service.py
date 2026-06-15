import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Mock sounddevice and soundfile before import to prevent platform-specific loading failures
sys.modules['sounddevice'] = MagicMock()
sys.modules['soundfile'] = MagicMock()

from services.audio_service import AudioService
from models.domain import VoiceSettings


class TestAudioService(unittest.TestCase):
    def setUp(self):
        self.tts_engine = MagicMock()
        self.config_manager = MagicMock()
        self.config_manager.get_models_dir.return_value = "/mock/models"
        
        self.service = AudioService(self.tts_engine, self.config_manager)

    def test_speed_validation(self):
        # Valid range default is 0.5 to 2.5
        self.assertEqual(self.service.validate_speed(1.5), 1.5)
        self.assertEqual(self.service.validate_speed(0.2), 0.5)  # clamped to min
        self.assertEqual(self.service.validate_speed(4.0), 2.5)  # clamped to max

    def test_generate_preview_success(self):
        self.tts_engine.initialize_model.return_value = True
        self.tts_engine.generate_audio.return_value = True
        
        voice_settings = VoiceSettings(model_name="test-model", speed=1.0, speaker_id=0, use_gpu=False)
        model_info = {"name": "test-model", "extracted_dir": "extracted"}
        
        progress_cb = MagicMock()
        complete_cb = MagicMock()
        
        with patch('tempfile.mkstemp', return_value=(999, "/tmp/preview.wav")):
            with patch('os.close') as mock_close:
                res_path = self.service.generate_preview(
                    voice_settings=voice_settings,
                    model_info=model_info,
                    progress_callback=progress_cb,
                    complete_callback=complete_cb
                )
                
                self.assertIsNotNone(res_path)
                self.tts_engine.initialize_model.assert_called()
                self.tts_engine.generate_audio.assert_called()
                progress_cb.assert_any_call(1.0)
                complete_cb.assert_called_with(Path("/tmp/preview.wav"))

    def test_generate_preview_failure(self):
        self.tts_engine.initialize_model.return_value = False
        
        voice_settings = VoiceSettings(model_name="test-model", speed=1.0, speaker_id=0, use_gpu=False)
        model_info = {"name": "test-model", "extracted_dir": "extracted"}
        
        error_cb = MagicMock()
        
        with patch('tempfile.mkstemp', return_value=(999, "/tmp/preview.wav")):
            with patch('os.close'):
                res_path = self.service.generate_preview(
                    voice_settings=voice_settings,
                    model_info=model_info,
                    error_callback=error_cb
                )
                
                self.assertIsNone(res_path)
                error_cb.assert_called()


if __name__ == '__main__':
    unittest.main()
