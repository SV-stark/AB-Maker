"""
Model Service
Manages TTS models, downloads, and availability
"""
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
import logging

from models.domain import ModelInfo
from config.constants import get_config

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing TTS models."""
    
    def __init__(self, model_manager, config_manager):
        """
        Initialize model service.
        
        Args:
            model_manager: ModelManager instance
            config_manager: ConfigManager instance
        """
        self._model_manager = model_manager
        self._config_manager = config_manager
        self._app_config = get_config()
        self._model_cache: Dict[str, ModelInfo] = {}
        self._refresh_cache()
    
    def _refresh_cache(self):
        """Refresh model cache from model manager."""
        self._model_cache.clear()
        
        try:
            # Get all models from manager
            models = self._model_manager.list_available_models(only_recommended=False)
            
            for model_data in models:
                model_info = self._convert_to_model_info(model_data)
                self._model_cache[model_info.name] = model_info
                
        except Exception as e:
            logger.error(f"Failed to refresh model cache: {e}")
    
    def _convert_to_model_info(self, model_data: Dict) -> ModelInfo:
        """Convert model dict to ModelInfo."""
        models_dir = self._config_manager.get_models_dir()
        extracted_dir = model_data.get('extracted_dir', '')
        local_path = Path(models_dir) / extracted_dir if extracted_dir else None
        
        return ModelInfo(
            name=model_data.get('name', 'Unknown'),
            language=model_data.get('language', 'unknown'),
            quality=model_data.get('quality', 'medium'),
            size_mb=float(model_data.get('size_mb', 0)),
            description=model_data.get('description', ''),
            download_url=model_data.get('download_url'),
            local_path=local_path,
            is_recommended=bool(model_data.get('is_recommended', model_data.get('recommended', False)))
        )
    
    def get_available_models(
        self,
        language: Optional[str] = None,
        only_recommended: bool = False
    ) -> List[ModelInfo]:
        """
        Get list of available models.
        
        Args:
            language: Optional language filter
            only_recommended: Only show recommended models
            
        Returns:
            List of ModelInfo instances
        """
        models = list(self._model_cache.values())
        
        if language:
            models = [m for m in models if m.language.lower() == language.lower()]
        
        if only_recommended:
            models = [m for m in models if m.is_recommended]
        
        return models
    
    def get_model_by_name(self, name: str) -> Optional[ModelInfo]:
        """
        Get model by name.
        
        Args:
            name: Model name
            
        Returns:
            ModelInfo or None
        """
        return self._model_cache.get(name)
    
    def is_model_installed(self, model_name: str) -> bool:
        """
        Check if a model is installed.
        
        Args:
            model_name: Model name
            
        Returns:
            True if installed
        """
        model = self._model_cache.get(model_name)
        if not model:
            return False
        return model.is_installed
    
    def download_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        complete_callback: Optional[Callable[[bool], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Download a model.
        
        Args:
            model_name: Model name to download
            progress_callback: Optional progress callback (current, total)
            complete_callback: Optional completion callback (success)
            error_callback: Optional error callback (error_message)
            
        Returns:
            True if download started
        """
        model = self._model_cache.get(model_name)
        if not model:
            error_msg = f"Model not found: {model_name}"
            logger.error(error_msg)
            if error_callback:
                error_callback(error_msg)
            return False
        
        if model.is_installed:
            logger.info(f"Model already installed: {model_name}")
            if complete_callback:
                complete_callback(True)
            return True
        
        try:
            # Convert back to dict for model manager
            model_dict = model.to_dict()
            
            # Download with progress
            success = self._model_manager.download_model(
                model_dict,
                progress_callback=progress_callback
            )
            
            if success:
                # Refresh cache to update installed status
                self._refresh_cache()
                
                if complete_callback:
                    complete_callback(True)
                
                logger.info(f"Model downloaded successfully: {model_name}")
            else:
                error_msg = f"Download failed for model: {model_name}"
                logger.error(error_msg)
                if error_callback:
                    error_callback(error_msg)
                    
                if complete_callback:
                    complete_callback(False)
            
            return success
            
        except Exception as e:
            error_msg = f"Error downloading model {model_name}: {e}"
            logger.error(error_msg)
            if error_callback:
                error_callback(error_msg)
            return False
    
    def get_model_languages(self) -> List[str]:
        """Get list of available model languages."""
        languages = set()
        for model in self._model_cache.values():
            languages.add(model.language)
        return sorted(list(languages))
    
    def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get model configuration for TTS engine.
        
        Args:
            model_name: Model name
            
        Returns:
            Model config dict or None
        """
        model = self._model_cache.get(model_name)
        if not model:
            return None
        
        if not model.is_installed:
            return None
        
        return {
            'name': model.name,
            'language': model.language,
            'model_dir': str(model.local_path),
            'extracted_dir': model.local_path.name if model.local_path else ""
        }
    
    def refresh_models(self) -> None:
        """Refresh model list from source."""
        self._refresh_cache()
        logger.info("Model cache refreshed")
    
    def get_default_model(self) -> Optional[str]:
        """Get default model name."""
        recommended = [m for m in self._model_cache.values() if m.is_recommended]
        if recommended:
            return recommended[0].name
        
        if self._model_cache:
            return list(self._model_cache.keys())[0]
        
        return None
    
    def get_model_size(self, model_name: str) -> float:
        """Get model size in MB."""
        model = self._model_cache.get(model_name)
        return model.size_mb if model else 0.0
