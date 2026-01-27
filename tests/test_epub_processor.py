import unittest
import os
import shutil
import json
from unittest.mock import MagicMock, patch
from epub_processor import EpubProcessor
import ebooklib

class TestEpubProcessor(unittest.TestCase):
    def setUp(self):
        self.cache_dir = "tests/.test_cache"
        self.processor = EpubProcessor(cache_dir=self.cache_dir)

    def tearDown(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    @patch('epub_processor.epub.read_epub')
    def test_extract_chapters_valid(self, mock_read_epub):
        # Mock the book structure
        mock_book = MagicMock()
        mock_item = MagicMock()
        mock_item.get_type.return_value = ebooklib.ITEM_DOCUMENT
        mock_item.get_content.return_value = b'<h1>Intro</h1><p>Test content</p>'
        
        # Setup spine
        mock_book.spine = [('id1', 'yes')]
        mock_book.get_item_with_id.return_value = mock_item
        mock_read_epub.return_value = mock_book

        chapters = self.processor.extract_chapters("dummy.epub")
        
        self.assertEqual(len(chapters), 1)
        self.assertEqual(chapters[0]['title'], 'Intro')
        self.assertIn('Test content', chapters[0]['content'])

    @patch('epub_processor.epub.read_epub')
    def test_caching(self, mock_read_epub):
        # 1. Setup Mock
        mock_book = MagicMock()
        mock_item = MagicMock()
        mock_item.get_type.return_value = ebooklib.ITEM_DOCUMENT
        mock_item.get_content.return_value = b'<h1>Cached</h1>'
        mock_book.spine = [('id1', 'yes')]
        mock_book.get_item_with_id.return_value = mock_item
        mock_read_epub.return_value = mock_book
        
        # Mock os.path.getmtime to return constant
        with patch('os.path.getmtime', return_value=12345):
             # First run - should call read_epub
            self.processor.extract_chapters("book.epub")
            mock_read_epub.assert_called_once()
            
            # Reset mock
            mock_read_epub.reset_mock()
            
            # Second run - should NOT call read_epub (hit cache)
            chapters = self.processor.extract_chapters("book.epub")
            mock_read_epub.assert_not_called()
            self.assertEqual(chapters[0]['title'], 'Cached')

if __name__ == '__main__':
    unittest.main()
