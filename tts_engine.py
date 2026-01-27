import sherpa_onnx
import soundfile as sf
import os
import logging

class TTSEngine:
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
                length_scale=1.0,
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
                max_num_sentences=1,
            )

            # Create TTS instance (will fail if config is invalid)
            self.tts = sherpa_onnx.OfflineTts(tts_config)
            self.sample_rate = self.tts.sample_rate
            self.logger.info(f"TTS Model initialized. Sample rate: {self.sample_rate}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS model: {e}")
            return False

    def generate_audio(self, text, output_filename, speed=1.0, sid=0):
        """
        Generates audio from text and saves it to a file.
        """
        if not self.tts:
            self.logger.error("TTS model not initialized")
            return False
            
        try:
            # Generate audio
            audio = self.tts.generate(text, sid=sid, speed=speed)
            
            # Save to file
            sf.write(
                output_filename,
                audio.samples,
                samplerate=audio.sample_rate,
                subtype='PCM_16'
            )
            return True
        except Exception as e:
            self.logger.error(f"Error generating audio: {e}")
            return False
