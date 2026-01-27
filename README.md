# AB-Maker 🎧📚

**AB-Maker** is a modern, offline desktop application designed to convert EPUB e-books into high-quality chapterized audiobooks. Built with privacy and performance in mind, it leverages next-generation offline text-to-speech technology to bring your digital library to life without relying on cloud services.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.13+-yellow)
![License](https://img.shields.io/badge/License-Apache_2.0-green)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## ✨ Features

### 🎧 Core Audio Generation
- **🗣️ Offline Neural TTS**: Powered by **sherpa-onnx** VITS models. Runs entirely locally—zero API costs, zero tracking.
- **⚡ GPU Acceleration**: Utilize your NVIDIA GPU (CUDA) for blazing-fast audiobook generation.
- **⏩ Speed Control**: Adjustable speaking rate (0.5x to 2.5x).
- **👥 Multi-Speaker Support**: Select specific speaker IDs for multi-voice models (e.g., LibriTTS).

### 📖 Book Processing
- **📂 Batch Processing**: Select multiple EPUB files at once for sequential conversion.
- **⏯️ Smart Resume**: Automatically skips already-converted chapters if you restart a conversion.
- **👁️ Chapter Editor**: View and rename chapters before conversion to ensure perfect metadata.
- **📁 Custom Output**: Choose exactly where to save your generated audiobooks.

### 🎛️ Modern UI & Usability
- **🌗 Dark Mode**: Toggle between Light and Dark themes for comfortable viewing.
- **🖱️ Drag & Drop**: Simply drag EPUB files onto the window to import them.
- **🕒 History**: Quickly access your recently converted files.
- **⏳ ETA**: Real-time estimation of audio duration and conversion time.
- **🔈 Voice Preview**: Listen to a sample of the selected voice/speed before committing.

### 💾 Output Formats
- **Chapterized M4B**: Single professional audiobook file with chapters (Best for Apple Books, Audible, etc.).
- **Separate MP3s**: Space-saving, universally compatible files.
- **Separate WAVs**: Lossless quality for archiving.

---

## 🚀 Getting Started

### Prerequisites

To use **M4B** or **MP3** features, you must have **FFmpeg** installed and added to your system PATH.

#### 🔧 How to Install FFmpeg on Windows & Add to PATH

1.  **Download**: Go to [ffmpeg.org/download](https://ffmpeg.org/download.html) (or use a direct build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)). Download the release build (`.zip` or `.7z`).
2.  **Extract**: Unzip to a permanent location (e.g., `C:\ffmpeg`).
3.  **Add to PATH**:
    - Search Start Menu for **"Edit the system environment variables"**.
    - Click **"Environment Variables..."**.
    - Under **"System variables"**, edit `Path` -> **"New"** -> Paste `C:\ffmpeg\bin`.
    - Click **OK**.
4.  **Verify**: Open CMD/PowerShell and type `ffmpeg -version`.

### 📥 Running from Source

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/AB-Maker.git
    cd AB-Maker
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the App**:
    ```bash
    python main.py
    ```

---

## 🚀 Enabling GPU Acceleration (Optional)

To achieve **10x-50x faster conversions**, you can enable NVIDIA GPU support.

### 1. Requirements
- **NVIDIA GPU** (GeForce/RTX etc.) with updated drivers.
- **Windows 10/11** (x64).

### 2. Install CUDA & cuDNN
AB-Maker requires specific dynamic libraries to unlock the GPU:

1.  **Download CUDA Toolkit 12.x**: [NVIDIA Developer](https://developer.nvidia.com/cuda-downloads)
2.  **Download cuDNN 9.x (for CUDA 12)**: [NVIDIA Developer](https://developer.nvidia.com/cudnn)
    -   *Note: Requires a free NVIDIA Developer account.*
3.  **Setup**:
    -   Install CUDA Toolkit.
    -   Extract the cuDNN zip file.
    -   Copy the contents of `bin`, `include`, and `lib` from the extracted cuDNN folder into your CUDA installation directory (usually `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x`).
    -   **Important**: Ensure `zlibwapi.dll` is available in your PATH (required by cuDNN on Windows). Download it from [WinImage](http://www.winimage.com/zLibDll/index.html) and place the dll in `C:\Windows\System32` or your CUDA `bin` folder.

### 3. Verify
1.  Run AB-Maker.
2.  Toggle the **🚀 GPU** switch in the UI.
3.  Start a conversion.
    -   Check the log. If you see `TTS Model initialized` without fallback warnings, you are on GPU!
    -   If you see `Falling back to CPU`, double-check your PATH and ensure `zlibwapi.dll` and `cudnn64_*.dll` are accessible.

---

## 🛠️ Usage

1.  **Launch AB-Maker**.
2.  **Import Book**: Drag & drop an EPUB or click **Pick EPUB(s)**.
3.  **Configure Voice**:
    - Select a model from the dropdown (auto-downloads if missing).
    - (Optional) Adjust **Speed** or **Speaker ID**.
    - Click **Preview** to test.
    - (Optional) Enable **GPU (CUDA)** switch for speed (requires CUDA drivers).
4.  **Configure Output**:
    - Select Format: **M4B**, **MP3**, or **WAV**.
    - (Optional) Click **View/Edit Chapters** to verify chapter names.
    - (Optional) Select a **Output Folder**.
5.  **Convert**: Click **Start Conversion**.
    - *Tip: You can cancel at any time, and Smart Resume will pick up where you left off next time.*

---

## 🤝 Credits

This project stands on the shoulders of giants:
- **[Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx)**: Next-gen offline TTS engine.
- **[eSpeak-NG](https://github.com/espeak-ng/espeak-ng)**: Phoneme data for Piper voice models.
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)**: Modern UI framework for Python.
- **[EbookLib](https://github.com/aerkalov/ebooklib)** & **[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)**: EPUB parsing.
- **[FFmpeg](https://ffmpeg.org/)**: Media encoding.

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
