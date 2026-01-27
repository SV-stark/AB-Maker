# AB-Maker 🎧📚

**AB-Maker** is a modern, offline desktop application designed to convert EPUB e-books into high-quality chapterized audiobooks. Built with privacy and performance in mind, it leverages next-generation offline text-to-speech technology to bring your digital library to life without relying on cloud services.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.13+-yellow)
![License](https://img.shields.io/badge/License-Apache_2.0-green)

---

## ✨ Features

- **📖 Smart EPUB Parsing**: Automatically extracts chapters and cleans text from your e-books, ensuring a smooth listening experience.
- **🗣️ Offline Neural TTS**: Powered by **sherpa-onnx**, offering incredible quality VITS models that run entirely locally on your device. Zero API costs, zero data tracking.
- **🎧 Multiple Formats**:
  - **Chapterized M4B**: Creates a single professional audiobook file with chapter markers, perfect for apps like Apple Books, Audible, or Voice.
  - **Separate WAVs**: Generates individual audio files for each chapter for flexible playback.
- **⬇️ Integrated Model Manager**: Browse and download high-quality voice models directly within the app.
- **🖥️ Modern UI**: A clean, responsive interface built with Flet (Flutter for Python).

---

## 🚀 Getting Started

### Prerequisites

To use the **M4B Audiobook** feature, you must have **FFmpeg** installed and added to your system PATH.

#### 🔧 How to Install FFmpeg on Windows & Add to PATH

1.  **Download**: Go to [ffmpeg.org/download](https://ffmpeg.org/download.html) (or use a direct build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)). Download the `ffmpeg-git-full.7z` or `.zip` release build.
2.  **Extract**: Unzip the folder to a permanent location, e.g., `C:\ffmpeg`.
3.  **Add to PATH**:
    - Press `Win` key, type **"Edit the system environment variables"**, and hit Enter.
    - Click **"Environment Variables..."**.
    - Under **"System variables"**, find the `Path` variable and click **"Edit..."**.
    - Click **"New"** and paste the path to the `bin` folder inside your extracted FFmpeg folder (e.g., `C:\ffmpeg\bin`).
    - Click **OK** on all windows to save.
4.  **Verify**: Open a new Command Prompt or PowerShell and type `ffmpeg -version`. If you see version info, you're set!

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
    # Linux/Mac
    source .venv/bin/activate
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

## 🛠️ Usage

1.  **Launch AB-Maker**.
2.  **Pick an EPUB**: Click the generic upload icon or button to select your `.epub` file.
3.  **Choose a Voice**: Select a voice model from the dropdown.
    - *Note: If a model is not installed, the app will automatically download it for you (approx. 50-100MB).*
4.  **Select Format**:
    - **Separate WAV Files**: Good for legacy players.
    - **Single M4B Audiobook**: Best for modern audiobook players (supports chapters).
5.  **Convert**: Click **Start Conversion** and watch the progress bar.
6.  **Enjoy**: Find your audiobook in the new folder created next to your original EPUB.

---

## 🤝 Credits

This project stands on the shoulders of giants. A massive thank you to the open-source projects that make this possible:

- **[Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx)**: The core engine behind the offline text-to-speech capabilities. Their work on optimizing next-gen Kaldi and VITS models for on-device inference is groundbreaking.
- **[Flet](https://flet.dev/)**: For enabling the creation of beautiful, cross-platform Flutter UIs accurately with Python.
- **[EbookLib](https://github.com/aerkalov/ebooklib)** & **[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)**: For the robust parsing and processing of EPUB files.
- **[FFmpeg](https://ffmpeg.org/)**: The industry standard for multimedia handling, used here for creating chapterized M4B containers.

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
