# Troubleshooting Guide

Solutions to common issues and error messages.

---

## Installation Issues

### Python Not Found

**Error:** `'python' is not recognized as an internal or external command`

**Solutions:**
1. Install Python 3.13+ from [python.org](https://python.org)
2. During install, check **"Add Python to PATH"**
3. Restart terminal/PowerShell
4. Verify: `python --version`

**Alternative:**
- Use `py` instead of `python`: `py main.py`

### FFmpeg Not Found

**Error:** `WARNING: FFmpeg not found! M4B/MP3 output may fail.`

**Solutions:**
1. Install FFmpeg (see [Getting Started](Getting-Started.md#ffmpeg))
2. Add to PATH
3. Restart terminal/PowerShell
4. Verify: `ffmpeg -version`

**Quick fix:**
```powershell
# Using Chocolatey
choco install ffmpeg

# Restart PowerShell, then test
ffmpeg -version
```

### Dependency Installation Fails

**Error:** `ERROR: Could not find a version that satisfies the requirement...`

**Solutions:**
1. Update pip:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Install dependencies one-by-one:
   ```bash
   pip install customtkinter
   pip install sherpa-onnx
   # etc.
   ```

3. Check Python version:
   ```bash
   python --version
   # Should be 3.13+
   ```

---

## GPU Issues

### GPU Not Working

**Symptoms:**
- Log shows "Falling back to CPU"
- Conversion not faster with GPU enabled
- No speedup from GPU toggle

**Solutions:**

#### 1. Verify CUDA Installation
```powershell
nvidia-smi
# Should show GPU info
```

If this fails:
- Install NVIDIA GPU drivers
- Install CUDA Toolkit 12.x
- Restart computer

#### 2. Check cuDNN Installation
Verify these files exist:
- `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin\cudnn64_9.dll`
- `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin\cudnn_ops_infer64_9.dll`

If missing:
- Download cuDNN 9.x
- Extract and copy to CUDA folder

#### 3. Install zlibwapi.dll
Check for:
- `C:\Windows\System32\zlibwapi.dll`
- OR `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin\zlibwapi.dll`

If missing:
- Download from [WinImage](http://www.winimage.com/zLibDll/)
- Extract and copy to System32

#### 4. Verify PATH
```powershell
$env:PATH
# Should include CUDA bin folder
```

Add if missing:
- `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin`

#### 5. Check Logs
Look for specific error in AB-Maker logs:
- `Failed to load library: cudnn64_9.dll` → cuDNN issue
- `Failed to load library: zlibwapi.dll` → Missing zlib
- `CUDA error` → Driver/CUDA problem

### GPU Out of Memory

**Error:** `CUDA out of memory`

**Solutions:**
1. Close other GPU applications
2. Reduce chapter size (edit EPUB, split chapters)
3. Use CPU mode instead
4. Upgrade GPU (needs more VRAM)

---

## Conversion Errors

### "Audio file is too large"

**Full Error:** `Audio file is too large. Try using a lower quality preset.`

**Cause:** FFmpeg buffer size exceeded (rare)

**Solutions:**
1. Use lower quality: High → Medium → Low
2. Split EPUB into smaller files
3. Convert to MP3 instead of M4B

### "The audio file is corrupted"

**Full Error:** `The audio file is corrupted or in an unsupported format.`

**Cause:** Generated WAV file is invalid

**Solutions:**
1. Delete chapter WAV files in output folder
2. Restart conversion (will regenerate)
3. Try different TTS model
4. Check disk space (may be full)

### "Permission denied"

**Full Error:** `Don't have permission to write to output folder.`

**Solutions:**
1. Run AB-Maker as administrator (right-click → Run as admin)
2. Change output folder to user directory:
   - Click Output Folder button
   - Select: `C:\Users\YourName\Documents\Audiobooks`
3. Check folder permissions (shouldn't be read-only)

### "Out of disk space"

**Full Error:** `Out of disk space. Please free up some space and try again.`

**Cause:** Not enough storage for conversion

**Solutions:**
1. Free up disk space
2. Change output to different drive with more space
3. Delete old audiobooks
4. Use lower quality (smaller files)

**Space Requirements:**
- ~50-100 MB per hour of audio (Medium quality)
- Temporary WAV files: 2-5x larger (auto-deleted after merge)

### Conversion Stuck

**Symptoms:**
- Progress frozen
- No log activity
- Chapter stuck in "Processing..."

**Solutions:**

1. **Wait:** Complex chapters can take time (5-10 min+)

2. **Check Logs:** Look for errors
   - TTS timeout
   - Memory error
   - File access issue

3. **Cancel & Restart:**
   - Click STOP button
   - Wait for graceful shutdown
   - Restart conversion
   - Cached chapters will be skipped

4. **Problematic Chapter:**
   - Edit chapter in EPUB
   - Simplify overly complex formatting
   - Remove special characters

### Chapter Failed (❌)

**Symptoms:**
- Specific chapter shows ❌ Failed
- Other chapters complete successfully

**Solutions:**
1. Check logs for error message
2. Common causes:
   - Empty chapter → Edit EPUB, add content
   - Encoding error → Re-save EPUB as UTF-8
   - TTS timeout → Reduce chapter length
3. Delete failed chapter WAV file
4. Retry conversion

---

## Model Issues

### Model Download Fails

**Error:** `Failed to download model: Connection timeout`

**Solutions:**
1. Check internet connection
2. Disable firewall/antivirus temporarily
3. Manual download:
   - Get model from [sherpa-onnx releases](https://github.com/k2-fsa/sherpa-onnx/releases)
   - Extract to `%APPDATA%\AB-Maker\models\`
4. Retry in AB-Maker

### Model Won't Load

**Error:** `Failed to initialize TTS engine`

**Solutions:**
1. Verify model files exist:
   - `model.onnx`
   - `tokens.txt`
2. Re-download model (delete and re-select)
3. Check file permissions
4. Try different model

### Model List Empty

**Symptoms:**
- Model dropdown is empty
- "Show All Models" doesn't help

**Solutions:**
1. Click **⚙️ Manage Models**
2. Download at least one model
3. Refresh model list (F5)
4. Restart AB-Maker

---

## Audio Quality Issues

### Audio Sounds Distorted

**Solutions:**
1. Enable **Normalize** option
2. Use higher quality preset
3. Try different TTS model
4. Reduce speed (closer to 1.0x)

### Audio Too Quiet/Loud

**Solutions:**
1. Enable **Normalize** option (recommended)
2. Adjust in audio player instead
3. Re-convert with normalization enabled

### Robotic/Unnatural Voice

**Solutions:**
1. Reduce speed (try 0.9x or 0.8x)
2. Try different TTS model
3. Test different Speaker ID
4. Some models are better than others

### Volume Varies Between Chapters

**Cause:** Normalization disabled

**Solution:**
1. Enable **Normalize** checkbox
2. Re-convert book

---

## File/Format Issues

### M4B Not Playing

**Symptoms:**
- File won't open
- No chapters visible
- Crashes player

**Solutions:**
1. Verify FFmpeg installed correctly
2. Check M4B file size (should be > 1 MB)
3. Try different player:
   - VLC Media Player
   - Apple Books
   - Bound Audiobook Player
4. Convert to MP3 instead
5. Check conversion logs for FFmpeg errors

### MP3 Missing Metadata

**Symptoms:**
- No title/author in player
- No album art
- Wrong chapter names

**Solutions:**
1. Verify EPUB has metadata
2. Check if custom cover provided
3. Re-convert with updated EPUB
4. Manually add tags with MP3Tag

### Cover Art Not Showing

**Solutions:**
1. Verify image file is valid (JPG/PNG)
2. Image size reasonable (< 5 MB, > 500x500px)
3. Use square aspect ratio
4. Try different image format
5. Re-convert with new cover

---

## UI/Application Issues

### App Won't Start

**Error:** `ModuleNotFoundError: No module named 'customtkinter'`

**Solutions:**
1. Activate virtual environment:
   ```bash
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Verify Python version (3.13+)

### App Crashes

**Symptoms:**
- Sudden close
- No error message
- Logs show exception

**Solutions:**
1. Check logs in `%APPDATA%\AB-Maker\logs\`
2. Report issue with log file
3. Restart with clean config:
   ```powershell
   Remove-Item "$env:APPDATA\AB-Maker\config.json"
   ```

### Tooltips Not Showing

**Cause:** Mouse movement too fast, or delay not triggered

**Solutions:**
1. Hover longer (500ms delay)
2. Move mouse slower
3. Verify tooltip system working:
   - Hover over any button
   - Wait 1 second
   - Tooltip should appear

### Theme Not Changing

**Solutions:**
1. Toggle Dark Mode switch in sidebar
2. Restart AB-Maker
3. Check system theme settings

---

## Performance Issues

### Conversion Very Slow

**Without GPU:**
- **Expected:** 1-5 min per 1000 words
- **Slow if:** > 10 min per 1000 words

**Solutions:**
1. Enable GPU if available (10-50x speedup!)
2. Close other applications
3. Use SSD for output folder
4. Lower quality (slightly faster encoding)

**With GPU:**
- **Expected:** 5-30 sec per 1000 words
- **Slow if:** Same as CPU speed

**Solutions:**
- See [GPU Not Working](#gpu-not-working)
- Verify GPU actually being used (check logs)

### High Memory Usage

**Symptoms:**
- RAM usage > 4 GB
- System slowdown
- Out of memory errors

**Solutions:**
1. Convert smaller books
2. Reduce batch size (1 book at a time)
3. Close other applications
4. Add more RAM (if persistent issue)

---

## Common Error Messages

### "Model download failed: HTTP 404"

**Meaning:** Model URL invalid or file moved

**Solution:** Report issue - model repository changed

### "Failed to parse EPUB"

**Meaning:** EPUB file corrupted or non-standard

**Solutions:**
1. Verify EPUB opens in e-reader (Calibre)
2. Re-download EPUB
3. Convert EPUB with Calibre
4. Try different EPUB file

### "Chapter contains no text"

**Meaning:** Chapter is empty or only images

**Solutions:**
1. Open EPUB in editor
2. Verify chapter has text content
3. Skip empty chapters manually
4. Edit chapter titles to mark as "[Skip]"

---

## Getting Help

If issue not covered here:

1. **Check Logs:**
   - Bottom of AB-Maker window
   - `%APPDATA%\AB-Maker\logs\app.log`

2. **Search Issues:**
   - [GitHub Issues](https://github.com/your-username/AB-Maker/issues)

3. **Report Bug:**
   - Include: Error message, logs, OS version, Python version
   - Steps to reproduce
   - EPUB file (if shareable)

4. **Community:**
   - [GitHub Discussions](https://github.com/your-username/AB-Maker/discussions)

---

## Next Steps

- 📖 [User Guide](User-Guide.md) - Usage instructions
- ⚙️ [Configuration](Configuration.md) - Advanced settings
- ❓ [FAQ](FAQ.md) - Common questions
