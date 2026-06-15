import unittest
from unittest.mock import MagicMock
from pathlib import Path
import os
import tempfile
import shutil
from services.file_service import FileService
from models.domain import ConversionStatus


class TestFileService(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock()
        self.config_manager.get_recent_files.return_value = []
        self.config_manager.get_file_status.return_value = None
        
        self.temp_dir = tempfile.mkdtemp()
        self.service = FileService(self.config_manager)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_validate_epub_file(self):
        # Non-existent file
        non_existent = Path(self.temp_dir) / "missing.epub"
        is_valid, err = self.service.validate_epub_file(non_existent)
        self.assertFalse(is_valid)
        self.assertIn("File not found", err)

        # Wrong extension
        bad_ext = Path(self.temp_dir) / "file.txt"
        bad_ext.touch()
        is_valid, err = self.service.validate_epub_file(bad_ext)
        self.assertFalse(is_valid)
        self.assertIn("Not an EPUB file", err)

        # Valid EPUB path
        good_epub = Path(self.temp_dir) / "book.epub"
        good_epub.touch()
        is_valid, err = self.service.validate_epub_file(good_epub)
        self.assertTrue(is_valid)

    def test_validate_cover_image(self):
        # Valid format
        img = Path(self.temp_dir) / "cover.png"
        img.touch()
        is_valid, _ = self.service.validate_cover_image(img)
        self.assertTrue(is_valid)

        # Invalid format
        img_bad = Path(self.temp_dir) / "cover.txt"
        img_bad.touch()
        is_valid, err = self.service.validate_cover_image(img_bad)
        self.assertFalse(is_valid)

    def test_validate_output_directory(self):
        out_dir = Path(self.temp_dir) / "output"
        is_valid, _ = self.service.validate_output_directory(out_dir)
        self.assertTrue(is_valid)
        self.assertTrue(out_dir.exists())

    def test_add_recent_files_and_status(self):
        file_path = Path(self.temp_dir) / "book1.epub"
        file_path.touch()
        
        self.service.add_recent_file(file_path, "Book One")
        self.config_manager.add_recent_file.assert_called_with(str(file_path))
        
        # Test status update
        self.service.update_file_status(file_path, ConversionStatus.COMPLETED)
        self.config_manager.set_file_status.assert_called_with(str(file_path), "completed")

    def test_suggest_output_path(self):
        epub = Path("/path/to/my book.epub")
        suggested = self.service.suggest_output_path(epub, "m4b")
        self.assertEqual(suggested.name, "my book_audiobook.m4b")

    def test_check_disk_space(self):
        # Test checking space
        has_space, avail = self.service.check_disk_space(Path(self.temp_dir), 1.0)
        self.assertTrue(has_space)
        self.assertGreater(avail, 0.0)


if __name__ == '__main__':
    unittest.main()
