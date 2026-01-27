import unittest
import threading
import time
from unittest.mock import MagicMock
from conversion_worker import ConversionWorker

class TestConversionWorker(unittest.TestCase):
    def setUp(self):
        self.tts = MagicMock()
        self.audio = MagicMock()
        self.log = MagicMock()
        self.progress = MagicMock()
        self.status = MagicMock()
        self.done = MagicMock()
        
        self.worker = ConversionWorker(
            self.tts, self.audio, self.log,
            self.progress, self.status, self.done
        )
        
        self.epub_proc = MagicMock()

    def test_cancel_immediately(self):
        # Setup mocks to simulate a long process we want to cancel
        self.epub_proc.extract_chapters.return_value = [{'title': 'Ch1', 'content': 'txt'}]
        # TTS generation takes a bit 
        self.tts.generate_audio.side_effect = lambda *args, **kwargs: True
        
        # Start worker
        self.worker.start(['book.epub'], {}, '', 1.0, 0, 'm4b', False, self.epub_proc)
        
        # Cancel immediately
        self.worker.cancel()
        
        # Wait for thread
        self.worker._thread.join(timeout=2.0)
        
        self.assertFalse(self.worker._thread.is_alive())
        # Should have logged cancellation
        # Depending on timing, it might have processed 0 or 1 chapter, but must be done.
        self.done.assert_called()

    def test_worker_flow_success(self):
        # Mock successful conversions
        self.epub_proc.extract_chapters.return_value = [{'title': 'Ch1', 'content': 'tx'}, {'title': 'Ch2', 'content': 'tx'}]
        self.tts.initialize_model.return_value = True
        self.tts.generate_audio.return_value = True
        
        self.worker._run_conversion(['book.epub'], {'extracted_dir': 'mod'}, '', 1.0, 0, 'wav', False, self.epub_proc)
        
        self.done.assert_called()
        self.assertEqual(self.tts.generate_audio.call_count, 2)

    def test_initialization_failure(self):
        self.tts.initialize_model.return_value = False
        self.worker._run_conversion(['book.epub'], {'extracted_dir': 'mod'}, '', 1.0, 0, 'wav', False, self.epub_proc)
        
        self.done.assert_called()
        self.tts.generate_audio.assert_not_called()

if __name__ == '__main__':
    unittest.main()
