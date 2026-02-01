
import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.character_detector import CharacterDetector, CharacterGender

class TestCharacterDetector(unittest.TestCase):
    def setUp(self):
        self.detector = CharacterDetector()

    def test_simple_attribution(self):
        text = '"Hello," said John.'
        self.detector._analyze_text(text)
        self.assertIn('John', self.detector.characters)
        self.assertEqual(self.detector.characters['John'].gender, CharacterGender.MALE)

    def test_name_clustering(self):
        chapters = [{'content': '"Hi," said John Smith.\n"Hello," said John.'}]
        chars = self.detector.detect_characters(chapters)
        
        # Should merge John into John Smith
        self.assertIn('John Smith', chars)
        self.assertNotIn('John', chars)
        self.assertEqual(chars['John Smith'].speaking_count, 2)

    def test_pronoun_resolution(self):
        # Context: John detected -> He said
        chapters = [{'content': '"I am John," said John.\n"I agree," he said.'}]
        chars = self.detector.detect_characters(chapters)
        
        self.assertIn('John', chars)
        self.assertEqual(chars['John'].speaking_count, 2)  # John + He

    def test_stoplist(self):
        text = '"What?" The man asked.'
        self.detector._analyze_text(text)
        self.assertNotIn('The', self.detector.characters)

    def test_before_quote(self):
        text = 'Mary asked, "How are you?"'
        self.detector._analyze_text(text)
        self.assertIn('Mary', self.detector.characters)
        self.assertEqual(self.detector.characters['Mary'].gender, CharacterGender.FEMALE)

if __name__ == '__main__':
    unittest.main()
