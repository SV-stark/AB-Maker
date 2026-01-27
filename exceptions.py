class ABMakerError(Exception):
    """Base exception for AB-Maker application."""
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

class ModelDownloadError(ABMakerError):
    """Raised when model download fails."""
    pass

class TTSGenError(ABMakerError):
    """Raised when TTS generation fails."""
    pass

class FFmpegError(ABMakerError):
    """Raised when FFmpeg operations fail."""
    pass

class ConfigurationError(ABMakerError):
    """Raised when there is a configuration issue."""
    pass
