"""
Character Voice Assignment Dialog
Configure voice assignments for different characters in the book
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CharacterVoiceDialog(ctk.CTkToplevel):
    """Dialog for assigning voices to characters."""
    
    def __init__(self, parent, chapters, model_info, icons, on_save_callback=None):
        super().__init__(parent)
        self.title("Character Voice Assignment")
        self.geometry("650x550")
        self.transient(parent)
        self.grab_set()
        
        self.chapters = chapters
        self.model_info = model_info
        self.icons = icons or {}
        self.on_save = on_save_callback
        
        # Get number of available voices from model
        self.num_voices = model_info.get('num_speakers', 1)
        
        # Character data
        self.characters: Dict[str, dict] = {}
        self.character_widgets = []
        
        # Detect characters
        self._detect_characters()
        
        self._create_ui()
        
    def _detect_characters(self):
        """Detect characters from chapters."""
        try:
            from services.character_detector import CharacterDetector, CharacterGender
            
            detector = CharacterDetector()
            detected = detector.detect_characters(self.chapters)
            
            # Convert to our format
            for name, char in detected.items():
                self.characters[name] = {
                    'name': name,
                    'gender': char.gender.value,
                    'speaking_count': char.speaking_count,
                    'voice_id': char.voice_id if char.voice_id is not None else 0
                }
            
            # If no characters detected, at least add Narrator
            if not self.characters:
                self.characters['Narrator'] = {
                    'name': 'Narrator',
                    'gender': 'narrator',
                    'speaking_count': 0,
                    'voice_id': 0
                }
                
        except Exception as e:
            logger.error(f"Error detecting characters: {e}")
            # Fallback to just narrator
            self.characters = {
                'Narrator': {
                    'name': 'Narrator',
                    'gender': 'narrator',
                    'speaking_count': 0,
                    'voice_id': 0
                }
            }
    
    def _create_ui(self):
        """Create the dialog UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            header,
            text="Character Voice Assignment",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        
        # Model info
        model_name = self.model_info.get('name', 'Unknown Model')
        voices_text = f"{self.num_voices} voice{'s' if self.num_voices > 1 else ''} available"
        ctk.CTkLabel(
            header,
            text=f"Model: {model_name} | {voices_text}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        # Info message
        if self.num_voices > 1:
            info_text = (f"✓ This model supports {self.num_voices} different voices. "
                        "Assign different voices to characters for a more immersive experience.")
        else:
            info_text = ("⚠ This model only supports 1 voice. "
                        "Multi-voice assignment is not available for this model.")
        
        info_frame = ctk.CTkFrame(self, fg_color=("gray95", "gray20"))
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            wraplength=600,
            justify="left"
        ).pack(padx=10, pady=10)
        
        # Controls
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=5)
        
        if self.num_voices > 1:
            ctk.CTkButton(
                controls,
                text="Auto-Assign Voices",
                command=self._auto_assign,
                width=130
            ).pack(side="left", padx=5)
            
            ctk.CTkLabel(
                controls,
                text="🎲 Automatically distributes voices across characters",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(side="left", padx=10)
        
        # Column headers
        headers = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        headers.pack(fill="x", padx=20, pady=(10, 0))
        
        ctk.CTkLabel(headers, text="Character", width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(headers, text="Gender", width=80, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Dialogue Lines", width=100, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Voice ID", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        # Scrollable character list
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        self._populate_characters()
        
        # Actions
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            actions,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            text_color="gray",
            width=80
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            actions,
            text="Save Assignments",
            command=self._save,
            width=130
        ).pack(side="right", padx=5)
    
    def _populate_characters(self):
        """Populate the character list."""
        self.character_widgets = []
        
        for name, char_data in sorted(self.characters.items(), 
                                      key=lambda x: (x[1]['gender'] != 'narrator', -x[1]['speaking_count'])):
            row = ctk.CTkFrame(self.scroll, fg_color=("gray95", "gray20"))
            row.pack(fill="x", pady=2, padx=2)
            
            # Character name
            name_label = ctk.CTkLabel(row, text=name, width=150, anchor="w")
            name_label.pack(side="left", padx=10, pady=5)
            
            # Gender
            gender = char_data.get('gender', 'unknown')
            gender_emoji = {'female': '👩', 'male': '👨', 'narrator': '📖', 'unknown': '❓'}.get(gender, '❓')
            gender_label = ctk.CTkLabel(row, text=f"{gender_emoji} {gender.title()}", width=80)
            gender_label.pack(side="left", padx=5)
            
            # Speaking count
            count = char_data.get('speaking_count', 0)
            count_text = f"{count} line{'s' if count != 1 else ''}" if count > 0 else "-"
            count_label = ctk.CTkLabel(row, text=count_text, width=100, text_color="gray")
            count_label.pack(side="left", padx=5)
            
            # Voice ID selector
            voice_var = ctk.StringVar(value=str(char_data.get('voice_id', 0)))
            
            if self.num_voices > 1:
                voice_menu = ctk.CTkOptionMenu(
                    row,
                    variable=voice_var,
                    values=[str(i) for i in range(self.num_voices)],
                    width=80,
                    command=lambda val, n=name: self._on_voice_change(n, int(val))
                )
            else:
                voice_menu = ctk.CTkOptionMenu(
                    row,
                    variable=voice_var,
                    values=["0"],
                    width=80,
                    state="disabled"
                )
            
            voice_menu.pack(side="left", padx=10)
            
            self.character_widgets.append({
                'name': name,
                'voice_var': voice_var,
                'widget': voice_menu
            })
    
    def _on_voice_change(self, character_name: str, voice_id: int):
        """Handle voice change for a character."""
        if character_name in self.characters:
            self.characters[character_name]['voice_id'] = voice_id
            logger.debug(f"Assigned voice {voice_id} to {character_name}")
    
    def _auto_assign(self):
        """Auto-assign voices to characters."""
        try:
            from services.character_detector import CharacterDetector
            
            detector = CharacterDetector()
            
            # Load characters into detector
            for name, char_data in self.characters.items():
                from services.character_detector import Character, CharacterGender
                char = Character(
                    name=name,
                    gender=CharacterGender(char_data['gender']),
                    speaking_count=char_data['speaking_count'],
                    voice_id=char_data.get('voice_id')
                )
                detector.characters[name] = char
            
            # Auto-assign
            assignments = detector.auto_assign_voices(self.num_voices)
            
            # Update UI
            for widget_data in self.character_widgets:
                name = widget_data['name']
                voice_var = widget_data['voice_var']
                if name in assignments:
                    voice_var.set(str(assignments[name]))
                    self.characters[name]['voice_id'] = assignments[name]
            
            messagebox.showinfo("Success", 
                              f"Voices auto-assigned!\n"
                              f"Narrator: Voice 0\n"
                              f"{len(assignments) - 1} characters distributed across voices 1-{self.num_voices-1}")
            
        except Exception as e:
            logger.error(f"Error auto-assigning voices: {e}")
            messagebox.showerror("Error", f"Failed to auto-assign voices: {e}")
    
    def _save(self):
        """Save character voice assignments."""
        try:
            # Build result
            result = {}
            for name, char_data in self.characters.items():
                result[name] = char_data.get('voice_id', 0)
            
            # Call callback if provided
            if self.on_save:
                self.on_save(result)
            
            messagebox.showinfo("Success", f"Voice assignments saved for {len(result)} characters!")
            self.destroy()
            
        except Exception as e:
            logger.error(f"Error saving voice assignments: {e}")
            messagebox.showerror("Error", f"Failed to save: {e}")
    
    def get_assignments(self) -> Dict[str, int]:
        """Get current voice assignments."""
        return {name: data.get('voice_id', 0) for name, data in self.characters.items()}
