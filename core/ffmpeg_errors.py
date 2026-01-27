"""
FFmpeg Error Parser
Converts cryptic FFmpeg errors into user-friendly messages
"""
import re
import logging

logger = logging.getLogger(__name__)

# Common FFmpeg error patterns mapped to friendly messages
FFMPEG_ERROR_PATTERNS = [
    (r"Invalid data found", "The audio file is corrupted or in an unsupported format."),
    (r"output buffer too small", "Audio file is too large. Try using a lower quality preset."),
    (r"No such file or directory", "Could not find the audio file. It may have been deleted."),
    (r"Permission denied", "Don't have permission to write to the output folder."),
    (r"Disk quota exceeded", "Out of disk space. Please free up some space and try again."),
    (r"Too many open files", "System file limit reached. Try closing other applications."),
    (r"Conversion failed", "Audio conversion failed. The file may be corrupted."),
    (r"Unable to find a suitable output format", "Unsupported output format specified."),
    (r"does not contain any stream", "The input file doesn't contain valid audio data."),
    (r"Invalid argument", "Invalid audio encoding parameters. Try different quality settings."),
    (r"Broken pipe", "FFmpeg process was interrupted. Try again."),
]

def parse_ffmpeg_error(stderr_output: str, default_message: str = "Audio processing failed") -> str:
    """
    Parse FFmpeg stderr output and return a user-friendly error message.
    
    Args:
        stderr_output: Raw stderr from FFmpeg
        default_message: Fallback message if no pattern matches
    
    Returns:
        User-friendly error message
    """
    if not stderr_output:
        return default_message
    
    # Try to match known patterns
    for pattern, friendly_msg in FFMPEG_ERROR_PATTERNS:
        if re.search(pattern, stderr_output, re.IGNORECASE):
            logger.debug(f"FFmpeg error matched pattern: {pattern}")
            return friendly_msg
    
    # If no pattern matches, try to extract meaningful error
    # Look for lines starting with common error prefixes
    for line in stderr_output.split('\n'):
        line = line.strip()
        if any(prefix in line.lower() for prefix in ['error', 'fatal', 'invalid']):
            # Remove technical details like memory addresses
            cleaned = re.sub(r'0x[0-9a-fA-F]+', '', line)
            if len(cleaned) > 20:  # Only use if it's meaningful
                return f"{default_message}: {cleaned[:200]}"
    
    return default_message

def get_friendly_ffmpeg_error(exception: Exception) -> str:
    """
    Extract friendly error message from FFmpeg exception.
    
    Args:
        exception: Exception from subprocess call
    
    Returns:
        User-friendly error message
    """
    try:
        if hasattr(exception, 'stderr') and exception.stderr:
            stderr = exception.stderr.decode('utf-8', errors='replace') if isinstance(exception.stderr, bytes) else str(exception.stderr)
            return parse_ffmpeg_error(stderr)
        return parse_ffmpeg_error(str(exception))
    except Exception as e:
        logger.warning(f"Error parsing FFmpeg exception: {e}")
        return "Audio processing failed. Check the logs for details."
