import flet as ft
import os
import threading
import time
import logging
from model_manager import ModelManager
from epub_processor import EpubProcessor
from tts_engine import TTSEngine
from audio_builder import AudioBuilder
from config_manager import ConfigManager
from conversion_worker import ConversionWorker
try:
    import winsound
except ImportError:
    winsound = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(page: ft.Page):
    # --- Setup & Configuration ---
    page.title = "AB-Maker: Audiobook Creator"
    page.window_width = 950
    page.window_height = 850
    page.padding = 20
    
    # Initialize Managers
    config_mgr = ConfigManager()
    model_manager = ModelManager()
    epub_processor = EpubProcessor()
    tts_engine = TTSEngine()
    audio_builder = AudioBuilder()
    
    # Load Theme
    theme_pref = config_mgr.get("theme_mode", "system")
    page.theme_mode = getattr(ft.ThemeMode, theme_pref.upper(), ft.ThemeMode.SYSTEM)

    # State Variables
    selected_epubs = []
    chapters_cache = {} 
    current_worker = None
    
    # --- UI References ---
    log_view = ft.Ref[ft.ListView]()
    start_btn = ft.Ref[ft.FilledButton]()
    cancel_btn = ft.Ref[ft.ElevatedButton]()
    conversion_progress = ft.Ref[ft.ProgressBar]()
    conversion_status_text = ft.Ref[ft.Text]()
    
    # Inputs
    model_dropdown = ft.Ref[ft.Dropdown]()
    speed_slider = ft.Ref[ft.Slider]()
    speed_label = ft.Ref[ft.Text]()
    speaker_input = ft.Ref[ft.TextField]()
    gpu_switch = ft.Ref[ft.Switch]()
    format_group = ft.Ref[ft.RadioGroup]()
    output_dir_text = ft.Ref[ft.Text]()
    selected_file_text = ft.Ref[ft.Text]()

    # --- Helper Functions ---
    def log(message):
        if log_view.current:
            log_view.current.controls.append(ft.Text(message, size=12, font_family="Consolas"))
            log_view.current.update()
            # Auto-scroll?
            log_view.current.scroll_to(offset=-1, duration=500)

    # --- Callbacks for Worker ---
    def on_worker_log(msg):
        # Thread-safe update? Flet 0.21+ handles this well usually, or use page.run_task
        # safely we can just call update if we are careful, or use page.call_later
        log(msg)

    def on_worker_progress(val):
        conversion_progress.current.visible = True
        conversion_progress.current.value = val
        conversion_progress.current.update()

    def on_worker_status(msg, progress=None):
        conversion_status_text.current.value = msg
        conversion_status_text.current.update()
        if progress is not None:
             on_worker_progress(progress)

    def on_worker_done():
        nonlocal current_worker
        current_worker = None
        start_btn.current.disabled = False
        start_btn.current.update()
        cancel_btn.current.disabled = True
        cancel_btn.current.update()
        conversion_progress.current.visible = False
        conversion_progress.current.update()
        conversion_status_text.current.value = "Ready"
        conversion_status_text.current.update()
        log("Process finished.")
        
        # Play sound on finish (Windows only safe verify)
        try:
             import winsound
             winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except: pass

    # Initialize Worker
    worker = ConversionWorker(
        tts_engine, audio_builder, 
        log_callback=on_worker_log,
        progress_callback=on_worker_progress,
        status_callback=on_worker_status,
        done_callback=on_worker_done
    )

    # --- Event Handlers ---
    
    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        config_mgr.set("theme_mode", page.theme_mode.name.lower())
        page.update()

    def on_files_selected(e):
        nonlocal selected_epubs
        if e.files:
            selected_epubs = [f.path for f in e.files]
            count = len(selected_epubs)
            selected_file_text.current.value = f"{count} file(s) selected: {os.path.basename(selected_epubs[0])}..."
            selected_file_text.current.update()
            config_mgr.add_recent_file(selected_epubs[0])
            update_history_menu()
            start_btn.current.disabled = False
            start_btn.current.update()

    def on_folder_selected(e):
        if e.path:
            output_dir_text.current.value = e.path
            output_dir_text.current.update()

    def on_speed_change(e):
        val = e.control.value
        speed_label.current.value = f"{val}x"
        speed_label.current.update()
        config_mgr.set("last_speed", val)

    def on_gpu_change(e):
        config_mgr.set("use_gpu", e.control.value)

    def on_speaker_change(e):
        config_mgr.set("last_speaker_id", e.control.value)

    def on_model_change(e):
        # Persist logic could go here
        # Check if installed
        model_key = model_dropdown.current.value
        config_mgr.set("last_model", model_key)
        
        model_info = next((opt.data for opt in model_dropdown.current.options if opt.key == model_key), None)
        if model_info and not model_manager.is_model_installed(model_info):
            log(f"NOTE: Model {model_info['name']} needs to be downloaded.")

    def start_conversion_click(e):
        if not selected_epubs:
            log("No files selected!")
            return
            
        model_key = model_dropdown.current.value
        model_info = next((opt.data for opt in model_dropdown.current.options if opt.key == model_key), None)
        if not model_info:
            log("Please select a valid model.")
            return

        # Prepare UI
        start_btn.current.disabled = True
        start_btn.current.update()
        cancel_btn.current.disabled = False
        cancel_btn.current.update()
        
        # Download if needed (blocking UI for simplicity or we can move to worker? Worker handles it?)
        # For better UX, let's do it here or let worker handle. Worker is cleaner.
        # But worker needs to download first.
        # Let's check installed first.
        if not model_manager.is_model_installed(model_info):
            log(f"Downloading {model_info['name']} (Please wait)...")
            on_worker_status("Downloading Model...", None)
            
            def dl_progress(current, total):
                if total > 0:
                    on_worker_progress(current / total)
            
            if not model_manager.download_model(model_info, dl_progress):
                log("Download failed!")
                on_worker_done()
                return
            log("Download complete.")

        nonlocal current_worker
        current_worker = worker
        
        # Start
        worker.start(
            selected_epubs=selected_epubs,
            model_info=model_info,
            output_dir_root=output_dir_text.current.value,
            speed=speed_slider.current.value,
            speaker_id=speaker_input.current.value,
            output_format=format_group.current.value,
            use_gpu=gpu_switch.current.value,
            epub_processor=epub_processor
        )

    def cancel_click(e):
        if current_worker:
            current_worker.cancel()
            cancel_btn.current.disabled = True # Prevent double types
            cancel_btn.current.update()

    def view_chapters_click(e):
        if not selected_epubs:
             log("No EPUB selected.")
             return
        
        epub_path = selected_epubs[0]
        if epub_path not in chapters_cache:
            try:
                chapters_cache[epub_path] = epub_processor.extract_chapters(epub_path)
            except Exception as ex:
                log(f"Error reading chapters: {ex}")
                return

        chapters = chapters_cache[epub_path]
        
        dt = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("#")),
                ft.DataColumn(ft.Text("Title")),
                ft.DataColumn(ft.Text("Length")),
            ],
            rows=[]
        )
        
        for i, ch in enumerate(chapters):
            title_field = ft.TextField(value=ch['title'], text_size=12, border="none", height=30)
            def on_t_change(e, idx=i):
                 chapters[idx]['title'] = e.control.value
            title_field.on_change = on_t_change
            
            dt.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(i+1))),
                ft.DataCell(title_field),
                ft.DataCell(ft.Text(f"{len(ch['content'])} chars")),
            ]))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Chapters: {os.path.basename(epub_path)}"),
            content=ft.Column([dt], height=400, scroll=ft.ScrollMode.ALWAYS),
            actions=[ft.TextButton("Close", on_click=lambda e: page.close_dialog())]
        )
        page.show_dialog(dlg)

    # --- Setup UI Components ---
    
    # File Pickers
    file_picker = ft.FilePicker(on_result=on_files_selected)
    folder_picker = ft.FilePicker(on_result=on_folder_selected)
    page.overlay.extend([file_picker, folder_picker])
    
    # History Menu
    history_menu = ft.PopupMenuButton(icon=ft.Icons.HISTORY, tooltip="Recent Files")
    def update_history_menu():
        hist = config_mgr.get_recent_files()
        history_menu.items = [
            ft.PopupMenuItem(
                text=os.path.basename(p), 
                on_click=lambda e, p=p: on_files_selected(SimpleEvent(files=[SimpleFile(p)]))
            ) for p in hist
        ] if hist else [ft.PopupMenuItem(text="No recent files", disabled=True)]
        if page.appbar: page.update()

    # Mocks because Flet events are hard to instantiate manually
    class SimpleFile:
         def __init__(self, path): self.path = path
    class SimpleEvent:
         def __init__(self, files): self.files = files

    update_history_menu()

    # About Dialog
    def open_about(e):
        dlg = ft.AlertDialog(
            title=ft.Text("About AB-Maker"),
            content=ft.Column([
                ft.Text("Version: 1.1.0"),
                ft.Text("Created with Flet & Sherpa-ONNX"),
                ft.Text("A local, private audiobook creator."),
                ft.Divider(),
                ft.Text("© 2026 AB-Maker Team", size=12, italic=True)
            ], tight=True),
            actions=[ft.TextButton("Close", on_click=lambda e: page.close_dialog())]
        )
        page.show_dialog(dlg)
    
    # Initialize Model Dropdown
    models = model_manager.list_available_models()
    model_opts = []
    last_model = config_mgr.get("last_model")
    for m in models:
        key = m['name']
        installed = "(Installed)" if model_manager.is_model_installed(m) else ""
        model_opts.append(ft.dropdown.Option(key=key, text=f"{key} {installed}", data=m))
    
    model_dropdown_ctrl = ft.Dropdown(
        ref=model_dropdown, 
        options=model_opts, 
        value=last_model if last_model else model_opts[0].key if model_opts else None,
        label="Voice Model",
        on_change=on_model_change,
        expand=True
    )

    # Build Layout
    page.appbar = ft.AppBar(
        title=ft.Text("AB-Maker", weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.SURFACE_VARIANT,
        actions=[
            history_menu,
            ft.IconButton(ft.Icons.INFO_OUTLINE, tooltip="About", on_click=open_about),
            ft.IconButton(ft.Icons.DARK_MODE, on_click=toggle_theme)
        ]
    )

    page.add(
        ft.Column([
            # Section 1: Input
            ft.Container(
                content=ft.Column([
                    ft.Text("1. Input & Output", weight=ft.FontWeight.BOLD, size=16),
                    ft.Row([
                        ft.ElevatedButton("Select EPUB", icon=ft.Icons.BOOK, on_click=lambda _: file_picker.pick_files(allow_multiple=True, allowed_extensions=['epub'])),
                        ft.Text("Drag & Drop supported", ref=selected_file_text, italic=True, size=12)
                    ]),
                    ft.Row([
                        ft.OutlinedButton("Edit Chapters", icon=ft.Icons.EDIT_NOTE, on_click=view_chapters_click, tooltip="Preview and rename chapters"),
                        ft.ElevatedButton("Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: folder_picker.get_directory_path()),
                        ft.Text("Default (Same as Book)", ref=output_dir_text, size=10)
                    ])
                ]),
                padding=15,
                bgcolor=ft.Colors.SURFACE_VARIANT,
                border_radius=10
            ),
            
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

            # Section 2: Configuration
            ft.Container(
                content=ft.Column([
                    ft.Text("2. Voice Configuration", weight=ft.FontWeight.BOLD, size=16),
                    ft.Row([
                        model_dropdown_ctrl,
                        ft.Column([
                            ft.Text("Speaker ID", size=12),
                            ft.TextField(ref=speaker_input, value=config_mgr.get("last_speaker_id", "0"), width=80, text_size=12, on_change=on_speaker_change)
                        ])
                    ]),
                    ft.Row([
                        ft.Text("Speed:", size=14),
                        ft.Slider(
                            ref=speed_slider, 
                            min=0.5, max=2.5, divisions=20, 
                            value=config_mgr.get("last_speed", 1.0), 
                            label="{value}x", 
                            expand=True,
                            on_change=on_speed_change
                        ),
                        ft.Text(f"{config_mgr.get('last_speed', 1.0)}x", ref=speed_label, weight=ft.FontWeight.BOLD)
                    ]),
                    ft.Row([
                        ft.Switch(ref=gpu_switch, label="Use GPU (CUDA)", value=config_mgr.get("use_gpu", False), on_change=on_gpu_change, tooltip="Requires NVIDIA GPU and CUDA drivers"),
                    ])
                ]),
                padding=15,
                bgcolor=ft.Colors.SURFACE_VARIANT,
                border_radius=10
            ),
            
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

            # Section 3: Format & Action
            ft.Container(
                content=ft.Column([
                    ft.Text("3. Finalize", weight=ft.FontWeight.BOLD, size=16),
                    ft.RadioGroup(ref=format_group, value=config_mgr.get("output_format", "m4b"), content=ft.Column([
                        ft.Row([
                            ft.Radio(value="m4b", label="M4B Audiobook (Recommended)"),
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16, tooltip="Single file with chapters. Best for Apple Books, Audible, and modern players.")
                        ]),
                        ft.Radio(value="mp3", label="MP3 Files (Zipped or Folder)"),
                        ft.Radio(value="wav", label="WAV (Lossless Source)")
                    ])),
                    ft.Row([
                        ft.FilledButton("Start Conversion", icon=ft.Icons.ROCKET_LAUNCH, ref=start_btn, on_click=start_conversion_click, height=50, expand=True),
                        ft.ElevatedButton("Cancel", icon=ft.Icons.CANCEL, ref=cancel_btn, on_click=cancel_click, height=50, disabled=True, color=ft.Colors.ERROR)
                    ]),
                    ft.ProgressBar(ref=conversion_progress, visible=False, bar_height=5),
                    ft.Text("Ready", ref=conversion_status_text, size=12, text_align=ft.TextAlign.CENTER, width=page.window_width)
                ]),
                padding=15,
                bgcolor=ft.Colors.SURFACE_VARIANT, 
                border_radius=10
            ),

            # Log View
            ft.Container(
                content=ft.ListView(ref=log_view, expand=True, auto_scroll=True, spacing=2),
                height=150,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10,
                margin=ft.margin.only(top=10)
            )
        ], scroll=ft.ScrollMode.HIDDEN) # Main column scroll
    )

    # Check FFmpeg on startup
    if not audio_builder.check_ffmpeg():
        page.banner = ft.Banner(
            bgcolor=ft.Colors.AMBER_100,
            leading=ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.AMBER_900),
            content=ft.Text("FFmpeg not found! M4B/MP3 disabled. Install FFmpeg to enable.", color=ft.Colors.BLACK),
            actions=[ft.TextButton("Dismiss", on_click=lambda e: setattr(page.banner, 'open', False) or page.update())] # Fix for deprecated close_banner
        )
        page.banner.open = True
        page.update()

    # Confirm Exit Handler
    def on_window_event(e):
        if e.data == "close":
            if current_worker:
                dlg = ft.AlertDialog(
                    title=ft.Text("Conversion in Progress"),
                    content=ft.Text("Are you sure you want to exit? The conversion will be stopped."),
                    actions=[
                        ft.TextButton("Yes, Exit", on_click=lambda _: page.window_destroy()),
                        ft.TextButton("No", on_click=lambda _: page.close_dialog())
                    ]
                )
                page.show_dialog(dlg)
            else:
                page.window_destroy()

    page.window_prevent_close = True
    page.on_window_event = on_window_event

    def on_drop(e):
       if e.files:
           on_files_selected(e)
           
    page.on_file_drop = on_drop

if __name__ == "__main__":
    ft.run(target=main)
