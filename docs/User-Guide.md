# AB-Maker User Guide

Complete guide to using AB-Maker for converting EPUBs to audiobooks.

---

## Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────────┐
│  AB-Maker 🎧                                  [- □ ✕]  │
├──────────┬──────────────────────────────────────────────┤
│          │  📚 BOOK & COVER                             │
│ Recent   │  [Browse] [Edit Chapters] [📷] [🗑️] [📁]    │
│ Files    │  ┌──────────────────────────────────────┐   │
│          │  │  Selected: my-book.epub               │   │
│ ✅ book1 │  └──────────────────────────────────────┘   │
│ 🔄 book2 │                                              │
│          │  🗣️ VOICE STRATEGY                          │
│ [Theme]  │  [Model▼] [▶️] Speaker:0 Speed:█1.0x 🚀GPU  │
│          │  [Show All] [⚙️Manage]                       │
│          │                                              │
│          │  ⚙️ OUTPUT                                   │
│          │  ⚪M4B ⚪MP3  Quality:[Medium▼] ☑Normalize  │
│          │  [↺Reset] [⚡START CONVERSION]  [STOP]      │
│          │                                              │
│          │  ━━━━━━━━━━━ 45% ━━━━━━━━━━                │
│          │  Processing chapter 9/20  --:-- remaining    │
│          │                                              │
│          │  📊 Detailed Progress                        │
│          │  1. Chapter One          Done ✅             │
│          │  2. Chapter Two          Processing... 🔄    │
│          │                                              │
│          │  📜 LOGS                                     │
│          │  [Chapter 2] Generating audio...             │
└──────────┴──────────────────────────────────────────────┘
```

### Tooltips
Hover over any button or control to see helpful tooltips explaining its function.

---

## Basic Workflow

### 1. Select Your Book

**Method A: Drag & Drop**
- Drag EPUB file from File Explorer
- Drop onto AB-Maker window
- Book info loads automatically

**Method B: Browse Button**
1. Click **Browse** button (or folder icon)
2. Navigate to EPUB file
3. Click Open

**Batch Selection:**
- Hold `Ctrl` while selecting multiple EPUBs
- They'll convert sequentially
- Progress shows "Book X/Y"

### 2. Review Chapters (Optional)

1. Click **📋 Edit Chapters** button
2. Chapter editor window opens
3. Review chapter titles
4. Edit if needed (e.g., fix "Chapter001" → "Chapter 1")
5. Click Save

**Why edit chapters?**
- Chapter titles appear in M4B metadata
- Easier navigation in audiobook players
- Professional appearance

### 3. Choose Voice Settings

#### Select Model

1. Click **Model** dropdown
2. Choose from available models:
   - **English - Female** (vits-vctk)
   - **English - Male** (vits-ljs)
   - **Multilingual** (can handle multiple languages)
3. First selection triggers auto-download (~50-200 MB)
4. Download progress shown in logs

**Show All Models:**
- Toggle to see all available models
- Default shows only recommended models

**Manage Models:**
1. Click **⚙️ Manage** button
2. Download additional models
3. Delete unused models to save space

#### Adjust Speed

- Default: **1.0x** (normal speed)
- Range: **0.5x - 2.5x**
- Drag slider to adjust
- Tooltip shows current value

**Recommendations:**
- 0.8x - Slower, clearer (for dense content)
- 1.0x - Natural reading speed
- 1.5x - Faster listening (saves time)
- 2.0x+ - Speed listening (experienced users)

#### Speaker ID

- Default: **0**
- Some models have multiple voices (0, 1, 2, etc.)
- Test different IDs to find preferred voice
- Use **Preview** to compare

#### GPU Acceleration

- Toggle **🚀 GPU** switch
- Requires NVIDIA GPU + CUDA setup
- 10-50x speed boost
- Logs show "GPU initialized" if working

**Without GPU:**
- Still works! Just slower
- ~1-5 min per 1000 words
- CPU-only mode is reliable

**With GPU:**
- Much faster! 
- ~5-30 sec per 1000 words
- Great for large books

### 4. Test Your Voice

1. Click **▶️ Preview** button
2. Sample audio plays
3. Test text: "Hello, this is a preview..."
4. Adjust settings if needed
5. Preview again

**Preview Tips:**
- Test before starting long conversions
- Verify speed feels right
- Check voice quality
- Ensure GPU is working (faster preview)

### 5. Configure Output

#### Choose Format

**M4B (Recommended)**
- Professional audiobook format
- Single file with chapters
- Cover art embedded
- Compatible with Apple Books, Audible app
- Seekable chapters

**MP3**
- Universal compatibility
- One file per chapter
- ID3 tags + cover art
- Works everywhere
- Larger total size

#### Select Quality

| Preset | Bitrate | Best For |
|--------|---------|----------|
| **Low** | 32k | Testing, small files |
| **Medium** | 64k | **Recommended** - Good quality/size |
| **High** | 128k | High quality audio |
| **Lossless** | FLAC | Perfect quality, large files |
| **Podcast** | 48k | Voice-optimized |
| **Audible** | 64k | Audible-compatible |

**Recommendations:**
- Start with **Medium**
- Only use Lossless if archiving
- Low is good for testing

#### Normalize Audio

- Toggle **Normalize** checkbox
- Uses EBU R128 loudness normalization
- Ensures consistent volume across chapters
- **Recommended** for most books

**Why normalize?**
- Prevents volume jumps between chapters
- Professional sound
- Better listening experience

### 6. Start Conversion

1. Review all settings
2. Click **⚡ START CONVERSION**
3. Watch progress:
   - Overall progress bar
   - Current chapter status
   - Detailed chapter list
   - Logs at bottom
4. Cancel anytime with **STOP** button

**What Happens:**
1. Model loads (if not already loaded)
2. EPUB parsed into chapters
3. Each chapter converted to audio
4. Audio files merged (M4B) or tagged (MP3)
5. Metadata and cover added
6. Output saved to output folder

**Progress Indicators:**
- 🟦 **Pending** - Waiting to process
- 🔄 **Processing...** - Currently converting
- ✅ **Done** - Successfully completed
- 💾 **Cached** - Already converted (skipped)
- ❌ **Failed** - Error occurred

### 7. Access Your Audiobook

**Default Location:**
```
C:\Users\YourName\Documents\AB-Maker-Output\
```

**Custom Location:**
- Click **📁 Output Folder** button
- Select preferred location
- Apply to all future conversions

**File Naming:**
```
M4B: BookTitle_Author.m4b
MP3: BookTitle_Author/001_ChapterTitle.mp3
```

---

## Advanced Features

### Batch Processing

Convert multiple books sequentially:

1. Select multiple EPUBs (Ctrl+Click)
2. Configure settings (apply to all)
3. Start conversion
4. Status shows "Book 1/3", "Book 2/3", etc.
5. Each book processes completely before next

**Features:**
- Automatic queue management
- Per-book progress tracking
- Pause/resume capability
- Status icons in sidebar

### Smart Caching

AB-Maker remembers completed chapters:

**Benefits:**
- Resume interrupted conversions
- Skip already-done chapters
- Saves processing time
- Cached chapters marked 💾

**How It Works:**
1. Each chapter saved as WAV file
2. On restart, existing files checked
3. Valid files skipped
4. Only missing/corrupted chapters regenerated

**Clear Cache:**
Delete WAV files in output folder to force regeneration.

### Custom Covers

Override EPUB cover with your own image:

1. Click **📷 Select Cover** button
2. Choose image (JPG, PNG, WebP)
3. Image embedded in output
4. Clear anytime with **🗑️ Clear Cover**

**Recommendations:**
- Square images work best (1:1 ratio)
- Min: 500x500px
- Max: 3000x3000px
- JPG or PNG format

### Settings Reset

Made changes and want defaults back?

1. Click **↺ Reset** button
2. All settings restore:
   - Speed: 1.0x
   - Format: M4B
   - Quality: Medium
   - Normalize: Off
   - GPU: Off
   - Speaker: 0

**Note:** Doesn't affect selected book or output folder.

### Recent Files

Left sidebar shows recently converted books:

- ✅ **Completed** - Successfully converted
- 🔄 **In Progress** - Currently converting
- Click filename to reload book

**Clear Recent:**
Recent files list in: `%APPDATA%\AB-Maker\config.json`

---

## Tips & Tricks

### Performance Optimization

**Faster Conversions:**
1. Enable GPU if available (biggest speedup!)
2. Use lower quality for drafts
3. Close other applications
4. Use SSD for output folder

**Reduce File Size:**
1. Lower quality preset (Medium → Low)
2. Disable normalization (slightly smaller)
3. Use MP3 instead of M4B
4. Mono audio vs stereo (check preset)

### Quality Tips

**Better Audio:**
1. Use **High** or **Lossless** quality
2. Enable normalization
3. Test multiple speaker IDs
4. Adjust speed for naturalness

**Metadata Quality:**
1. Edit chapter titles before conversion
2. Use custom cover for branding
3. EPUB metadata auto-populated

### Troubleshooting During Conversion

**Conversion Stuck?**
- Check logs for errors
- Click STOP and restart
- Try lower quality
- Check disk space

**Chapter Failed?**
- Specific chapter shows ❌
- Check logs for error message
- Usually: text encoding issue or TTS error
- Delete WAV file and retry

**FFmpeg Errors?**
- Ensure FFmpeg in PATH
- Try different quality preset
- Check output folder permissions

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open EPUB |
| `Ctrl+S` | Start Conversion |
| `Ctrl+Q` | Quit |
| `F5` | Refresh Model List |
| `Ctrl+L` | Clear Logs |
| `Ctrl+,` | Open Settings (future) |

---

## Next Steps

- ⚙️ [Configuration Guide](Configuration.md) - Advanced customization
- 🔧 [Troubleshooting](Troubleshooting.md) - Fix common issues
- ❓ [FAQ](FAQ.md) - Frequently asked questions
