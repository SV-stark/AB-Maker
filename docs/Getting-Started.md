# Getting Started with AB-Maker

This guide will help you install and set up AB-Maker for the first time.

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB
- **Storage**: 2 GB free space (for app + models)
- **Python**: 3.13 or higher

### Recommended Requirements
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB or more
- **Storage**: 5 GB free space
- **GPU**: NVIDIA GPU with CUDA support (for acceleration)

---

## Installation Steps

### 1. Install Prerequisites

#### Python 3.13+
1. Download from [python.org](https://www.python.org/downloads/)
2. During installation, check **"Add Python to PATH"**
3. Verify: Open PowerShell and run `python --version`

#### FFmpeg (Required for M4B/MP3)
FFmpeg is required for creating M4B and MP3 files.

**Quick Install:**
```powershell
# Using Chocolatey (recommended)
choco install ffmpeg

# Or using Scoop
scoop install ffmpeg
```

**Manual Install:**
1. Download from [ffmpeg.org/download](https://ffmpeg.org/download.html)
   - Or use [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/) (easier)
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Press `Win + X` → System → Advanced system settings
   - Environment Variables → System Variables → Path → Edit
   - New → Add `C:\ffmpeg\bin`
   - OK → OK → OK
4. **Verify**: Open new PowerShell window
   ```powershell
   ffmpeg -version
   # Should show FFmpeg version info
   ```

### 2. Install AB-Maker

#### Option A: From Source (Recommended)

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/AB-Maker.git
   cd AB-Maker
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run AB-Maker**:
   ```bash
   python main.py
   ```

#### Option B: Standalone Executable (Coming Soon)
Pre-built executables will be available in future releases.

---

## GPU Acceleration Setup (Optional)

For **10-50x faster conversions**, enable GPU support.

### Prerequisites
- NVIDIA GPU (GTX/RTX series)
- Windows 10/11 64-bit

### Installation

#### 1. Install CUDA Toolkit 12.x

1. Visit [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads)
2. Select:
   - Operating System: Windows
   - Architecture: x86_64
   - Version: Your Windows version
   - Installer Type: exe (local)
3. Download and run installer (~3 GB)
4. Follow installation wizard (default options work)

#### 2. Install cuDNN 9.x

1. Visit [NVIDIA cuDNN](https://developer.nvidia.com/cudnn)
   - Requires free NVIDIA Developer account
2. Download cuDNN v9.x for CUDA 12.x
3. Extract the zip file
4. Copy files to CUDA directory:
   ```
   From cuDNN zip:           To CUDA folder:
   bin\*.dll           →     C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin\
   include\*.h         →     C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\include\
   lib\*.lib           →     C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\lib\x64\
   ```

#### 3. Install zlibwapi.dll

cuDNN requires this Windows library:

1. Download from [WinImage zLib DLL](http://www.winimage.com/zLibDll/)
2. Extract `zlibwapi.dll`
3. Copy to one of:
   - `C:\Windows\System32\` (recommended)
   - OR `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin\`

#### 4. Verify GPU Setup

1. Open PowerShell and run:
   ```powershell
   nvidia-smi
   # Should show GPU info
   ```

2. Launch AB-Maker:
   ```bash
   python main.py
   ```

3. In AB-Maker:
   - Toggle **🚀 GPU** switch ON
   - Start a conversion
   - Check logs at bottom of window

**Success indicators:**
- Log shows: `TTS Model initialized` (no "Falling back to CPU")
- Conversion is noticeably faster

**If GPU doesn't work:**
- See [Troubleshooting GPU Issues](Troubleshooting.md#gpu-not-working)

---

## First Launch

### Initial Setup

1. **Launch AB-Maker**:
   ```bash
   cd AB-Maker
   .venv\Scripts\activate  # If using venv
   python main.py
   ```

2. **Model Download**:
   - First time: App will download default TTS model (~50-200 MB)
   - Models are stored in: `%APPDATA%\AB-Maker\models\`
   - Download happens automatically when you select a model

3. **Interface Overview**:
   - **Left Sidebar**: Recent files, theme toggle
   - **Book & Cover**: EPUB selection, cover customization
   - **Voice Strategy**: Model selection, speed, GPU
   - **Action Controls**: Format, quality, start/stop
   - **Progress**: Real-time conversion status
   - **Logs**: Detailed operation logs

---

## Quick Test

Let's convert your first audiobook!

1. **Get a Test EPUB**:
   - Use any EPUB file you own
   - Or download a free book from [Project Gutenberg](https://www.gutenberg.org/)

2. **Import Book**:
   - Drag EPUB onto AB-Maker window
   - OR click **Browse** button

3. **Select Voice**:
   - Choose model (e.g., "English - Female")
   - Click **Preview** to test voice

4. **Configure Output**:
   - Format: **M4B** (recommended)
   - Quality: **Medium**
   - Enable: **Normalize**

5. **Convert**:
   - Click **⚡ START CONVERSION**
   - Watch progress in "Detailed Progress" section
   - Audio saved to `Documents\AB-Maker-Output\`

---

## Next Steps

- 📖 [User Guide](User-Guide.md) - Detailed usage instructions
- ⚙️ [Configuration](Configuration.md) - Customize settings
- ❓ [FAQ](FAQ.md) - Common questions

---

## Getting Help

- 🐛 [Report Issues](https://github.com/your-username/AB-Maker/issues)
- 📖 [Troubleshooting Guide](Troubleshooting.md)
- 💬 [Community Discussions](https://github.com/your-username/AB-Maker/discussions)
