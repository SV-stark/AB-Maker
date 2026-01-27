import flet as ft
import os
import threading
import time
import logging
from model_manager import ModelManager
from epub_processor import EpubProcessor
from tts_engine import TTSEngine
from audio_builder import AudioBuilder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(page: ft.Page):
    page.title = "AB-Maker: Audiobook Creator"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 700
    page.padding = 20

    # Initialize modules
    model_manager = ModelManager()
    epub_processor = EpubProcessor()
    tts_engine = TTSEngine()
    audio_builder = AudioBuilder()

    # State variables
    selected_file_path = ft.Ref[ft.Text]()
    conversion_progress = ft.Ref[ft.ProgressBar]()
    log_view = ft.Ref[ft.ListView]()
    start_btn = ft.Ref[ft.ElevatedButton]()
    model_dropdown = ft.Ref[ft.Dropdown]()
    output_format_radio = ft.Ref[ft.RadioGroup]()
    
    current_epub_path = None
    
    def log(message):
        if log_view.current:
            log_view.current.controls.append(ft.Text(message, size=12, font_family="Consolas"))
            log_view.current.update()
            page.update()

    def load_models():
        models = model_manager.list_available_models()
        options = []
        for m in models:
            installed = model_manager.is_model_installed(m)
            status = "(Installed)" if installed else "(Not Installed)"
            options.append(ft.dropdown.Option(
                key=m['name'],
                text=f"{m['name']} {status}",
                data=m
            ))
        model_dropdown.current.options = options
        if options:
            model_dropdown.current.value = options[0].key
        model_dropdown.current.update()

    def on_model_change(e):
        # Check if selected model is installed, if not, prompt or auto download
        pass

    def pick_file_result(e: ft.FilePickerResultEvent):
        nonlocal current_epub_path
        if e.files:
            path = e.files[0].path
            current_epub_path = path
            selected_file_path.current.value = path
            selected_file_path.current.update()
            log(f"Selected file: {path}")

    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)

    def run_conversion():
        try:
            if not current_epub_path:
                log("Error: No EPUB file selected.")
                return

            model_key = model_dropdown.current.value
            model_info = next((opt.data for opt in model_dropdown.current.options if opt.key == model_key), None)
            
            if not model_info:
                log("Error: No model selected.")
                return

            # Disable UI
            start_btn.current.disabled = True
            start_btn.current.update()
            conversion_progress.current.visible = True
            conversion_progress.current.value = None # Indeterminate
            conversion_progress.current.update()

            # 1. Check/Download Model
            if not model_manager.is_model_installed(model_info):
                log(f"Downloading model {model_info['name']}...")
                if not model_manager.download_model(model_info, lambda d, t: None):
                    log("Error: Failed to download model.")
                    return
                log("Model downloaded.")
            
            # 2. Initialize TTS
            log("Initializing TTS engine...")
            model_path = os.path.join(model_manager.models_dir, model_info['extracted_dir'])
            config = model_info.copy()
            config['model_dir'] = model_path
            
            if not tts_engine.initialize_model(config):
                log("Error: Failed to initialize TTS engine.")
                return

            # 3. Parse EPUB
            log(f"Parsing EPUB: {current_epub_path}...")
            chapters = epub_processor.extract_chapters(current_epub_path)
            log(f"Found {len(chapters)} chapters.")
            
            if not chapters:
                log("Error: No chapters found.")
                return

            # Prepare Output Directory
            base_name = os.path.splitext(os.path.basename(current_epub_path))[0]
            output_dir = os.path.join(os.path.dirname(current_epub_path), f"{base_name}_audiobook")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            generated_files = []
            
            # 4. Convert Chapters
            conversion_progress.current.value = 0
            conversion_progress.current.update()
            
            for i, chapter in enumerate(chapters):
                title = chapter['title']
                text = chapter['content']
                safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
                filename = f"{i+1:03d}_{safe_title}.wav" # Generate WAV first
                filepath = os.path.join(output_dir, filename)
                
                log(f"Generating Chapter {i+1}/{len(chapters)}: {title}...")
                
                # Estimate duration? No, just generate.
                if tts_engine.generate_audio(text, filepath):
                    # Get duration for metadata
                    info = sf.info(filepath)
                    chapter['duration'] = info.duration
                    generated_files.append(filepath)
                else:
                    log(f"Error generating chapter {i+1}")
                
                conversion_progress.current.value = (i + 1) / len(chapters)
                conversion_progress.current.update()

            # 5. Merge if M4B
            output_format = output_format_radio.current.value
            if output_format == "m4b" and generated_files:
                log("Merging into M4B...")
                m4b_path = os.path.join(os.path.dirname(current_epub_path), f"{base_name}.m4b")
                metadata_path = os.path.join(output_dir, "metadata.txt")
                
                if audio_builder.create_chapter_metadata(chapters[:len(generated_files)], metadata_path):
                    if audio_builder.merge_chapters_to_m4b(generated_files, m4b_path, metadata_path):
                        log(f"M4B Created: {m4b_path}")
                    else:
                        log("Error merging M4B.")
                else:
                    log("Error creating metadata.")

            log("Process Complete!")
            
        except Exception as e:
            log(f"Unexpected Error: {e}")
            logging.error(e, exc_info=True)
        finally:
            start_btn.current.disabled = False
            start_btn.current.update()
            conversion_progress.current.visible = False
            conversion_progress.current.update()

    def start_click(e):
        threading.Thread(target=run_conversion, daemon=True).start()

    # Layout
    page.add(
        ft.Column([
            ft.Text("AB-Maker", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text("1. Select EPUB File", weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.ElevatedButton("Pick EPUB", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["epub"])),
                ft.Text("No file selected", ref=selected_file_path, expand=True)
            ]),
            
            ft.Divider(),
            
            ft.Text("2. Select Voice Model", weight=ft.FontWeight.BOLD),
            ft.Dropdown(ref=model_dropdown, label="Voice Model"),
            
            ft.Divider(),
            
            ft.Text("3. Output Format", weight=ft.FontWeight.BOLD),
            ft.RadioGroup(ref=output_format_radio, content=ft.Column([
                ft.Radio(value="mp3", label="Separate WAV Files (Chapters)"), # Actually generating WAV for now
                ft.Radio(value="m4b", label="Single M4B Audiobook (Chapterized)")
            ]), value="m4b"),
            
            ft.Divider(),
            
            ft.FilledButton("Start Conversion", ref=start_btn, icon=ft.Icons.PLAY_ARROW, on_click=start_click),
            
            ft.ProgressBar(ref=conversion_progress, visible=False),
            
            ft.Container(
                content=ft.ListView(ref=log_view, expand=True, auto_scroll=True),
                height=200,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10,
                bgcolor=ft.Colors.SURFACE_VARIANT
            )
        ])
    )
    
    # Load initial data
    load_models()

if __name__ == "__main__":
    ft.app(target=main)
