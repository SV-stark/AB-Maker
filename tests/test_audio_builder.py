import unittest
import os
import shutil
from unittest.mock import patch, MagicMock
from audio_builder import AudioBuilder

class TestAudioBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = AudioBuilder()
        self.test_dir = "tests/audio_test"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_ffmpeg(self):
        # This depends on system state, but we expect it to return bool
        result = self.builder.check_ffmpeg()
        self.assertIsInstance(result, bool)

    def test_create_chapter_metadata(self):
        chapters = [
            {'title': 'Chapter 1', 'duration': 10.5},
            {'title': 'Chapter 2', 'duration': 20.0}
        ]
        metadata_file = os.path.join(self.test_dir, "metadata.txt")
        self.builder.create_chapter_metadata(chapters, metadata_file)
        
        self.assertTrue(os.path.exists(metadata_file))
        with open(metadata_file, 'r') as f:
            content = f.read()
            self.assertIn(";FFMETADATA1", content)
            self.assertIn("title=Chapter 1", content)
            self.assertIn("START=0", content)
            self.assertIn("END=10500", content) # 10.5s * 1000

    @patch('subprocess.run')
    def test_merge_chapters_to_m4b(self, mock_run):
        # Mock successful subprocess
        mock_run.return_value = MagicMock(returncode=0)
        
        files = ["file1.wav", "file2.wav"]
        output = os.path.join(self.test_dir, "book.m4b")
        metadata = os.path.join(self.test_dir, "meta.txt")
        with open(metadata, 'w') as f: f.write("meta")
        
        success = self.builder.merge_chapters_to_m4b(files, output, metadata)
        self.assertTrue(success)
        mock_run.assert_called_once()
        
        args = mock_run.call_args[0][0]
        self.assertIn("ffmpeg", args[0])
        self.assertIn("-f", args)
        self.assertIn("concat", args)

if __name__ == '__main__':
    unittest.main()
