import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock sherpa_onnx before importing tts_engine
sys.modules['sherpa_onnx'] = MagicMock()

from tts_engine import TTSEngine

class TestTTSEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TTSEngine()

    def test_init_model_success(self):
        config = {
            'model_dir': '/tmp/model',
            'model_file': 'model.onnx',
            'tokens_file': 'tokens.txt'
        }
        
        # Mock validation to return True
        sys.modules['sherpa_onnx'].OfflineTts.validate_config.return_value = True
        
        success = self.engine.initialize_model(config)
        self.assertTrue(success)
        self.assertIsNotNone(self.engine.tts)

    def test_init_model_failure(self):
        # Mock validation to return False
        sys.modules['sherpa_onnx'].OfflineTts.validate_config.return_value = False
        
        success = self.engine.initialize_model({})
        self.assertFalse(success)

    def test_generate_audio_no_init(self):
        success = self.engine.generate_audio("Test", "out.wav")
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
