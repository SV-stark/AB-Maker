import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os

class EpubProcessor:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

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
                print(f"Loading chapters from cache: {cache_file}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Cache check failed: {e}")

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
                            print(f"Warning: Failed to process chapter {id_ref}: {chap_err}")
                            continue

            # 2. Save to Cache
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(chapters, f)
            except Exception as e:
                print(f"Failed to write cache: {e}")

            return chapters
            return chapters
        except KeyError:
             print("Error: EPUB keys missing. Content might be encrypted/DRM protected.")
             return []
        except Exception as e:
            print(f"Error processing EPUB: {e}")
            return []

    def clean_text(self, html_content):
        """
        Extracts raw text from HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        # Add spaces between block elements to prevent words merging
        for br in soup.find_all("br"):
            br.replace_with(" ")
        for p in soup.find_all("p"):
            p.insert_after(" ")
            
        text = soup.get_text()
        # Normalize whitespace
        return " ".join(text.split())

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
