# Configuration Guide

Advanced configuration and customization for AB-Maker.

---

## Configuration Files

AB-Maker stores configuration in `%APPDATA%\AB-Maker\`:

```
C:\Users\YourName\AppData\Roaming\AB-Maker\
├── config.json          # User settings
├── models\              # Downloaded TTS models
│   ├── vits-vctk\
│   └── vits-ljs\
├── .cache\              # EPUB parsing cache
└── logs\                # Application logs
```

---

## Quality Presets

### Built-in Presets

Located in: `config/presets.json`

```json
{
  "Low": {
    "bitrate": "32k",
    "channels": "1",
    "sample_rate": "22050",
    "description": "Low quality for testing or very small files"
  },
  "Medium": {
    "bitrate": "64k",
    "channels": "2",
    "sample_rate": "44100",
    "description": "Balanced quality and file size"
  },
  "High": {
    "bitrate": "128k",
    "channels": "2",
    "sample_rate": "44100",
    "description": "High quality for most use cases"
  },
  "Lossless": {
    "codec": "flac",
    "channels": "2",
    "sample_rate": "48000",
    "description": "Perfect quality, larger file size"
  },
  "Podcast": {
    "bitrate": "48k",
    "channels": "1",
    "sample_rate": "44100",
    "description": "Optimized for voice content"
  },
  "Audible": {
    "bitrate": "64k",
    "channels": "1",
    "sample_rate": "22050",
    "description": "Compatible with Audible standards"
  }
}
```

### Creating Custom Presets

1. Open `config/presets.json`
2. Add new preset:
   ```json
   {
     "MyCustom": {
       "bitrate": "96k",
       "channels": "2",
       "sample_rate": "48000",
       "description": "My custom high-quality preset"
     }
   }
   ```
3. Restart AB-Maker
4. Preset appears in Quality dropdown

**Parameters:**
- `bitrate`: Audio bitrate (32k, 64k, 128k, etc.)
- `channels`: "1" (mono) or "2" (stereo)
- `sample_rate`: Sample rate in Hz (22050, 44100, 48000)
- `codec`: Optional (default: aac for M4B, mp3 for MP3)

---

## User Settings

File: `%APPDATA%\AB-Maker\config.json`

### Persistent Settings

```json
{
  "last_model": "vits-vctk",
  "last_speed": 1.0,
  "last_speaker_id": "0",
  "use_gpu": false,
  "output_format": "m4b",
  "last_quality": "Medium",
  "normalize": false,
  "output_dir": "C:\\Users\\YourName\\Documents\\AB-Maker-Output",
  "recent_files": [
    "C:\\Books\\book1.epub",
    "C:\\Books\\book2.epub"
  ],
  "file_status": {
    "C:\\Books\\book1.epub": "completed",
    "C:\\Books\\book2.epub": "in_progress"
  },
  "theme": "dark"
}
```

### Manual Editing

**To reset all settings:**
1. Close AB-Maker
2. Delete `%APPDATA%\AB-Maker\config.json`
3. Restart AB-Maker (creates new config with defaults)

**To change default output folder:**
```json
{
  "output_dir": "D:\\Audiobooks"
}
```

**To clear recent files:**
```json
{
  "recent_files": []
}
```

---

## TTS Models

### Model Configuration

Models stored in: `%APPDATA%\AB-Maker\models\`

Each model folder contains:
```
vits-vctk/
├── model.onnx          # Neural network model
├── tokens.txt          # Tokenizer vocabulary
└── lexicon.txt         # Pronunciation dictionary (optional)
```

### Adding Custom Models

1. Download ONNX model from [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx/releases)
2. Extract to models folder
3. Ensure files named correctly:
   - `model.onnx`
   - `tokens.txt`
4. Restart AB-Maker
5. Model appears in dropdown

**Supported Models:**
- VITS models (recommended)
- Piper models (experimental)

### Model Settings

Some models support configurable parameters:

```python
# In tts_engine.py (advanced)
config = {
    'noise_scale': 0.667,        # Voice variation
    'noise_scale_w': 0.8,        # Speed variation
    'length_scale': 1.0,         # Overall speed
}
```

---

## FFmpeg Configuration

### Custom FFmpeg Path

If FFmpeg not in PATH, specify manually:

1. Edit `audio_builder.py`:
   ```python
   def _get_ffmpeg_cmd(self):
       return r"C:\path\to\ffmpeg.exe"
   ```

### FFmpeg Advanced Options

**Custom Encoding:**

Edit `audio_builder.py` → `merge_and_convert_to_m4b()`:

```python
# Add custom FFmpeg arguments
cmd.extend([
    '-movflags', '+faststart',  # Web-optimized M4B
    '-write_xing', '0',         # Disable Xing header
    '-id3v2_version', '4',      # ID3v2.4 tags
])
```

**Silence Detection:**

Remove silence from audio:
```python
cmd.extend([
    '-af', 'silenceremove=start_periods=1:start_duration=0.1:start_threshold=-50dB'
])
```

---

## Advanced Settings

### Logging Level

Increase verbosity for debugging:

1. Edit `main.py`:
   ```python
   logging.basicConfig(
       level=logging.DEBUG,  # Change from INFO
       # ...
   )
   ```

2. Restart AB-Maker
3. More detailed logs appear

### Cache Management

**Clear EPUB Cache:**
```powershell
Remove-Item -Recurse "$env:APPDATA\AB-Maker\.cache"
```

**Clear Model Downloads:**
```powershell
Remove-Item -Recurse "$env:APPDATA\AB-Maker\models"
```
Note: Will re-download on next use.

### GPU Memory Optimization

For low-VRAM GPUs, reduce batch size:

Edit `tts_engine.py`:
```python
# Reduce memory usage (default: process full chapter)
max_chunk_size = 500  # characters per chunk
```

---

## File Organization

### Recommended Structure

```
Documents/
└── AB-Maker/
    ├── Input/              # Source EPUBs
    │   ├── Fiction/
    │   ├── Non-Fiction/
    │   └── Audiobooks/     # Organized by genre
    └── Output/             # Generated audiobooks
        ├── M4B/
        └── MP3/
```

### Output Naming

Customize output filenames:

Edit `conversion_worker.py`:
```python
# Current: BookTitle_Author.m4b
# Custom: Author - BookTitle (Year).m4b
output_filename = f"{author} - {title} ({year}).m4b"
```

---

## Environment Variables

### Set via PowerShell

```powershell
# Custom models directory
$env:AB_MAKER_MODELS_DIR = "D:\TTS-Models"

# Custom output directory
$env:AB_MAKER_OUTPUT_DIR = "D:\Audiobooks"

# Enable debug mode
$env:AB_MAKER_DEBUG = "1"
```

### Make Permanent

1. Win + X → System
2. Advanced system settings
3. Environment Variables
4. User variables → New
5. Add variables above

---

## Performance Tuning

### CPU-Only Optimization

**Enable Multi-threading:**
```python
# In conversion_worker.py
import multiprocessing
pool = multiprocessing.Pool(processes=4)
```

**Note:** Experimental - may not provide speedup.

### GPU Optimization

**CUDA Performance:**
```python
# In tts_engine.py
config = {
    'provider': 'cuda',
    'num_threads': 1,        # GPU uses single thread
    'debug': 0
}
```

---

## Integration with Other Tools

### External Editors

**Custom Chapter Editor:**
```json
{
  "chapter_editor_cmd": "notepad.exe {filepath}"
}
```

### Post-Processing Scripts

**Run after conversion:**

Create `post_process.py`:
```python
import sys
audiobook_path = sys.argv[1]
# Your custom processing
```

Integrate in `conversion_worker.py`:
```python
import subprocess
subprocess.run(['python', 'post_process.py', output_path])
```

---

## Backup & Restore

### Backup Configuration

**What to backup:**
- `%APPDATA%\AB-Maker\config.json`
- `config/presets.json` (if customized)
- Downloaded models (optional, can re-download)

**Backup script:**
```powershell
$backup = "C:\AB-Maker-Backup-$(Get-Date -Format 'yyyyMMdd').zip"
Compress-Archive -Path "$env:APPDATA\AB-Maker" -DestinationPath $backup
```

### Restore Configuration

1. Close AB-Maker
2. Extract backup to `%APPDATA%\AB-Maker\`
3. Restart AB-Maker

---

## Next Steps

- 🔧 [Troubleshooting](Troubleshooting.md) - Common issues
- 🏗️ [Architecture](Architecture.md) - Technical details
- ❓ [FAQ](FAQ.md) - Frequently asked questions
