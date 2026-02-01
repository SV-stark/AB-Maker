"""
Character Detector Service
Automatically detects characters from book text using dialogue attribution, gender hints,
and context tracking.
"""
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import collections

class CharacterGender(Enum):
    """Character gender classification."""
    UNKNOWN = "unknown"
    FEMALE = "female"
    MALE = "male"
    NARRATOR = "narrator"


@dataclass
class Character:
    """Represents a detected character."""
    name: str
    gender: CharacterGender
    speaking_count: int = 0
    voice_id: Optional[int] = None
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
            
    def to_dict(self):
        return {
            'name': self.name,
            'gender': self.gender.value,
            'speaking_count': self.speaking_count,
            'voice_id': self.voice_id,
            'aliases': self.aliases
        }


class CharacterDetector:
    """Detects characters from book text using advanced heuristics."""
    
    # Expanded female name patterns/words
    FEMALE_INDICATORS = {
        'she', 'her', 'hers', 'woman', 'girl', 'lady', 'madam', 'ms', 'mrs', 'miss',
        'mother', 'mom', 'aunt', 'sister', 'daughter', 'niece', 'grandmother', 
        'queen', 'princess', 'duchess', 'baroness', 'empress',
        'mary', 'jane', 'alice', 'emma', 'anna', 'lucy', 'grace', 'rose',
        'sarah', 'kate', 'laura', 'lisa', 'linda', 'maria', 'nancy', 'patricia',
        'jennifer', 'elizabeth', 'susan', 'margaret', 'dorothy', 'betty'
    }
    
    # Expanded male name patterns/words
    MALE_INDICATORS = {
        'he', 'his', 'him', 'man', 'boy', 'gentleman', 'sir', 'mr', 'lord',
        'father', 'dad', 'uncle', 'brother', 'son', 'nephew', 'grandfather', 
        'king', 'prince', 'duke', 'baron', 'emperor',
        'john', 'james', 'robert', 'michael', 'william', 'david', 'richard',
        'joseph', 'thomas', 'charles', 'daniel', 'matthew', 'anthony',
        'mark', 'donald', 'steven', 'paul', 'andrew', 'kenneth', 'george'
    }

    # Expanded speech verbs for detection
    SPEECH_VERBS = {
        'said', 'replied', 'asked', 'answered', 'shouted', 'whispered', 'muttered',
        'exclaimed', 'called', 'cried', 'yelled', 'responded', 'continued', 'added',
        'remarked', 'commented', 'observed', 'noted', 'stated', 'declared',
        'announced', 'proclaimed', 'commanded', 'ordered', 'demanded', 'requested',
        'begged', 'pleaded', 'promised', 'threatened', 'warned', 'advised',
        'suggested', 'insisted', 'repeated', 'echoed', 'retorted', 'inquired',
        'mused', 'thought', 'bellowed', 'screamed', 'snapped', 'murmured',
        'grumbled', 'moaned', 'complained', 'sighed', 'laughed', 'giggled',
        'sobbed', 'whimpered', 'interjected', 'interrupted',
    }

    # Stoplist of words that look like names but aren't
    STOPLIST = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'as', 'is', 'was', 'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 
        'need', 'dare', 'ought', 'used', 'rare', 'said', 'asked', 'replied',
        'then', 'there', 'here', 'now', 'later', 'soon', 'meanwhile', 'however', 
        'suddenly', 'finally', 'slowly', 'quickly', 'softly', 'loudly',
        'yes', 'no', 'oh', 'ah', 'well', 'hey', 'hello', 'hi',
        'one', 'two', 'three', 'first', 'second', 'third', 'next', 'last',
        'everyone', 'everybody', 'someone', 'somebody', 'anyone', 'anybody', 'nobody', 'noone',
        'it', 'that', 'this', 'these', 'those', 'they', 'them', 'their', 'we', 'us', 'our', 'you', 'your'
    }
    
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        # Context tracking
        self.last_male_character: Optional[str] = None
        self.last_female_character: Optional[str] = None
        self.last_speaker: Optional[str] = None
    
    def detect_characters(self, chapters: List[Dict]) -> Dict[str, Character]:
        """
        Detect characters from all chapters in the book.
        
        Args:
            chapters: List of chapter dicts with 'title' and 'content' keys
            
        Returns:
            Dictionary mapping character names to Character objects
        """
        self.characters = {}
        
        # Process all chapters
        for chapter in chapters:
            content = chapter.get('content', '')
            self._analyze_text(content)
        
        # Add narrator as default character
        if 'Narrator' not in self.characters:
            self.characters['Narrator'] = Character(
                name='Narrator',
                gender=CharacterGender.NARRATOR,
                speaking_count=0,
                voice_id=0
            )

        # Cluster similar names (e.g., "John" -> "John Smith")
        self._cluster_names()
        
        return self.characters
    
    def _analyze_text(self, text: str):
        """Analyze text to find characters and their dialogue."""
        lines = text.split('\n')
        
        for line in lines:
            if not line.strip(): continue

            # Look for quoted dialogue
            # Logic: We scan the line for quotes. For each quote, we try to find attribution.
            dialogue_matches = list(re.finditer(r'"([^"]+)"', line))
            
            # If line has no quotes, it's narration. Check for character mentions to update context.
            if not dialogue_matches:
                self._scan_narration_for_context(line)
                continue

            for i, match in enumerate(dialogue_matches):
                dialogue_text = match.group(1)
                before_quote = line[:match.start()].strip()
                after_quote = line[match.end():].strip()
                
                # Contextual Speaker Resolution
                speaker = None
                
                # 1. Try explicit attribution AFTER quote
                speaker = self._extract_speaker_after_quote(after_quote)
                
                # 2. Try explicit attribution BEFORE quote (if not found after)
                if not speaker and before_quote:
                    # Only look at the immediate preceding text if multiple quotes exist
                    # If this is the second quote in a line, 'before_quote' is the text between match i-1 and match i
                    if i > 0:
                        prev_end = dialogue_matches[i-1].end()
                        immediate_before = line[prev_end:match.start()].strip()
                        speaker = self._extract_speaker_before_quote(immediate_before)
                    else:
                        speaker = self._extract_speaker_before_quote(before_quote)

                # 3. Resolve pronouns if "He said"/"She said" detected
                if speaker and speaker.lower() in {'he', 'she', 'him', 'her'}:
                     speaker = self._resolve_pronoun(speaker)

                # 4. Implicit alternation (Experimental)
                # If no speaker found, and we have a strong conversation flow... 
                # (Skipping for now to avoid false positives, safer to default to Narrator/Unknown)
                
                if speaker:
                    self._add_character(speaker)
                    self._update_context(speaker)
                else:
                    # If dialogue exists but no speaker detected, it might be the last speaker continuing
                    # or the other person in a 2-person conversation.
                    # For safety, we classify as 'Narrator' (or implicit) but don't add a new character named "Unknown"
                    pass

    def _scan_narration_for_context(self, text: str):
        """Scan narration text to update last mentioned male/female chars."""
        # This is a simple scan for known capitalized names
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        for word in words:
            if word in self.characters and word not in self.STOPLIST:
                 self._update_context(word)

    def _update_context(self, name: str):
        """Update the tracking variables for context resolution."""
        if name not in self.characters: return
        
        self.last_speaker = name
        gender = self.characters[name].gender
        
        if gender == CharacterGender.MALE:
            self.last_male_character = name
        elif gender == CharacterGender.FEMALE:
            self.last_female_character = name

    def _resolve_pronoun(self, pronoun: str) -> Optional[str]:
        """Resolve 'he'/'she' to the last prominent character."""
        p_lower = pronoun.lower()
        if p_lower in {'he', 'him', 'his'}:
            return self.last_male_character
        if p_lower in {'she', 'her', 'hers'}:
            return self.last_female_character
        return None

    def _extract_speaker_after_quote(self, text: str) -> Optional[str]:
        """Extract speaker name from text after a closing quote."""
        # Pattern: ..." speaker said/verb ...
        # Improved regex to handle "said John Smith" or "John said"
        
        # 1. "said [Name]"
        pattern1 = r'^(?:\s*,?\s*)(?:said|replied|asked|answered|shouted|whispered|exclaimed|called|cried|muttered|yelled|responded|added|continued)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        match1 = re.search(pattern1, text)
        if match1:
            return self._validate_name(match1.group(1))

        # 2. "[Name] said"
        # We look for a name followed immediately by a verb
        verbs_pattern = '|'.join(self.SPEECH_VERBS)
        pattern2 = rf'^(?:\s*,?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:{verbs_pattern})'
        
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
             return self._validate_name(match2.group(1))

        return None
    
    def _extract_speaker_before_quote(self, text: str) -> Optional[str]:
        """Extract speaker name from text before an opening quote."""
        # Pattern: [Name] said "..." or [Name] said, "..."
        if not text: return None
        
        verbs_pattern = '|'.join(self.SPEECH_VERBS)
        
        # Look for [Name] [Verb] at the END of the text string
        pattern = rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:{verbs_pattern})\s*,?$'
        
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
             return self._validate_name(match.group(1))
        
        return None

    def _validate_name(self, name: str) -> Optional[str]:
        """Clean and validate a potential name."""
        clean_name = name.strip()
        if not clean_name: return None
        
        # Check stoplist (case-insensitive)
        if clean_name.lower() in self.STOPLIST:
            return None
            
        return clean_name.title()
    
    def _add_character(self, name: str):
        """Add or update a character."""
        name = name.strip().title()
        
        # Skip if in stoplist (double check)
        if name.lower() in self.STOPLIST: return

        # Validate Length
        if len(name) < 2: return 

        # Skip if already exists
        if name in self.characters:
            self.characters[name].speaking_count += 1
            return
        
        # Detect gender
        gender = self._detect_gender(name)
        
        self.characters[name] = Character(
            name=name,
            gender=gender,
            speaking_count=1,
            voice_id=None
        )
    
    def _detect_gender(self, name: str) -> CharacterGender:
        """Detect character gender based on name and heuristics."""
        name_lower = name.lower()
        
        # Check female indicators
        for indicator in self.FEMALE_INDICATORS:
            if re.search(rf'\b{indicator}\b', name_lower):
                return CharacterGender.FEMALE
        
        # Check male indicators
        for indicator in self.MALE_INDICATORS:
             if re.search(rf'\b{indicator}\b', name_lower):
                return CharacterGender.MALE
        
        return CharacterGender.UNKNOWN
    
    def _cluster_names(self):
        """
        Merge similar names (e.g., 'John', 'John Smith', 'Mr. Smith').
        Strategy:
        1. Sort names by length (longest to shortest).
        2. If a shorter name is a substring of a longer name, merge them into the longer one.
           (Only if gender matches or is unknown)
        """
        sorted_names = sorted(self.characters.keys(), key=len, reverse=True)
        removals = set()
        
        for i, long_name in enumerate(sorted_names):
            if long_name in removals: continue
            if long_name == 'Narrator': continue
            
            long_char = self.characters[long_name]
            long_parts = set(long_name.lower().split())

            for j in range(i + 1, len(sorted_names)):
                short_name = sorted_names[j]
                if short_name in removals: continue
                if short_name == 'Narrator': continue
                
                short_char = self.characters[short_name]
                
                # Check for gender conflict (Don't merge 'Mr. X' and 'Mrs. X')
                if long_char.gender != CharacterGender.UNKNOWN and \
                   short_char.gender != CharacterGender.UNKNOWN and \
                   long_char.gender != short_char.gender:
                    continue

                # Check if parts match (e.g. "John" in "John Smith")
                # We require the short name to be a full token match within the long name
                short_parts = set(short_name.lower().split())
                
                if short_parts.issubset(long_parts):
                     # MERGE!
                     # Add counts to long char
                     long_char.speaking_count += short_char.speaking_count
                     long_char.aliases.append(short_name)
                     
                     # Mark for removal
                     removals.add(short_name)
        
        # Remove merged characters
        for name in removals:
            del self.characters[name]

    def auto_assign_voices(self, num_available_voices: int) -> Dict[str, int]:
        """
        Automatically assign voice IDs to characters.
        
        Strategy:
        - Narrator gets voice 0 (usually the best quality)
        - Female characters get voices 1-N
        - Male characters get voices N-M
        - Unknown/other cycle through remaining
        
        Args:
            num_available_voices: Total number of speaker IDs available in the model
            
        Returns:
            Dictionary mapping character names to voice IDs
        """
        voice_assignments = {}
        
        if not self.characters:
            return voice_assignments
        
        # Ensure we have at least 1 voice
        num_available_voices = max(1, num_available_voices)
        
        # Group characters by gender
        narrators = []
        females = []
        males = []
        unknowns = []
        
        for name, char in self.characters.items():
            if char.gender == CharacterGender.NARRATOR:
                narrators.append(name)
            elif char.gender == CharacterGender.FEMALE:
                females.append(name)
            elif char.gender == CharacterGender.MALE:
                males.append(name)
            else:
                unknowns.append(name)
                
        # Sort by speaking count (assign voices to most frequent speakers first)
        females.sort(key=lambda n: self.characters[n].speaking_count, reverse=True)
        males.sort(key=lambda n: self.characters[n].speaking_count, reverse=True)
        unknowns.sort(key=lambda n: self.characters[n].speaking_count, reverse=True)
        
        # Assign voices
        current_voice = 0
        
        # Narrator gets voice 0
        for name in narrators:
            voice_assignments[name] = 0
            self.characters[name].voice_id = 0
        
        # If no narrator, voice 0 is available for others
        if not narrators:
            current_voice = 0
        else:
            current_voice = 1
        
        # Distribute remaining voices
        # Using a round-robin strategy with reservations
        
        # Calculate pool size
        pool_size = max(1, num_available_voices - current_voice)
        
        if pool_size >= 2:
            # We have enough voices to split roughly by gender
            # Split pool: 40% female, 40% male, 20% unknown (approx)
            # Actually, just interleaving is often better to ensure variety
            pass
            
        # Distribute to females
        for i, name in enumerate(females):
            voice_id = current_voice + (i % pool_size)
            voice_id = min(voice_id, num_available_voices - 1)
            voice_assignments[name] = voice_id
            self.characters[name].voice_id = voice_id
            
        # Distribute to males (offset to avoid overlap if possible)
        offset = len(females) % pool_size
        for i, name in enumerate(males):
            voice_id = current_voice + ((i + offset) % pool_size)
            voice_id = min(voice_id, num_available_voices - 1)
            voice_assignments[name] = voice_id
            self.characters[name].voice_id = voice_id
            
        # Distribute to unknowns
        offset = (len(females) + len(males)) % pool_size
        for i, name in enumerate(unknowns):
            voice_id = current_voice + ((i + offset) % pool_size)
            voice_id = min(voice_id, num_available_voices - 1)
            voice_assignments[name] = voice_id
            self.characters[name].voice_id = voice_id
        
        return voice_assignments
    
    def get_character_list(self) -> List[Character]:
        """Get list of all detected characters."""
        return list(self.characters.values())
    
    def set_character_voice(self, character_name: str, voice_id: int):
        """Manually set a character's voice ID."""
        if character_name in self.characters:
            self.characters[character_name].voice_id = voice_id
