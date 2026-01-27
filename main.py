import flet as ft
import os
import threading
import time
import logging
import json # Added for config
from model_manager import ModelManager
from epub_processor import EpubProcessor
from tts_engine import TTSEngine
from audio_builder import AudioBuilder
import soundfile as sf
import winsound

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(page: ft.Page):
    page.title = "AB-Maker: Audiobook Creator"
    
    # Load Theme
    config = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", 'r') as f:
                config = json.load(f)
        except: pass
    
    theme_pref = config.get("theme_mode", "system")
    if theme_pref == "dark":
        page.theme_mode = ft.ThemeMode.DARK
    elif theme_pref == "light":
        page.theme_mode = ft.ThemeMode.LIGHT
    else:
        page.theme_mode = ft.ThemeMode.SYSTEM

    page.window_width = 900
    page.window_height = 800
    page.padding = 20

    # Initialize modules
    model_manager = ModelManager()
    epub_processor = EpubProcessor()
    tts_engine = TTSEngine()
    audio_builder = AudioBuilder()
    
    # Check FFmpeg on startup
    ffmpeg_available = audio_builder.check_ffmpeg()
    if not ffmpeg_available:
        page.banner = ft.Banner(
            bgcolor=ft.Colors.AMBER_100,
            leading=ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.AMBER_900),
            content=ft.Text(
                "FFmpeg is not installed or not in PATH. M4B features will be disabled.",
                color=ft.Colors.BLACK
            ),
            actions=[
                ft.TextButton("Dismiss", on_click=lambda e: page.close_banner())
            ],
        )
        page.banner.open = True
        page.update()

    # State variables
    cancel_event = threading.Event()
    selected_file_path = ft.Ref[ft.Text]()
    conversion_progress = ft.Ref[ft.ProgressBar]()
    conversion_status_text = ft.Ref[ft.Text]() # New detailed status
    log_view = ft.Ref[ft.ListView]()
    start_btn = ft.Ref[ft.ElevatedButton]()
    cancel_btn = ft.Ref[ft.ElevatedButton]() # New cancel button
    model_dropdown = ft.Ref[ft.Dropdown]()
    gpu_switch = ft.Ref[ft.Switch]() # New GPU switch
    speed_slider = ft.Ref[ft.Slider]() # New speed slider
    # preview_audio removed due to Flet version issue
    item_preview_path = None # Track temp file to clean up
    # page.overlay.append(preview_audio) removed
    
    output_format_radio = ft.Ref[ft.RadioGroup]()
    speaker_id_input = ft.Ref[ft.TextField]() # New for multi-speaker
    custom_output_dir = ft.Ref[ft.Text]() # New for output selection
    
    output_format_radio = ft.Ref[ft.RadioGroup]()
    speaker_id_input = ft.Ref[ft.TextField]()
    custom_output_dir = ft.Ref[ft.Text]()
    
    selected_epubs = []
    current_epub_path = None
    chapters_cache = {} # Store chapters for editing: {path: [chapters]}
    
    # --- Phase 3: History & Theme ---
    CONFIG_FILE = "config.json"

    def load_config():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(config):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            log(f"Error saving config: {e}")

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.update()
        # Save theme preference
        config = load_config()
        config['theme_mode'] = "dark" if page.theme_mode == ft.ThemeMode.DARK else "light"
        save_config(config)

    def load_history():
        config = load_config()
        return config.get("recent_files", [])

    def save_history(path):
        config = load_config()
        history = config.get("recent_files", [])
        if path in history:
            history.remove(path)
        history.insert(0, path)
        config["recent_files"] = history[:10]
        save_config(config)
        update_history_menu()

    def history_click(e):
        # Handle recent file click
        path = e.control.data
        if os.path.exists(path):
            pick_file_result(ft.FilePickerResultEvent(files=[ft.FilePickerResultEvent(path=path, name=os.path.basename(path), size=0)], path=None))
        else:
            log(f"File not found: {path}")

    history_menu = ft.PopupMenuButton(icon=ft.Icons.HISTORY, tooltip="Recent Files")

    def update_history_menu():
        history = load_history()
        history_menu.items = [
            ft.PopupMenuItem(text=path, on_click=history_click, data=path) for path in history
        ]
        if not history:
            history_menu.items = [ft.PopupMenuItem(text="No recent files", disabled=True)]
        if page.appbar:
            page.update()

    # --- Phase 3: Drag & Drop ---
    def on_drop(e):
        # flet DropEvent returns path in e.data usually, or e.files? 
        # Actually page.on_file_drop returns a FilePickerResultEvent-like object in recent flet versions or string?
        # Let's check docs or assume standard behavior: e.files
        # But page.on_drop event is different. user_data is e.data?
        # Let's assume on_file_drop passes a normal event with files.
        # WAIT: page.on_file_drop is e.files.
        if e.files:
            file_paths = [f.path for f in e.files if f.path.lower().endswith(".epub")]
            if file_paths:
                # Trigger logic similar to picker
                 # We need to manually update state since pick_file_result expects specific event
                 nonlocal selected_epubs, current_epub_path
                 selected_epubs = file_paths
                 count = len(selected_epubs)
                 selected_file_path.current.value = f"{count} file(s) selected (Drag & Drop)"
                 selected_file_path.current.update()
                 log(f"Dropped {count} EPUBs.")
                 # Add first to history
                 save_history(file_paths[0])
            else:
                log("Ignored dropped files (not EPUB).")

    page.on_file_drop = on_drop

    # --- AppBar ---
    page.appbar = ft.AppBar(
        title=ft.Text("AB-Maker"),
        center_title=False,
        bgcolor=ft.Colors.GREY_200,
        actions=[
            history_menu,
            ft.IconButton(ft.Icons.DARK_MODE, on_click=toggle_theme, tooltip="Toggle Dark Mode"),
        ],
    )
    update_history_menu()
    
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
        # Check if selected model is installed
        model_key = model_dropdown.current.value
        model_info = next((opt.data for opt in model_dropdown.current.options if opt.key == model_key), None)
        if model_info:
            is_installed = model_manager.is_model_installed(model_info)
            if not is_installed:
                log(f"Note: Model '{model_info['name']}' is not installed. It will be downloaded automatically (approx 50-100MB) when you start conversion.")
            else:
                log(f"Selected model: {model_info['name']}")

    def delete_model_click(e):
        model_key = model_dropdown.current.value
        model_info = next((opt.data for opt in model_dropdown.current.options if opt.key == model_key), None)
        if not model_info:
             return
        
        if not model_manager.is_model_installed(model_info):
            log("Model is not installed.")
            return

        def close_dlg(e):
            confirm_dlg.open = False
            page.update()

        def confirm_delete(e):
            if model_manager.delete_model(model_info):
                log(f"Deleted model: {model_info['name']}")
                load_models() # Refresh dropdown
            else:
                log("Error deleting model.")
            close_dlg(e)

        confirm_dlg = ft.AlertDialog(
            title=ft.Text("Delete Model"),
            content=ft.Text(f"Are you sure you want to delete '{model_info['name']}'?"),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = confirm_dlg
        confirm_dlg.open = True
        page.update()

    def pick_file_result(e):
        nonlocal selected_epubs
        if e.files:
            selected_epubs = [f.path for f in e.files]
            count = len(selected_epubs)
            selected_file_path.current.value = f"{count} file(s) selected"
            selected_file_path.current.update()
            log(f"Selected {count} EPUBs.")
            save_history(selected_epubs[0]) # Save first one to history

    def pick_folder_result(e):
        if e.path:
            custom_output_dir.current.value = e.path
            custom_output_dir.current.update()
            log(f"Output folder set to: {e.path}")

    file_picker = ft.FilePicker(on_result=pick_file_result)
    folder_picker = ft.FilePicker(on_result=pick_folder_result) # New folder picker
    page.overlay.append(file_picker)
    page.overlay.append(folder_picker)

    def cancel_click(e):
        cancel_event.set()
        log("Cancelling...")
        cancel_btn.current.disabled = True
        cancel_btn.current.update()

    def preview_click(e):
        nonlocal item_preview_path
        model_key = model_dropdown.current.value
        model_info = next((opt.data for opt in model_dropdown.current.options if opt.key == model_key), None)
        
        if not model_info:
            log("Error: Select a model to preview.")
            return

        # Disable button during generation
        e.control.disabled = True
        e.control.update()
        
        def _generate_preview():
            try:
                # Ensure model is ready (minimal check)
                if not model_manager.is_model_installed(model_info):
                     # For preview, we might just require it to be installed for simplicity, 
                     # or auto-download. Let's require install or warn.
                     log("Downloading model for preview...")
                     if not model_manager.download_model(model_info):
                         log("Error: Could not download model for preview.")
                         return

                # Init TTS if needed
                model_path = os.path.join(model_manager.models_dir, model_info['extracted_dir'])
                config = model_info.copy()
                config['model_dir'] = model_path
                
                # We reuse the main tts_engine instance. 
                # NOTE: concurrency issue if converting? 
                # Ideally we shouldn't preview while converting. available UI prevents this mostly.
                if not tts_engine.initialize_model(config):
                     log("Error: Failed to init TTS for preview.")
                     return

                # Generate sample
                text = "This is a preview of the selected voice."
                temp_file = os.path.join(model_manager.models_dir, "preview_temp.wav")
                speed = speed_slider.current.value
                try:
                    sid = int(speaker_id_input.current.value)
                except:
                    sid = 0
                
                if tts_engine.generate_audio(text, temp_file, speed=speed, sid=sid):
                    # Play using winsound (Windows only)
                    log("Playing preview...")
                    winsound.PlaySound(temp_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    log("Error generating preview.")
            except Exception as ex:
                log(f"Preview error: {ex}")
            finally:
                e.control.disabled = False
                e.control.update()
                page.update()

        threading.Thread(target=_generate_preview, daemon=True).start()

    def view_chapters_click(e):
        if not selected_epubs:
             log("No EPUB selected.")
             return
        
        # Load chapters for the first book as regular preview
        epub_path = selected_epubs[0]
        # Check cache or load
        if epub_path not in chapters_cache:
            try:
                chapters_cache[epub_path] = epub_processor.extract_chapters(epub_path)
            except Exception as ex:
                log(f"Error parsing chapters: {ex}")
                return

        chapters = chapters_cache[epub_path]
        
        def save_edits(e):
            # Updates are happening in-place in 'chapters' list references if logic allows
            # But DataTable cells need logic to update data source
            dlg.open = False
            page.update()
            log("Chapters updated (Client-side only for now - title changes persisted in memory).")

        def close_dlg(e):
            dlg.open = False
            page.update()

        # Simple DataTable
        dt = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("#")),
                ft.DataColumn(ft.Text("Title")),
                ft.DataColumn(ft.Text("Length (chars)")),
            ],
            rows=[]
        )
        
        for i, ch in enumerate(chapters):
            # We want editable Title
            # Use TextField in a cell?
            title_field = ft.TextField(value=ch['title'], border=ft.InputBorder.NONE, height=30, text_style=ft.TextStyle(size=12))
            # Bind change
            def on_change(e, index=i):
                chapters[index]['title'] = e.control.value
            title_field.on_change = on_change
            
            dt.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(i+1))),
                ft.DataCell(title_field),
                ft.DataCell(ft.Text(str(len(ch['content'])))),
            ]))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Chapters: {os.path.basename(epub_path)}"),
            content=ft.Column([
                ft.Text("Edit chapter titles below. These changes apply to conversion."),
                ft.Container(content=dt, height=300, scroll=ft.ScrollMode.ALWAYS)
            ], height=350, width=500),
            actions=[
                ft.TextButton("Close", on_click=close_dlg)
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def run_conversion():
        try:
            cancel_event.clear()
            if not selected_epubs:
                log("Error: No EPUB files selected.")
                return

            model_key = model_dropdown.current.value
            model_info = next((opt.data for opt in model_dropdown.current.options if opt.key == model_key), None)
            
            if not model_info:
                log("Error: No model selected.")
                return

            # Disable UI
            # Disable UI
            start_btn.current.disabled = True
            start_btn.current.update()
            cancel_btn.current.disabled = False # Enable cancel
            cancel_btn.current.update()
            
            conversion_progress.current.visible = True
            conversion_progress.current.value = None # Indeterminate
            conversion_status_text.current.value = "Preparing..."
            conversion_progress.current.update()
            conversion_status_text.current.update()

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
            
            # 2.5 Get SID
            try:
                sid = int(speaker_id_input.current.value)
            except:
                sid = 0
                log("Invalid Speaker ID, defaulting to 0.")
            
            # Set provider based on switch
            use_gpu = gpu_switch.current.value
            config['provider'] = "cuda" if use_gpu else "cpu"
            if use_gpu:
                log("Attempting to use GPU (CUDA)...")

            if not tts_engine.initialize_model(config):
                log("Error: Failed to initialize TTS engine. If using GPU, ensure CUDA and onnxruntime-gpu are installed.")
                return

            # Batch Loop
            total_books = len(selected_epubs)
            
            for b_idx, epub_path in enumerate(selected_epubs):
                if cancel_event.is_set(): break
                
                log(f"Processing Book {b_idx+1}/{total_books}: {os.path.basename(epub_path)}")
                
                # 3. Parse EPUB
                log(f"Parsing EPUB...")
                chapters = epub_processor.extract_chapters(epub_path)
                log(f"Found {len(chapters)} chapters.")
                
                if not chapters:
                    log("Error: No chapters found. Skipping.")
                    continue

                # Prepare Output Directory
                base_name = os.path.splitext(os.path.basename(epub_path))[0]
                
                if custom_output_dir.current.value:
                    # Use custom root, create subfolder for book
                    output_dir = os.path.join(custom_output_dir.current.value, f"{base_name}_audiobook")
                else:
                    # Default: next to epub
                    output_dir = os.path.join(os.path.dirname(epub_path), f"{base_name}_audiobook")
                
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                generated_files = []
                
                # ESTIMATED TIME
                total_chars = sum(len(c['content']) for c in chapters)
                # Assume 15 chars/sec for 1.0x (rough heuristic) across languages?
                # or just count sentences? Text length is proxy.
                # 1000 chars ~ 1 min audio roughly?
                est_minutes = (total_chars / 900) / speed_slider.current.value
                log(f"Estimated Audio Duration: ~{int(est_minutes)} mins")
                
                # 4. Convert Chapters
                total_chapters = len(chapters)
                
                for i, chapter in enumerate(chapters):
                    if check_cancel(): break
                    
                    conversion_status_text.current.value = f"Book {b_idx+1}/{total_books} | Ch {i+1}/{total_chapters}: {chapter['title'][:20]}..."
                    conversion_status_text.current.update()
                    conversion_progress.current.value = (i + 1) / total_chapters
                    conversion_progress.current.update()

                    title = chapter['title']
                    text = chapter['content']
                    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
                    filename = f"{i+1:03d}_{safe_title}.wav" # Generate WAV first
                    filepath = os.path.join(output_dir, filename)
                    
                    # RESUME LOGIC: Check if exists
                    if os.path.exists(filepath):
                        # Optional: Check size > 0?
                        try:
                            if os.path.getsize(filepath) > 1000:
                                log(f"Skipping Ch {i+1} (Exists): {title}")
                                generated_files.append(filepath)
                                continue
                        except: pass
                    
                    log(f"Generating Ch {i+1}: {title}...")
                    
                    speed = speed_slider.current.value
                    if tts_engine.generate_audio(text, filepath, speed=speed, sid=sid):
                         # Get duration
                        info = sf.info(filepath)
                        chapter['duration'] = info.duration
                        generated_files.append(filepath)
                    else:
                        log(f"Error generating chapter {i+1}")
                    
                
                # 5. Merge if M4B or Convert to MP3
                if check_cancel():
                     log("Post-processing skipped (Cancelled).")
                else:
                    output_format = output_format_radio.current.value
                    
                    if output_format == "mp3":
                        # Post-process WAVs to MP3
                        if not audio_builder.check_ffmpeg():
                             log("Error: FFmpeg required for MP3.")
                        else:
                             log("Converting to MP3...")
                             conversion_status_text.current.value = "Converting to MP3..."
                             conversion_status_text.current.update()
                             for wav_file in generated_files:
                                 if check_cancel(): break
                                 mp3_file = wav_file.replace(".wav", ".mp3")
                                 if audio_builder.convert_to_mp3(wav_file, mp3_file):
                                     log(f"Created: {os.path.basename(mp3_file)}")
                                     # Optionally remove wav? Keeping for safety.
                                 else:
                                     log(f"Error converting {os.path.basename(wav_file)}")
                             log("MP3 Conversion Complete.")
                             
                    elif output_format == "m4b" and generated_files:
                        if not audio_builder.check_ffmpeg():
                            log("Error: FFmpeg not found. Cannot create M4B. WAV files are saved.")
                        else:
                            conversion_status_text.current.value = "Merging into M4B..."
                            conversion_status_text.current.update()
                            
                            log("Merging into M4B...")
                            # M4B goes to same parent as output_dir usually, or inside?
                            # Standard: outside the chapter folder
                            m4b_path = os.path.join(os.path.dirname(output_dir), f"{base_name}.m4b")
                            
                            metadata_path = os.path.join(output_dir, "metadata.txt")
                            
                            # Need chapters with duration for metadata. If we skipped generation,
                            # we need to read duration from existing files!
                            # Re-read duration for all generated files
                            valid_chapters = []
                            for idx, gf in enumerate(generated_files):
                                if idx < len(chapters):
                                     # Update duration
                                     chapters[idx]['duration'] = sf.info(gf).duration
                                     valid_chapters.append(chapters[idx])

                            if audio_builder.create_chapter_metadata(valid_chapters, metadata_path):
                                if audio_builder.merge_chapters_to_m4b(generated_files, m4b_path, metadata_path):
                                    log(f"M4B Created: {m4b_path}")
                                else:
                                    log("Error merging M4B.")
                            else:
                                log("Error creating metadata.")

            if cancel_event.is_set():
                log("Batch Process Cancelled.")
                conversion_status_text.current.value = "Cancelled."
            else:
                log("Batch Process Complete!")
                conversion_status_text.current.value = "Done!"
            
        except Exception as e:
            log(f"Unexpected Error: {e}")
            logging.error(e, exc_info=True)
        finally:
            start_btn.current.disabled = False
            start_btn.current.update()
            cancel_btn.current.disabled = True
            cancel_btn.current.update()
            conversion_progress.current.visible = False
            conversion_progress.current.update()
            conversion_status_text.current.update()

    def start_click(e):
        threading.Thread(target=run_conversion, daemon=True).start()

    # Layout
    page.add(
        ft.Column([
            ft.Text("AB-Maker", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text("1. Select EPUB File", weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.ElevatedButton("Pick EPUB(s)", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: file_picker.pick_files(allow_multiple=True, allowed_extensions=["epub"])),
                ft.Text("No file selected", ref=selected_file_path, expand=True)
            ]),
            
            # Chapter Editor Button
            ft.Row([
                 ft.OutlinedButton("View/Edit Chapters", icon=ft.Icons.LIST, on_click=lambda e: view_chapters_click(e))
            ]),
            
            ft.Container(height=5),
            ft.Row([
                ft.ElevatedButton("Output Folder (Optional)", icon=ft.Icons.FOLDER, on_click=lambda _: folder_picker.get_directory_path()),
                ft.Text(ref=custom_output_dir, value="", size=10, italic=True)
            ]),
            
            ft.Divider(),
            
            ft.Text("2. Select Voice Model", weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Dropdown(ref=model_dropdown, label="Voice Model", on_change=on_model_change, expand=True),
                ft.IconButton(icon=ft.Icons.PLAY_CIRCLE, tooltip="Preview Voice", on_click=preview_click),
                ft.IconButton(icon=ft.Icons.DELETE, tooltip="Delete Model", on_click=delete_model_click, icon_color=ft.Colors.ERROR)
            ]),
            
            ft.TextField(ref=speaker_id_input, label="Speaker ID (0-N)", value="0", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), tooltip="For multi-speaker models (e.g. LibriTTS)"),
            
            ft.Row([
                ft.Text("Use GPU (CUDA)", size=14),
                ft.Switch(ref=gpu_switch, value=False, tooltip="Enable experimental GPU support (Requires CUDA & onnxruntime-gpu)"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Text("Speaking Rate", size=14),
            ft.Slider(ref=speed_slider, min=0.5, max=2.5, divisions=20, value=1.0, label="{value}x"),

            ft.Divider(),
            
            ft.Text("3. Output Format", weight=ft.FontWeight.BOLD),
            ft.RadioGroup(ref=output_format_radio, content=ft.Column([
                ft.Radio(value="wav", label="Separate WAV Files (Chapters)"), 
                ft.Radio(value="mp3", label="Separate MP3 Files (Chapters)"), # New MP3
                ft.Radio(value="m4b", label="Single M4B Audiobook (Chapterized)")
            ]), value="m4b" if ffmpeg_available else "wav"),
            
            ft.Divider(),
            
            ft.Row([
                ft.FilledButton("Start Conversion", ref=start_btn, icon=ft.Icons.PLAY_ARROW, on_click=start_click, expand=True),
                ft.ElevatedButton("Cancel", ref=cancel_btn, icon=ft.Icons.CANCEL, on_click=cancel_click, disabled=True, color=ft.Colors.ERROR)
            ]),
            
            ft.Container(height=10),
            ft.Text(ref=conversion_status_text, value="Ready", size=12, italic=True),
            ft.ProgressBar(ref=conversion_progress, visible=False),
            
            ft.Container(
                content=ft.ListView(ref=log_view, expand=True, auto_scroll=True),
                height=200,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10,
                bgcolor=ft.Colors.GREY_100
            )
        ])
    )
    
    # Load initial data
    load_models()

if __name__ == "__main__":
    ft.app(target=main)
