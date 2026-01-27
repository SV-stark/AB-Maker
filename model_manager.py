import requests
import os
import tarfile
import zipfile
import shutil
import logging

class ModelManager:
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        self.logger = logging.getLogger(__name__)
        
        # Load models from JSON
        self.models_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models.json")
        self.models_catalog = self._load_models_catalog()

    def _load_models_catalog(self):
        """Loads models from models.json or returns defaults."""
        import json
        if os.path.exists(self.models_file):
            try:
                with open(self.models_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load models.json: {e}")
        
        # Fallback Defaults (if file missing or error)
        return [
            {
                "name": "en_US-amy-low (Female)",
                "language": "English (US)",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-amy-low.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-en_US-amy-low.tar.bz2",
                "extracted_dir": "vits-piper-en_US-amy-low",
                "model_file": "en_US-amy-low.onnx",
                "tokens_file": "tokens.txt",
                "data_file": "en_US-amy-low.onnx.json",
                "recommended": True
            },
            {
                "name": "en_US-ryan-low (Male)",
                "language": "English (US)",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-ryan-low.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-en_US-ryan-low.tar.bz2",
                "extracted_dir": "vits-piper-en_US-ryan-low",
                "model_file": "en_US-ryan-low.onnx",
                "tokens_file": "tokens.txt",
                "recommended": True
            },
            {
                "name": "es_ES-sharvard-medium (Spanish Male)",
                "language": "Spanish",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_ES-sharvard-medium.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-es_ES-sharvard-medium.tar.bz2",
                "extracted_dir": "vits-piper-es_ES-sharvard-medium",
                "model_file": "es_ES-sharvard-medium.onnx",
                "tokens_file": "tokens.txt",
                "recommended": False
            },
            {
                "name": "fr_FR-siwis-medium (French Female)",
                "language": "French",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-fr_FR-siwis-medium.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-fr_FR-siwis-medium.tar.bz2",
                "extracted_dir": "vits-piper-fr_FR-siwis-medium",
                "model_file": "fr_FR-siwis-medium.onnx",
                "tokens_file": "tokens.txt",
                "recommended": False
            },
            {
                "name": "de_DE-thorsten-medium (German Male)",
                "language": "German",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-de_DE-thorsten-medium.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-de_DE-thorsten-medium.tar.bz2",
                "extracted_dir": "vits-piper-de_DE-thorsten-medium",
                "model_file": "de_DE-thorsten-medium.onnx",
                "tokens_file": "tokens.txt",
                "recommended": False
            }
        ]

    def list_available_models(self, only_recommended=False):
        """
        Returns a list of available models to download.
        Args:
            only_recommended (bool): If True, filters list to only showing models marked 'recommended'.
        """
        if only_recommended:
            return [m for m in self.models_catalog if m.get('recommended', False)]
        return self.models_catalog

    def is_model_installed(self, model_info):
        """Checks if a model works and is installed"""
        path = os.path.join(self.models_dir, model_info['extracted_dir'])
        return os.path.exists(path)

    def download_model(self, model_info, progress_callback=None):
        """
        Downloads and extracts a specific model.
        """
        url = model_info['url']
        filename = model_info['archive_name']
        save_path = os.path.join(self.models_dir, filename)

        if not self.is_model_installed(model_info):
            self.logger.info(f"Downloading {model_info['name']}...")
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total_size)
                
                self.logger.info("Download complete. Extracting...")
                self._extract(save_path)
                self.logger.info("Extraction complete.")
                
                # Cleanup archive
                os.remove(save_path)
                return True
            except Exception as e:
                self.logger.error(f"Error downloading model: {e}")
                return False
        return True

    def _extract(self, archive_path):
        """Extracts tar.bz2 or zip archives"""
        if archive_path.endswith('.tar.bz2') or archive_path.endswith('.tar.gz'):
            with tarfile.open(archive_path, "r:*") as tar:
                tar.extractall(path=self.models_dir)
        elif archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(self.models_dir)
