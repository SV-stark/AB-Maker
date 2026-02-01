import sherpa_onnx
import soundfile as sf
import os
import logging
from core.base_tts import BaseTTSEngine

class TTSEngine(BaseTTSEngine):
    def __init__(self):
        self.tts = None
        self.sample_rate = 22050 # Default, will update from model
        self.logger = logging.getLogger(__name__)

    def initialize_model(self, model_config):
        """
        Initializes the sherpa-onnx offline TTS model.
        model_config: dict containing paths to model, tokens, etc.
        """
        try:
            # Helper to safely join paths if they are relative
            model_dir = model_config.get("model_dir", "")
            provider = model_config.get("provider", "cpu")
            
            # Check for espeak-ng-data folder
            data_dir_path = os.path.join(model_dir, "espeak-ng-data")
            if not os.path.exists(data_dir_path):
                data_dir_path = ""  # Fall back to empty if not present
            
            vits_config = sherpa_onnx.OfflineTtsVitsModelConfig(
                model=os.path.join(model_dir, model_config["model_file"]),
                lexicon="",
                tokens=os.path.join(model_dir, model_config["tokens_file"]),
                data_dir=data_dir_path,
                noise_scale=0.667,
                noise_scale_w=0.8,
                length_scale=1.3, # Increased from 1.2 for even more deliberate, professional narration pacing
            )
            
            # Configure model with provider (cpu/cuda)
            model_config_args = {
                "vits": vits_config,
                "num_threads": 1,
                "debug": 0,
                "provider": provider
            }
            
            tts_config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(**model_config_args),
                rule_fsts="",
                max_num_sentences=10, # Increased from 1 to allow better sentence transition
            )

            # Create TTS instance
            try:
                self.tts = sherpa_onnx.OfflineTts(tts_config)
            except Exception as e:
                if provider == "cuda":
                    self.logger.warning(f"Failed to initialize with CUDA: {e}. Falling back to CPU...")
                    self.logger.warning(f"Failed to initialize with CUDA: {e}. Falling back to CPU...")
                    # Fallback to CPU - Recreate config cleanly
                    model_config_args["provider"] = "cpu"
                    
                    # Rebuild the nested config
                    tts_config = sherpa_onnx.OfflineTtsConfig(
                        model=sherpa_onnx.OfflineTtsModelConfig(**model_config_args),
                        rule_fsts="",
                        max_num_sentences=10,
                    )
                    self.tts = sherpa_onnx.OfflineTts(tts_config)
                else:
                    raise e

            self.sample_rate = self.tts.sample_rate
            self.logger.info(f"TTS Model initialized. Sample rate: {self.sample_rate}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS model: {e}")
            return False

    def generate_audio(self, text, output_filename, speed=1.0, sid=0, 
                       sentence_pause_ms=700, clause_pause_ms=250, 
                       paragraph_pause_ms=1500, dialogue_pause_ms=400,
                       character_voices=None):
        """
        Generates audio from text and saves it to a file.
        
        Supports multi-voice generation for different characters when
        character_voices mapping is provided.
        
        Uses a hierarchical pause structure for natural pacing:
        - Clause pause (commas, etc.) - 250ms
        - Dialogue pause (quote to attribution) - 400ms
        - Sentence pause (end of sentences) - 700ms
        - Paragraph pause (between paragraphs) - 1500ms
        
        Args:
            text: Text to convert to speech
            output_filename: Output audio file path
            speed: Speech speed multiplier
            sid: Default speaker ID (voice)
            sentence_pause_ms: Pause duration after sentences (ms)
            clause_pause_ms: Pause duration after clauses (ms)
            paragraph_pause_ms: Pause duration between paragraphs (ms)
            dialogue_pause_ms: Pause duration after dialogue (ms)
            character_voices: Optional dict mapping character names to voice IDs
        """
        if not self.tts:
            self.logger.error("TTS model not initialized")
            return False
        
        # If character voices provided, use multi-voice generation
        if character_voices and len(character_voices) > 1:
            return self._generate_multi_voice(
                text, output_filename, speed, sid,
                sentence_pause_ms, clause_pause_ms, 
                paragraph_pause_ms, dialogue_pause_ms,
                character_voices
            )
        
        # Otherwise use single-voice generation (original implementation)
        return self._generate_single_voice(
            text, output_filename, speed, sid,
            sentence_pause_ms, clause_pause_ms, 
            paragraph_pause_ms, dialogue_pause_ms
        )
    
    def _generate_single_voice(self, text, output_filename, speed, sid,
                                sentence_pause_ms, clause_pause_ms, 
                                paragraph_pause_ms, dialogue_pause_ms):
        """Original single-voice audio generation."""
        try:
            import numpy as np
            
            # 1. Split text into paragraphs (separated by \n\n)
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            
            if not paragraphs:
                self.logger.warning("No text found to generate")
                return False
            
            # Generate silence samples
            paragraph_silence = np.zeros(int(self.sample_rate * paragraph_pause_ms / 1000), dtype=np.float32)
            sentence_silence = np.zeros(int(self.sample_rate * sentence_pause_ms / 1000), dtype=np.float32)
            clause_silence = np.zeros(int(self.sample_rate * clause_pause_ms / 1000), dtype=np.float32)
            dialogue_silence = np.zeros(int(self.sample_rate * dialogue_pause_ms / 1000), dtype=np.float32)
            
            all_samples = []
            
            for p_idx, paragraph in enumerate(paragraphs):
                # 2. Split paragraph into sentences
                sentences = self._split_into_sentences(paragraph)
                
                for s_idx, sentence in enumerate(sentences):
                    # 3. Split sentence into clauses and detect dialogue transitions
                    clauses_info = self._split_into_clauses_with_info(sentence)
                    
                    for c_idx, info in enumerate(clauses_info):
                        clause = info['text'].strip()
                        if not clause: continue
                            
                        try:
                            audio = self.tts.generate(clause, sid=sid, speed=speed)
                            if audio.samples:
                                all_samples.append(np.array(audio.samples, dtype=np.float32))
                                
                                # Apply the correct pause type
                                if c_idx < len(clauses_info) - 1:
                                    if info.get('is_dialogue_break'):
                                        all_samples.append(dialogue_silence)
                                    else:
                                        all_samples.append(clause_silence)
                        except Exception as e:
                            self.logger.warning(f"Failed to generate audio for clause: {clause[:30]}... Error: {e}")
                            continue
                    
                    # Sentence Pause
                    if s_idx < len(sentences) - 1:
                        all_samples.append(sentence_silence)
                
                # Paragraph Pause
                if p_idx < len(paragraphs) - 1:
                    all_samples.append(paragraph_silence)
            
            if not all_samples:
                self.logger.error("No audio samples generated")
                return False
            
            # Concatenate all audio samples
            final_audio = np.concatenate(all_samples)
            
            # Save to file
            sf.write(
                output_filename,
                final_audio,
                samplerate=self.sample_rate,
                subtype='PCM_16'
            )
            
            self.logger.debug(f"Generated {len(paragraphs)} paragraphs, total samples: {len(final_audio)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating audio: {e}")
            return False
    
    def _generate_multi_voice(self, text, output_filename, speed, sid,
                               sentence_pause_ms, clause_pause_ms, 
                               paragraph_pause_ms, dialogue_pause_ms,
                               character_voices):
        """
        Multi-voice audio generation with character voice mapping.
        
        Strategy:
        - Narrator voice (sid) for non-dialogue text
        - Character-specific voices for quoted dialogue
        """
        try:
            import re
            import numpy as np
            
            # Get narrator voice (default sid)
            narrator_voice = sid
            
            # Generate silence samples
            paragraph_silence = np.zeros(int(self.sample_rate * paragraph_pause_ms / 1000), dtype=np.float32)
            sentence_silence = np.zeros(int(self.sample_rate * sentence_pause_ms / 1000), dtype=np.float32)
            clause_silence = np.zeros(int(self.sample_rate * clause_pause_ms / 1000), dtype=np.float32)
            dialogue_silence = np.zeros(int(self.sample_rate * dialogue_pause_ms / 1000), dtype=np.float32)
            
            all_samples = []
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            
            if not paragraphs:
                self.logger.warning("No text found to generate")
                return False
            
            for p_idx, paragraph in enumerate(paragraphs):
                # Split into dialogue and non-dialogue segments
                segments = self._split_by_dialogue(paragraph, character_voices)
                
                for seg_idx, segment in enumerate(segments):
                    seg_text = segment['text'].strip()
                    seg_voice = segment['voice_id']
                    
                    if not seg_text:
                        continue
                    
                    # Process this segment with its assigned voice
                    sentences = self._split_into_sentences(seg_text)
                    
                    for s_idx, sentence in enumerate(sentences):
                        clauses_info = self._split_into_clauses_with_info(sentence)
                        
                        for c_idx, info in enumerate(clauses_info):
                            clause = info['text'].strip()
                            if not clause:
                                continue
                            
                            try:
                                audio = self.tts.generate(clause, sid=seg_voice, speed=speed)
                                if audio.samples:
                                    all_samples.append(np.array(audio.samples, dtype=np.float32))
                                    
                                    # Apply pauses within this speaker's segment
                                    if c_idx < len(clauses_info) - 1:
                                        if info.get('is_dialogue_break'):
                                            all_samples.append(dialogue_silence)
                                        else:
                                            all_samples.append(clause_silence)
                            except Exception as e:
                                self.logger.warning(f"Failed to generate audio for clause: {clause[:30]}... Error: {e}")
                                continue
                        
                        # Sentence pause
                        if s_idx < len(sentences) - 1:
                            all_samples.append(sentence_silence)
                    
                    # Small pause between segments (speaker changes)
                    if seg_idx < len(segments) - 1:
                        # Use dialogue pause for speaker transitions
                        all_samples.append(dialogue_silence)
                
                # Paragraph Pause
                if p_idx < len(paragraphs) - 1:
                    all_samples.append(paragraph_silence)
            
            if not all_samples:
                self.logger.error("No audio samples generated")
                return False
            
            # Concatenate all audio samples
            final_audio = np.concatenate(all_samples)
            
            # Save to file
            sf.write(
                output_filename,
                final_audio,
                samplerate=self.sample_rate,
                subtype='PCM_16'
            )
            
            self.logger.debug(f"Generated multi-voice audio: {len(paragraphs)} paragraphs, total samples: {len(final_audio)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating multi-voice audio: {e}")
            return False
    
    def _split_by_dialogue(self, text, character_voices):
        """
        Split text into segments by dialogue attribution.
        
        Returns list of dicts: [{'text': str, 'voice_id': int, 'character': str or None}]
        """
        import re
        
        segments = []
        narrator_voice = character_voices.get('Narrator', 0)
        
        # Pattern to find dialogue: "quoted text" [attribution]
        # This is a simplified approach - finds quoted sections
        dialogue_pattern = r'"([^"]+)"'
        
        last_end = 0
        
        for match in re.finditer(dialogue_pattern, text):
            # Text before dialogue (narration)
            if match.start() > last_end:
                narr_text = text[last_end:match.start()]
                if narr_text.strip():
                    segments.append({
                        'text': narr_text,
                        'voice_id': narrator_voice,
                        'character': 'Narrator'
                    })
            
            # The dialogue itself
            dialogue_text = match.group(1)
            
            # Try to determine speaker from attribution after dialogue
            after_dialogue = text[match.end():match.end() + 100]
            speaker = self._extract_speaker_from_attribution(after_dialogue)
            
            if speaker and speaker in character_voices:
                voice_id = character_voices[speaker]
            else:
                voice_id = narrator_voice
                speaker = 'Narrator'
            
            segments.append({
                'text': f'"{dialogue_text}"',
                'voice_id': voice_id,
                'character': speaker
            })
            
            last_end = match.end()
        
        # Add remaining text (narration)
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining.strip():
                segments.append({
                    'text': remaining,
                    'voice_id': narrator_voice,
                    'character': 'Narrator'
                })
        
        # If no dialogue found, return whole text as single narration segment
        if not segments:
            segments.append({
                'text': text,
                'voice_id': narrator_voice,
                'character': 'Narrator'
            })
        
        return segments
    
    def _extract_speaker_from_attribution(self, text):
        """Extract speaker name from dialogue attribution text."""
        import re
        
        # Common patterns: " said John", " replied Mary", ", Bob shouted"
        patterns = [
            r'(?:\s*,?\s*)(?:\w+\s+)*(\w+)(?:\s+(?:said|replied|asked|answered|shouted|whispered|muttered|exclaimed|called|cried|yelled|responded|continued|added|remarked|commented|observed|noted|stated|declared|announced|proclaimed|commanded|ordered|demanded|requested|begged|pleaded|promised|threatened|warned|advised|suggested|insisted|repeated|echoed))',
            r'(?:,\s*)(\w+)(?:\s*,)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Filter out common non-name words
                if name.lower() not in {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'was', 'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'rare', 'said', 'he', 'she', 'they', 'it', 'i', 'you', 'we'}:
                    return name.title()
        
        return None
    
    def _split_into_sentences(self, text):
        """
        Split text into sentences using regex.
        Handles common abbreviations and edge cases.
        """
        import re
        
        # Pattern to split on sentence-ending punctuation followed by space or end
        # This handles: . ! ? ... and combinations like "?!" or "!?"
        # We use a lookahead to keep the punctuation with the sentence
        
        # First, protect common abbreviations that shouldn't cause splits
        # (Note: epub_processor already expands these, but just in case)
        protected = text
        
        # Split on sentence boundaries
        # Match: period/exclamation/question (possibly repeated) followed by space or end
        # But NOT if preceded by common abbreviations
        pattern = r'(?<=[.!?])\s+(?=[A-Z"\'])'
        
        sentences = re.split(pattern, protected)
        
        # Also split on ellipsis followed by capital letter
        result = []
        for s in sentences:
            # Split further on ... followed by capital
            sub_sentences = re.split(r'(?<=\.\.\.)\s+(?=[A-Z])', s)
            result.extend(sub_sentences)
        
        # Filter out empty strings and very short fragments
        result = [s.strip() for s in result if s.strip() and len(s.strip()) > 2]
        
        return result
    
    def _split_into_clauses_with_info(self, sentence):
        """
        Split a sentence into clauses and detect if a break is a dialogue attribution.
        Returns a list of dicts: [{'text': str, 'is_dialogue_break': bool}]
        """
        import re
        
        # Find all split points
        splits = []
        
        # 1. Standard clause breaks
        for m in re.finditer(r'(?<=[,;:\u2014—])\s+(?=\S)', sentence):
            splits.append((m.start(), m.end(), False))
            
        # 2. Dialogue attribution breaks (quote followed by lowercase)
        for m in re.finditer(r'(?<=[?"\'])\s+(?=[a-z])', sentence):
            splits.append((m.start(), m.end(), True))
            
        splits.sort()
        
        results = []
        last_pos = 0
        for start, end, is_dialogue in splits:
            chunk = sentence[last_pos:start].strip()
            if chunk:
                # We associate the break type with the clause that PRECEDES it
                results.append({
                    'text': chunk,
                    'is_dialogue_break': is_dialogue
                })
            last_pos = end
            
        final_chunk = sentence[last_pos:].strip()
        if final_chunk:
            results.append({
                'text': final_chunk,
                'is_dialogue_break': False
            })
            
        return results
    
    def get_sample_rate(self):
        """Get the sample rate of the current model."""
        return self.sample_rate if self.tts else None

