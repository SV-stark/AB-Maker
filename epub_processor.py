import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import logging

class EpubProcessor:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def extract_metadata(self, epub_path):
        """
        Extracts book metadata including title, author, and cover image.
        Returns a dict: {'title': str, 'author': str, 'cover_path': str or None}
        """
        metadata = {
            'title': os.path.splitext(os.path.basename(epub_path))[0],
            'author': 'Unknown Author',
            'cover_path': None,
            'cover_data': None
        }
        
        try:
            book = epub.read_epub(epub_path)
            
            # Extract title
            title = book.get_metadata('DC', 'title')
            if title and title[0]:
                metadata['title'] = title[0][0]
            
            # Extract author
            creator = book.get_metadata('DC', 'creator')
            if creator and creator[0]:
                metadata['author'] = creator[0][0]
            
            # Extract cover image
            cover_item = None
            
            # Method 1: Check for cover-image in metadata
            for item in book.get_items():
                # Check if item has cover property
                if item.get_type() == ebooklib.ITEM_COVER:
                    cover_item = item
                    break
                # Check common cover naming patterns
                item_name = item.get_name().lower()
                if 'cover' in item_name and item.get_type() == ebooklib.ITEM_IMAGE:
                    cover_item = item
                    break
            
            # Method 2: Look for cover in manifest by ID
            if not cover_item:
                for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                    if 'cover' in item.id.lower():
                        cover_item = item
                        break
            
            if cover_item:
                # Save cover to cache
                cover_ext = os.path.splitext(cover_item.get_name())[1] or '.jpg'
                import hashlib
                file_hash = hashlib.md5(epub_path.encode()).hexdigest()[:8]
                cover_filename = f"cover_{file_hash}{cover_ext}"
                cover_path = os.path.join(self.cache_dir, cover_filename)
                
                with open(cover_path, 'wb') as f:
                    f.write(cover_item.get_content())
                
                metadata['cover_path'] = cover_path
                metadata['cover_data'] = cover_item.get_content()
                self.logger.info(f"Extracted cover: {cover_path}")
            
        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {e}")
        
        return metadata

    def extract_chapters(self, epub_path):
        """
        Reads an EPUB file and returns a list of dictionaries with 'title' and 'content'.
        Uses disk caching to speed up subsequent loads.
        """
        # 1. Check Cache
        import hashlib
        import json
        
        try:
            # Create a unique hash for the file based on path and mod time
            mod_time = os.path.getmtime(epub_path)
            file_hash = hashlib.md5(f"{epub_path}_{mod_time}".encode()).hexdigest()
            cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
            
            if os.path.exists(cache_file):
                self.logger.info(f"Loading chapters from cache: {cache_file}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Cache check failed: {e}")

        try:
            book = epub.read_epub(epub_path)
            chapters = []
            
            # Iterate through the spine to get chapters in order
            for item in book.spine:
                id_ref = item[0]
                item_obj = book.get_item_with_id(id_ref)
                
                if item_obj:
                    # Some items in spine might not be text documents
                    if item_obj.get_type() == ebooklib.ITEM_DOCUMENT:
                        try:
                            content = item_obj.get_content()
                            text = self.clean_text(content)
                            
                            # Only add if there is meaningful text
                            if text.strip():
                                # Try to find a title from the content or use a default
                                title = self.extract_title(content) or f"Chapter {len(chapters) + 1}"
                                chapters.append({
                                    'title': title,
                                    'content': text
                                })
                        except Exception as chap_err:
                            self.logger.warning(f"Failed to process chapter {id_ref}: {chap_err}")
                            continue

            # 2. Save to Cache
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(chapters, f)
            except Exception as e:
                self.logger.warning(f"Failed to write cache: {e}")

            return chapters
        except KeyError:
             self.logger.error("EPUB keys missing. Content might be encrypted/DRM protected.")
             return []
        except Exception as e:
            self.logger.error(f"Error processing EPUB: {e}")
            return []

    def clean_text(self, html_content):
        """
        Extracts raw text from HTML content, ensuring proper pauses for TTS.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Add pauses for line breaks - semicolon gives a better pause than a comma
        for br in soup.find_all("br"):
            br.replace_with("; ")
            
        # Ensure block elements end with punctuation to prevent run-on sentences
        block_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'blockquote']
        for tag_name in block_tags:
            for tag in soup.find_all(tag_name):
                # Check if tag has text and ends with punctuation
                tag_text = tag.get_text()
                if tag_text and tag_text.strip():
                    last_char = tag_text.strip()[-1]
                    if last_char not in ".,!?;:":
                        # For headers, add a stronger pause
                        if tag_name.startswith('h'):
                            tag.append("... ")
                        else:
                            # For normal blocks, a period is sufficient
                            tag.append(". ")
                
                # Add paragraph spacing after the block
                tag.insert_after("\n\n")
            
        text = soup.get_text()
        
        # Smart Text Processing
        import re
        
        # Replace common abbreviations
        abbreviations = {
            r"\bMr\.": "Mister",
            r"\bMrs\.": "Missus",
            r"\bDr\.": "Doctor",
            r"\bProf\.": "Professor",
            r"\bMs\.": "Miss",
            r"\bSt\.": "Saint", 
            r"\bvs\.": "versus",
            r"\bchap\.": "Chapter",
            r"\bfig\.": "Figure",
            r"\bvol\.": "Volume",
            r"\bed\.": "Edition"
        }
        
        for pattern, replacement in abbreviations.items():
             text = re.sub(pattern, replacement, text)
        
        # Handle ellipses to ensure they are spoken correctly with a pause
        text = text.replace("...", " ... ")
        
        # Normalize whitespace while preserving double newlines for paragraphs
        lines = []
        for p in text.split("\n\n"):
            p_clean = " ".join(p.split())
            if p_clean:
                lines.append(p_clean)
        
        return "\n\n".join(lines)

    def extract_title(self, html_content):
        """
        Attempts to extract a title from the HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        # Try h1, h2, etc.
        for tag in ['h1', 'h2', 'h3', 'title']:
            found = soup.find(tag)
            if found:
                return found.get_text().strip()
        return None

    def save_chapters(self, epub_path, chapters):
        """
        Saves the edited chapters back to the cache.
        """
        import hashlib
        import json
        
        try:
            mod_time = os.path.getmtime(epub_path)
            file_hash = hashlib.md5(f"{epub_path}_{mod_time}".encode()).hexdigest()
            cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(chapters, f)
            self.logger.info(f"Saved chapters to cache: {cache_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save chapters: {e}")
            return False
