<p align="center">
  <img src="assets/logo.svg" width="200" height="200" alt="AB-Maker Logo">
</p>

# AB-Maker 🎧📚

**AB-Maker** is a professional-grade, offline desktop application for converting EPUB e-books into high-quality chapterized audiobooks. Built with privacy, performance, and user experience in mind, it leverages cutting-edge offline TTS technology to transform your reading list into an audio library—no cloud services required.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.13+-yellow)
![License](https://img.shields.io/badge/License-AGPL_v3-blue)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

---

## ✨ Key Highlights

🔒 **100% Private** - All processing happens locally. No data leaves your machine.  
⚡ **GPU Accelerated** - 10-50x faster with NVIDIA CUDA support.  
🎨 **Professional UI** - Polished interface with comprehensive tooltips and real-time feedback.  
🌍 **Multi-Language** - English, Spanish, French, German models included.  
📦 **Batch Processing** - Convert multiple books sequentially with progress tracking.  
🛡️ **Production Ready** - Robust error handling and user-friendly error messages.

---

## 🎯 Features

### 🗣️ Advanced Audio Generation
- **Offline Neural TTS**: Powered by **sherpa-onnx** VITS models - completely offline
- **GPU Acceleration**: NVIDIA CUDA support for 10-50x speed boost
- **Speed Control**: Adjustable speaking rate (0.5x - 2.5x)
- **Audio Normalization**: EBU R128 loudness normalization for consistent volume
- **Voice Preview**: Test voice/speed settings instantly before conversion
- **Multi-Language Support**: Pre-configured models for English, Spanish, French, German

### 📖 Intelligent Book Processing
- **Batch Processing**: Convert multiple EPUBs sequentially with progress tracking
- **Smart Caching**: Auto-skips already-converted chapters on resume
- **Text Preprocessing**: Handles abbreviations (Dr. → Doctor) for natural flow
- **Chapter Editor**: View, rename, and verify chapters before conversion
- **Custom Covers**: Override EPUB covers with your own images
- **Metadata Preservation**: Maintains book title, author, and chapter information

### 🎨 Modern User Experience
- **Comprehensive Tooltips**: Every button and control has helpful descriptions
- **Real-time Progress**: Per-chapter status (Pending/Processing/Done/Cached)
- **Batch Progress Display**: Shows "Book X/Y" when converting multiple files
- **Status Tracking**: Sidebar icons show conversion history (✅ Completed, 🔄 In Progress)
- **Settings Reset**: One-click restore to default settings
- **Drag & Drop**: Import EPUBs by dragging onto the window
- **Theme Support**: Light/Dark mode with system sync
- **Recent Files**: Quick access to recently converted books

### 💾 Professional Output
- **Chapterized M4B**: Industry-standard audiobook format with chapters & cover art
- **MP3 with ID3**: Universal compatibility with full metadata and album art
- **Quality Presets**:
  - **Low** (32k) - Testing/Small files
  - **Medium** (64k) - Balanced quality/size
  - **High** (128k) - High quality for most use cases
  - **Lossless** - Perfect quality, larger files
  - **Podcast** (48k) - Voice-optimized
  - **Audible** (64k) - Audible-compatible specs

### 🏗️ Advanced Architecture
- **Event Bus System**: Decoupled component communication
- **Dependency Injection**: Testable, flexible architecture
- **Custom Exceptions**: Specific error types (ModelDownloadError, TTSGenError, FFmpegError)
- **FFmpeg Error Parser**: Converts cryptic errors to user-friendly messages
- **Externalized Config**: JSON-based quality presets for easy customization
- **Abstract Base Classes**: Extensible TTS engine interface

---

## 🚀 Getting Started

### Prerequisites

**Required:**
- Windows 10/11 (x64)
- Python 3.13+
- FFmpeg (for M4B/MP3 output)

**Optional:**
- NVIDIA GPU + CUDA Toolkit (for GPU acceleration)

### 🔧 FFmpeg Installation (Required for M4B/MP3)

1. **Download**: [ffmpeg.org/download](https://ffmpeg.org/download.html) or [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
2. **Extract**: Unzip to `C:\ffmpeg`
3. **Add to PATH**:
   - Search → "Edit the system environment variables"
   - Environment Variables → System variables → Path → New
   - Add: `C:\ffmpeg\bin`
4. **Verify**: Run `ffmpeg -version` in CMD/PowerShell

### 📥 Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/AB-Maker.git
   cd AB-Maker
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run**:
   ```bash
   python main.py
   ```

---

## ⚡ GPU Acceleration (Optional)

Achieve **10-50x faster conversions** with NVIDIA GPU support.

### Requirements
- NVIDIA GPU (GeForce/RTX series)
- Windows 10/11 (x64)

### Setup

1. **Install CUDA Toolkit 12.x**: [NVIDIA Developer](https://developer.nvidia.com/cuda-downloads)
2. **Install cuDNN 9.x (for CUDA 12)**: [NVIDIA Developer](https://developer.nvidia.com/cudnn)
   - Requires free NVIDIA Developer account
3. **Setup cuDNN**:
   - Extract cuDNN zip
   - Copy `bin`, `include`, `lib` to CUDA directory:  
     `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x`
4. **Install zlibwapi.dll**:
   - Download from [WinImage](http://www.winimage.com/zLibDll/)
   - Place in `C:\Windows\System32` or CUDA `bin` folder

### Verify
1. Launch AB-Maker
2. Enable **🚀 GPU** toggle
3. Check logs: "TTS Model initialized" = GPU working ✅
   - If "Falling back to CPU" appears, check PATH and DLL locations

---

## 🎯 Quick Start Guide

1. **Launch** `python main.py`
2. **Import EPUB**: Drag & drop or click Browse
3. **Select Voice**:
   - Choose model (auto-downloads first time)
   - Adjust speed slider (hover for tooltip)
   - Click Preview to test
   - Enable GPU if available
4. **Configure Output**:
   - Format: M4B (recommended) or MP3
   - Quality: Medium (default) or customize
   - Optional: Enable Normalize
   - Optional: Select custom cover image
5. **Convert**: Click "⚡ START CONVERSION"
   - Watch real-time chapter progress
   - Cancel anytime with STOP button

### 💡 Pro Tips
- **Batch Processing**: Select multiple EPUBs for sequential conversion
- **Resume Capability**: Smart caching skips completed chapters if interrupted
- **Settings Reset**: Click "↺ Reset" to restore defaults
- **Status Tracking**: Sidebar shows ✅ for completed books
- **Error Messages**: User-friendly explanations for common issues

---

## 🏗️ Architecture

```
AB-Maker/
├── core/                  # Core utilities
│   ├── event_bus.py      # Pub-sub event system
│   ├── base_tts.py       # TTS engine ABC
│   └── ffmpeg_errors.py  # Error parser
├── ui/                    # UI components
│   ├── app.py            # Main application
│   ├── book_card.py      # Book input section
│   ├── voice_card.py     # Voice settings
│   ├── action_card.py    # Conversion controls
│   ├── sidebar.py        # Recent files & theme
│   └── tooltip.py        # Tooltip utility
├── config/
│   └── presets.json      # Quality presets
├── audio_builder.py      # FFmpeg integration
├── tts_engine.py         # TTS wrapper
├── conversion_worker.py  # Conversion logic
├── epub_processor.py     # EPUB parsing
└── config_manager.py     # Settings persistence
```

---

## 🛠️ Customization

### Quality Presets
Edit `config/presets.json` to add custom quality profiles:
```json
{
  "Custom": {
    "bitrate": "96k",
    "channels": "2",
    "sample_rate": "48000",
    "description": "My custom preset"
  }
}
```

### Adding TTS Models
1. Download ONNX models from [sherpa-onnx models](https://github.com/k2-fsa/sherpa-onnx/releases)
2. Place in `%APPDATA%\AB-Maker\models\`
3. Refresh model list in app

---

## 🐛 Troubleshooting

### "FFmpeg not found"
**Solution**: Install FFmpeg and add to PATH (see installation steps above)

### "Permission denied" error
**Solution**: Run as administrator or change output folder to user directory

### "Out of disk space"
**Solution**: Free up space or change output folder. Each hour of audio ≈ 50-100MB

### GPU not working
**Solutions**:
- Verify CUDA Toolkit installed correctly
- Ensure `zlibwapi.dll` and `cudnn64_*.dll` are in PATH
- Update NVIDIA drivers
- Check logs for specific errors

### "Audio file is too large"
**Solution**: Use a lower quality preset (Medium instead of High)

---

## 🤝 Credits

Built with excellent open-source tools:

- **[Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx)** - Next-gen offline TTS
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Modern Python UI framework
- **[EbookLib](https://github.com/aerkalov/ebooklib)** - EPUB parsing
- **[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)** - HTML processing
- **[FFmpeg](https://ffmpeg.org/)** - Media encoding
- **[sounddevice](https://python-sounddevice.readthedocs.io/)** - Audio playback

---

## 📊 Project Stats

- **Lines of Code**: ~3,500
- **Components**: 15+ modular components
- **Error Handling**: 10+ friendly error patterns
- **UI Elements**: 18 tooltips across interface
- **Quality Presets**: 6 built-in profiles
- **Supported Languages**: 4+ TTS models

---

## 🔮 Roadmap

- [ ] Checkpoint system for resume from failed conversions
- [ ] Additional TTS backends (Piper, Coqui-TTS)
- [ ] MacOS/Linux support
- [ ] Voice cloning integration
- [ ] Web UI option
- [ ] Comprehensive test suite

---

## 📄 License

GNU Affero General Public License v3.0 - see [LICENSE](LICENSE) for details.

---

## 💬 Support

For issues, feature requests, or questions:
- 🐛 [GitHub Issues](https://github.com/your-username/AB-Maker/issues)
- 📖 [Documentation Wiki](https://github.com/your-username/AB-Maker/wiki)

---

**Made with ❤️ for audiobook enthusiasts who value privacy and quality.**
