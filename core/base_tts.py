"""
Abstract Base Class for TTS Engines
Defines the interface that all TTS implementations must follow
"""
from abc import ABC, abstractmethod
from typing import Optional

class BaseTTSEngine(ABC):
    """
    Abstract base class for Text-to-Speech engines.
    
    This allows AB-Maker to support multiple TTS backends
    (e.g., Sherpa-ONNX, Google TTS, AWS Polly) with a consistent interface.
    """
    
    @abstractmethod
    def initialize_model(self, config: dict) -> bool:
        """
        Initialize the TTS model with the given configuration.
        
        Args:
            config: Dictionary containing model configuration
                   (paths, provider, sample rate, etc.)
        
        Returns:
            True if initialization succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def generate_audio(self, text: str, output_path: str, **kwargs) -> bool:
        """
        Generate audio from text and save to file.
        
        Args:
            text: Text to convert to speech
            output_path: Path where audio file should be saved
            **kwargs: Additional engine-specific parameters
                     (e.g., speed, speaker_id)
        
        Returns:
            True if generation succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def get_sample_rate(self) -> Optional[int]:
        """
        Get the sample rate of the current model.
        
        Returns:
            Sample rate in Hz, or None if not available
        """
        pass
