import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from services.conversion_service import ConversionService
from models.domain import VoiceSettings, OutputSettings, AudioFormat, ConversionStatus


class TestConversionService(unittest.TestCase):
    def setUp(self):
        self.tts_engine = MagicMock()
        self.audio_builder = MagicMock()
        self.epub_processor = MagicMock()
        self.model_manager = MagicMock()
        self.config_manager = MagicMock()
        self.event_bus = MagicMock()
        
        # Setup mock chapter list
        self.epub_processor.extract_chapters.return_value = [
            {'title': 'Chapter 1', 'content': 'Hello world'}
        ]
        
        # Setup mock models list
        self.model_manager.list_available_models.return_value = [
            {'name': 'en-model-1', 'extracted_dir': 'dir1', 'num_speakers': 1}
        ]

        self.service = ConversionService(
            tts_engine=self.tts_engine,
            audio_builder=self.audio_builder,
            epub_processor=self.epub_processor,
            model_manager=self.model_manager,
            config_manager=self.config_manager,
            event_bus=self.event_bus
        )

    def test_create_job(self):
        voice = VoiceSettings(model_name="en-model-1", speed=1.0, speaker_id=0, use_gpu=False)
        output = OutputSettings(format=AudioFormat.M4B, quality="Medium", normalize=False)
        
        epub_path = Path("/mock/book.epub")
        job = self.service.create_job(epub_path, voice, output)
        
        self.assertEqual(job.book_metadata.title, "book")
        self.assertEqual(len(job.book_metadata.chapters), 1)
        self.assertEqual(job.status, ConversionStatus.PENDING)
        self.event_bus.emit.assert_called_with("job_created", job=job)

    @patch('conversion_worker.ConversionWorker')
    def test_start_and_cancel_job(self, mock_worker_class):
        mock_worker_inst = MagicMock()
        mock_worker_class.return_value = mock_worker_inst
        
        voice = VoiceSettings(model_name="en-model-1", speed=1.0, speaker_id=0, use_gpu=False)
        output = OutputSettings(format=AudioFormat.M4B, quality="Medium", normalize=False)
        epub_path = Path("/mock/book.epub")
        
        job = self.service.create_job(epub_path, voice, output)
        
        # Start job
        success = self.service.start_job(job.id)
        self.assertTrue(success)
        self.assertEqual(job.status, ConversionStatus.IN_PROGRESS)
        mock_worker_inst.start.assert_called_once()
        
        # Cancel job
        cancel_success = self.service.cancel_job(job.id)
        self.assertTrue(cancel_success)
        mock_worker_inst.cancel.assert_called_once()


if __name__ == '__main__':
    unittest.main()
