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

    def list_available_models(self):
        """
        Returns a list of available models to download.
        """
        return [
            {
                "name": "en_US-amy-low (Female)",
                "language": "English",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-amy-low.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-en_US-amy-low.tar.bz2",
                "extracted_dir": "vits-piper-en_US-amy-low",
                "model_file": "en_US-amy-low.onnx",
                "tokens_file": "tokens.txt",
                "data_file": "en_US-amy-low.onnx.json" # some models use different configs
            },
            {
                "name": "en_US-lessac-low (Female)",
                "language": "English",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-low.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-en_US-lessac-low.tar.bz2",
                "extracted_dir": "vits-piper-en_US-lessac-low",
                "model_file": "en_US-lessac-low.onnx",
                "tokens_file": "tokens.txt"
            },
            {
                "name": "en_US-ryan-low (Male)",
                "language": "English",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-ryan-low.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-en_US-ryan-low.tar.bz2",
                "extracted_dir": "vits-piper-en_US-ryan-low",
                "model_file": "en_US-ryan-low.onnx",
                "tokens_file": "tokens.txt"
            },
            {
                "name": "en_US-libritts-vits (Expressive)",
                "language": "English",
                "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-libritts_r-medium.tar.bz2",
                "type": "vits",
                "archive_name": "vits-piper-en_US-libritts_r-medium.tar.bz2",
                "extracted_dir": "vits-piper-en_US-libritts_r-medium",
                "model_file": "en_US-libritts_r-medium.onnx",
                "tokens_file": "tokens.txt"
            }
        ]

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
