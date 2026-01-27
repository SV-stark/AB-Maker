import unittest
import os
import shutil
from unittest.mock import patch, MagicMock
from model_manager import ModelManager

class TestModelManager(unittest.TestCase):
    def setUp(self):
        self.test_models_dir = "tests/models"
        self.manager = ModelManager(models_dir=self.test_models_dir)

    def tearDown(self):
        if os.path.exists(self.test_models_dir):
            shutil.rmtree(self.test_models_dir)

    def test_list_models(self):
        models = self.manager.list_available_models()
        self.assertTrue(len(models) > 0)
        self.assertIn("name", models[0])

    def test_is_model_installed(self):
        model_info = {'extracted_dir': 'test_model'}
        self.assertFalse(self.manager.is_model_installed(model_info))
        
        # Fake install
        os.makedirs(os.path.join(self.test_models_dir, 'test_model'))
        self.assertTrue(self.manager.is_model_installed(model_info))

    @patch('requests.get')
    @patch('model_manager.ModelManager._extract')
    def test_download_model_success(self, mock_extract, mock_get):
        # Mock requests Response
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '100'}
        mock_response.iter_content.return_value = [b'data'] * 10
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        model_info = {
            'name': 'Test Model',
            'url': 'http://example.com/model.tar.bz2',
            'archive_name': 'model.tar.bz2',
            'extracted_dir': 'test_model_extracted'
        }
        
        success = self.manager.download_model(model_info)
        self.assertTrue(success)
        mock_get.assert_called_with(model_info['url'], stream=True)
        mock_extract.assert_called()

if __name__ == '__main__':
    unittest.main()
