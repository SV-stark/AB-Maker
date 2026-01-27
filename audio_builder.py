import os
import subprocess
import logging

class AudioBuilder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _get_ffmpeg_cmd(self):
        # Assume ffmpeg is in PATH
        return "ffmpeg"

    def check_ffmpeg(self):
        """Checks if FFmpeg is available."""
        try:
            subprocess.run([self._get_ffmpeg_cmd(), "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_chapter_metadata(self, chapters, output_metadata_file):
        """
        Creates FFmpeg metadata file format:
        ;FFMETADATA1
        [CHAPTER]
        TIMEBASE=1/1000
        START=0
        END=duration_in_ms
        title=Chapter 1
        """
        try:
            with open(output_metadata_file, 'w', encoding='utf-8') as f:
                f.write(";FFMETADATA1\n")
                current_time = 0
                
                for chapter in chapters:
                    duration_ms = int(chapter['duration'] * 1000)
                    start = current_time
                    end = current_time + duration_ms
                    
                    f.write("[CHAPTER]\n")
                    f.write("TIMEBASE=1/1000\n")
                    f.write(f"START={start}\n")
                    f.write(f"END={end}\n")
                    f.write(f"title={chapter['title']}\n")
                    f.write("\n")
                    
                    current_time = end
            return True
        except Exception as e:
            self.logger.error(f"Error creating metadata: {e}")
            return False

    def merge_chapters_to_m4b(self, chapter_files, output_path, metadata_file=None):
        """
        Merges multiple audio files into a single M4B file.
        chapter_files: List of absolute paths to audio files (wav/mp3)
        metadata_file: Path to FFMETADATA1 file
        """
        try:
            # Create a concat list file
            concat_list_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for file_path in chapter_files:
                    # Escape paths for ffmpeg concat demuxer
                    # Use forward slashes for cross-platform compatibility
                    safe_path = file_path.replace('\\', '/')
                    # Escape single quotes and allow for spaces
                    safe_path = safe_path.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            cmd = [
                self._get_ffmpeg_cmd(),
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
            ]
            
            if metadata_file:
                cmd.extend(["-i", metadata_file, "-map_metadata", "1"])
            
            cmd.extend([
                "-c:a", "aac", # Encode to AAC for M4B
                "-b:a", "128k",
                "-vn", # No video
                "-y", # Overwrite
                output_path
            ])
            
            self.logger.info(f"Running ffmpeg: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Cleanup concat list
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
                
            return True
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode() if e.stderr else "Unknown error"
            self.logger.error(f"FFmpeg failed: {err_msg}")
            return False
        except Exception as e:
            self.logger.error(f"Error during merge: {e}")
            return False

    def convert_to_mp3(self, wav_path, mp3_path):
        """Converts WAV to MP3 using FFmpeg."""
        try:
            cmd = [
                self._get_ffmpeg_cmd(),
                "-y",
                "-i", wav_path,
                "-codec:a", "libmp3lame",
                "-qscale:a", "2", # VBR quality 2 (~190kbps)
                mp3_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            self.logger.error(f"Error converting to MP3: {e}")
            return False
