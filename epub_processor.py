import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os

class EpubProcessor:
    def __init__(self):
        pass

    def extract_chapters(self, epub_path):
        """
        Reads an EPUB file and returns a list of dictionaries with 'title' and 'content'.
        """
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
            return chapters
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
