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

    def create_chapter_metadata(self, chapters, output_metadata_file, book_metadata=None):
        """
        Creates FFmpeg metadata file format with optional book metadata.
        book_metadata: dict with 'title', 'author' keys
        """
        try:
            with open(output_metadata_file, 'w', encoding='utf-8') as f:
                f.write(";FFMETADATA1\n")
                
                # Add book-level metadata
                if book_metadata:
                    if book_metadata.get('title'):
                        # Escape special characters for FFmpeg metadata
                        title = book_metadata['title'].replace('=', '\\=').replace(';', '\\;').replace('#', '\\#').replace('\n', '')
                        f.write(f"title={title}\n")
                    if book_metadata.get('author'):
                        author = book_metadata['author'].replace('=', '\\=').replace(';', '\\;').replace('#', '\\#').replace('\n', '')
                        f.write(f"artist={author}\n")
                        f.write(f"album_artist={author}\n")
                    f.write("genre=Audiobook\n")
                    f.write("\n")
                
                current_time = 0
                
                for chapter in chapters:
                    duration_ms = int(chapter['duration'] * 1000)
                    start = current_time
                    end = current_time + duration_ms
                    
                    # Escape chapter title
                    ch_title = chapter['title'].replace('=', '\\=').replace(';', '\\;').replace('#', '\\#').replace('\n', '')
                    
                    f.write("[CHAPTER]\n")
                    f.write("TIMEBASE=1/1000\n")
                    f.write(f"START={start}\n")
                    f.write(f"END={end}\n")
                    f.write(f"title={ch_title}\n")
                    f.write("\n")
                    
                    current_time = end
            return True
        except Exception as e:
            self.logger.error(f"Error creating metadata: {e}")
            return False

    def merge_chapters_to_m4b(self, chapter_files, output_path, metadata_file=None, cover_path=None):
        """
        Merges multiple audio files into a single M4B file with optional cover art.
        chapter_files: List of absolute paths to audio files (wav/mp3)
        metadata_file: Path to FFMETADATA1 file
        cover_path: Path to cover image (jpg/png)
        """
        try:
            # Create a concat list file
            concat_list_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for file_path in chapter_files:
                    # Escape paths for ffmpeg concat demuxer
                    safe_path = file_path.replace('\\', '/')
                    safe_path = safe_path.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            cmd = [
                self._get_ffmpeg_cmd(),
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
            ]
            
            # Add cover art if provided
            if cover_path and os.path.exists(cover_path):
                cmd.extend(["-i", cover_path])
            
            if metadata_file:
                cmd.extend(["-i", metadata_file, "-map_metadata", "2" if cover_path else "1"])
            
            # Map audio stream
            cmd.extend(["-map", "0:a"])
            
            # Map cover art as video stream if present
            if cover_path and os.path.exists(cover_path):
                cmd.extend([
                    "-map", "1:v",
                    "-c:v", "mjpeg",  # Use MJPEG for album art
                    "-disposition:v:0", "attached_pic"
                ])
            
            cmd.extend([
                "-c:a", "aac",  # Encode to AAC for M4B
                "-b:a", "128k",
                "-y",  # Overwrite
                output_path
            ])
            
            self.logger.info(f"Running ffmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
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

    def convert_to_mp3(self, wav_path, mp3_path, metadata=None, cover_path=None, track_num=None, total_tracks=None):
        """
        Converts WAV to MP3 using FFmpeg, then adds ID3 tags with mutagen.
        metadata: dict with 'title', 'author', 'chapter_title' keys
        cover_path: Path to cover image
        track_num: Track number for this chapter
        total_tracks: Total number of tracks
        """
        try:
            # Step 1: Convert WAV to MP3 with FFmpeg
            cmd = [
                self._get_ffmpeg_cmd(),
                "-y",
                "-i", wav_path,
                "-codec:a", "libmp3lame",
                "-qscale:a", "2",  # VBR quality 2 (~190kbps)
            ]
            
            # Embed cover art directly with FFmpeg if available
            if cover_path and os.path.exists(cover_path):
                cmd.extend([
                    "-i", cover_path,
                    "-map", "0:a",
                    "-map", "1:v",
                    "-c:v", "mjpeg",
                    "-id3v2_version", "3",
                    "-metadata:s:v", "title=Album cover",
                    "-metadata:s:v", "comment=Cover (front)"
                ])
            
            cmd.append(mp3_path)
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Step 2: Add ID3 tags using mutagen
            if metadata:
                self._add_mp3_tags(mp3_path, metadata, cover_path, track_num, total_tracks)
            
            return True
        except Exception as e:
            self.logger.error(f"Error converting to MP3: {e}")
            return False

    def _add_mp3_tags(self, mp3_path, metadata, cover_path=None, track_num=None, total_tracks=None):
        """Adds ID3 tags to MP3 file using mutagen."""
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TCON, APIC, ID3NoHeaderError
            
            # Try to load existing tags or create new
            try:
                audio = MP3(mp3_path)
                if audio.tags is None:
                    audio.add_tags()
            except ID3NoHeaderError:
                audio = MP3(mp3_path)
                audio.add_tags()
            
            tags = audio.tags
            
            # Set chapter title as track title
            if metadata.get('chapter_title'):
                tags.add(TIT2(encoding=3, text=metadata['chapter_title']))
            
            # Set author as artist
            if metadata.get('author'):
                tags.add(TPE1(encoding=3, text=metadata['author']))
            
            # Set book title as album
            if metadata.get('title'):
                tags.add(TALB(encoding=3, text=metadata['title']))
            
            # Set track number
            if track_num is not None:
                track_str = f"{track_num}/{total_tracks}" if total_tracks else str(track_num)
                tags.add(TRCK(encoding=3, text=track_str))
            
            # Set genre
            tags.add(TCON(encoding=3, text="Audiobook"))
            
            # Add cover art if available and not already added by FFmpeg
            if cover_path and os.path.exists(cover_path):
                with open(cover_path, 'rb') as f:
                    cover_data = f.read()
                
                # Determine MIME type
                mime = 'image/jpeg'
                if cover_path.lower().endswith('.png'):
                    mime = 'image/png'
                
                tags.add(APIC(
                    encoding=3,
                    mime=mime,
                    type=3,  # Front cover
                    desc='Cover',
                    data=cover_data
                ))
            
            audio.save()
            self.logger.info(f"Added ID3 tags to {os.path.basename(mp3_path)}")
            
        except ImportError:
            self.logger.warning("mutagen not installed, skipping ID3 tags")
        except Exception as e:
            self.logger.warning(f"Failed to add ID3 tags: {e}")

