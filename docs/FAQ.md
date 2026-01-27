# Frequently Asked Questions (FAQ)

Quick answers to common questions about AB-Maker.

---

## General Questions

### What is AB-Maker?

AB-Maker is an offline desktop application that converts EPUB e-books into high-quality audiobooks using AI text-to-speech (TTS). All processing happens locally on your computer - no cloud services, no API costs, complete privacy.

### Is it free?

Yes! AB-Maker is open-source under the AGPL v3 license. Free to use, modify, and distribute.

### What platforms are supported?

Currently: **Windows 10/11** (64-bit)

Planned: MacOS, Linux (future releases)

### Do I need an internet connection?

**Initial setup:** Yes, to download TTS models (~50-200 MB)

**Regular use:** No, everything runs offline

### Is my data private?

100%! All processing happens locally. No data is sent to cloud services. Your books and audio never leave your computer.

---

## Feature Questions

### What input formats are supported?

**Currently:** EPUB only

**Future:** PDF, MOBI, TXT (planned)

**Workaround:** Convert other formats to EPUB using [Calibre](https://calibre-ebook.com/)

### What output formats can I create?

- **.m4b** - Chapterized audiobook (recommended)
- **.mp3** - Universal compatibility (one file per chapter)

Both include metadata and cover art.

### How long does conversion take?

**Without GPU:**
- ~1-5 minutes per 1,000 words
- 300-page novel: ~2-3 hours

**With NVIDIA GPU (CUDA):**
- ~5-30 seconds per 1,000 words
- 300-page novel: ~10-15 minutes

**10-50x faster with GPU!**

### Can I batch convert multiple books?

Yes! Select multiple EPUBs (Ctrl+Click) and they'll convert sequentially. Progress shows "Book X/Y".

### How large are the output files?

Depends on quality preset:

| Quality | Size per Hour |
|---------|---------------|
| Low | ~25 MB |
| Medium | ~50 MB |
| High | ~100 MB |
| Lossless | ~300-500 MB |

300-page book (~10 hours) at Medium quality ≈ 500 MB

### What languages are supported?

Built-in models for:
- English (multiple voices)
- Spanish
- French
- German

Additional languages available via custom models.

---

## Quality Questions

### How good is the voice quality?

**Neural TTS** (VITS models) sound natural and expressive:
- Clear pronunciation
- Natural phrasing
- Multiple voice options
- Adjustable speed

**Better than:** Early robotic TTS, basic screen readers

**Not quite:** Human narrators, premium services like Audible

Perfect for personal use! Test with Preview before full conversion.

### Can I adjust the voice?

Yes:
- **Speed:** 0.5x - 2.5x (slower/faster reading)
- **Speaker ID:** Different voices per model (0, 1, 2...)
- **Model:** Choose from multiple TTS models

### How do I get better quality?

1. Use **High** or **Lossless** quality preset
2. Enable **Normalize** option
3. Test different TTS models
4. Adjust speed for naturalness (0.8x - 1.2x)
5. Try different Speaker IDs

---

## Technical Questions

### Do I need a powerful computer?

**Minimum:**
- Modern CPU (i5/Ryzen 5 or better)
- 4 GB RAM
- Works but slower (~3-5 hours for novel)

**Recommended:**
- NVIDIA GPU (GTX 1060 or better)
- 8 GB RAM  
- Much faster! (~15 min for novel)

**GPU makes huge difference** - 10-50x speedup

### What GPU do I need for acceleration?

**Requirements:**
- NVIDIA GPU (GeForce GTX/RTX series)
- CUDA support
- 4 GB+ VRAM

**Not supported:**
- AMD GPUs (no CUDA)
- Intel integrated graphics

**Recommended:**
- RTX 2060 or better
- 6 GB+ VRAM

### Can I use AMD GPU?

Currently no - sherpa-onnx uses CUDA (NVIDIA only).

AMD ROCm support is possible future enhancement.

### How much disk space do I need?

**For app:** ~500 MB (with one TTS model)

**Per audiobook:**
- Temporary: 2-5x final size (auto-deleted)
- Final: 25-500 MB/hour (depends on quality)

**Recommendation:** 5-10 GB free space for comfortable use

---

## Usage Questions

### Can I pause and resume conversion?

**Current:** Click STOP to cancel. Restart to resume - completed chapters are cached and skipped.

**Future:** Proper checkpoint system planned (resume from exact chapter)

### What if conversion fails?

1. Check error in logs
2. Common fixes:
   - Ensure FFmpeg installed
   - Check disk space
   - Try lower quality
   - Edit problematic chapter in EPUB
3. Delete failed chapter WAV and retry
4. See [Troubleshooting Guide](Troubleshooting.md)

### Can I edit chapters before conversion?

Yes! Click **📋 Edit Chapters** button to:
- View all chapters
- Rename chapter titles
- Fix numbering (Chapter001 → Chapter 1)
- Verify chapter order

Changes saved to metadata in output file.

### Can I use my own cover image?

Yes! Click **📷 Select Cover** to override EPUB cover.

Recommendations:
- Square images (1:1 ratio)
- Min 500x500px
- JPG or PNG format

### What happens to formatting?

- **Preserved:** Paragraphs, basic structure
- **Lost:** Fonts, colors, images, tables
- **Converted:** Headings → pauses, italics → slight emphasis (model-dependent)

TTS focuses on text content, not visual formatting.

---

## Comparison Questions

### How does this compare to Audible?

**AB-Maker:**
- ✅ Free, unlimited conversions
- ✅ Complete privacy
- ✅ Own your files
- ✅ Works offline
- ❌ AI voice (not human narrator)
- ❌ Requires setup time

**Audible:**
- ✅ Professional human narration
- ✅ Mobile apps
- ❌ Expensive ($15-30 per book)
- ❌ DRM restrictions
- ❌ Subscription required

**Best use:** AB-Maker for books without Audible versions, or personal library conversion.

### How does this compare to online TTS services?

**AB-Maker:**
- ✅ Offline, private
- ✅ No usage limits
- ✅ No recurring costs
- ✅ Own your data
- ❌ Requires local GPU for speed

**Cloud TTS (Google, AWS, Azure):**
- ✅ High-quality voices
- ✅ Many languages
- ❌ Costs $4-$16 per million characters
- ❌ Sends your book to cloud
- ❌ Requires internet

---

## Troubleshooting Questions

### Why does GPU toggle not do anything?

**Cause:** CUDA/cuDNN not installed correctly

**Solution:**
1. Install CUDA Toolkit 12.x
2. Install cuDNN 9.x
3. Install zlibwapi.dll
4. See [GPU Setup](Getting-Started.md#gpu-acceleration-setup-optional)

### Why is conversion so slow?

**On CPU:** 1-5 min per 1000 words is normal

**If slower:**
- Close other apps
- Use SSD
- Reduce quality

**On GPU:** Should be 10-50x faster than CPU

**If not:** GPU isn't actually being used - check logs, verify CUDA setup

### Why do I see "FFmpeg not found"?

**Cause:** FFmpeg not installed or not in PATH

**Solution:**
1. Install FFmpeg
2. Add to system PATH
3. Restart terminal/AB-Maker
4. See [FFmpeg Installation](Getting-Started.md#ffmpeg-installation)

### Can I convert DRM-protected books?

**No.** AB-Maker only works with DRM-free EPUBs.

**Workaround:**
- Buy DRM-free books
- Use legally-owned books
- Remove DRM (legal status varies by country)

AB-Maker doesn't include DRM removal tools.

---

## Future Features

### Will there be a web version?

Maybe! Web UI is on the roadmap bu requires significant changes.

### Will MacOS/Linux be supported?

Yes, planned for future releases. Technical challenges:
- Different GPU support (Metal for Mac)
- Different dependencies
- Testing across platforms

### Will you add more voices?

Yes! Plans include:
- More language models
- Voice cloning (custom voices)
- Integration with other TTS engines (Piper, Coqui)

### Can I contribute?

Absolutely! AB-Maker is open-source:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

See [Contributing Guide](Contributing.md)

---

## Legal Questions

### Can I sell audiobooks made with AB-Maker?

**Technical:** AB-Maker allows it

**Legal:** Depends on book copyright:
- ✅ Public domain books (Project Gutenberg)
- ✅ Your own written books
- ❌ Copyrighted books without permission

**Disclaimer:** You're responsible for ensuring legal rights to convert and distribute.

### What's the license?

**AB-Maker:** AGPL v3 (open-source)
- Free to use
- Must share modifications
- Can't make proprietary forks

**TTS Models:** Various licenses (check model source)

### Can I use this commercially?

**AB-Maker software:** Yes, under AGPL v3

**Audiobooks created:** Depends on source book's copyright

**For business use:** Consult a lawyer regarding book rights.

---

## Support Questions

### How do I report a bug?

1. Check [Troubleshooting Guide](Troubleshooting.md)
2. Search [GitHub Issues](https://github.com/your-username/AB-Maker/issues)
3. If new bug:
   - Create new issue
   - Include: Error message, logs, steps to reproduce
   - OS version, Python version

### How do I request a feature?

1. Check [GitHub Discussions](https://github.com/your-username/AB-Maker/discussions)
2. Search existing requests
3. If new: Create feature request discussion
4. Explain use case and benefits

### Where can I get help?

- 📖 [Documentation Wiki](Home.md)
- 🐛 [GitHub Issues](https://github.com/your-username/AB-Maker/issues)
- 💬 [GitHub Discussions](https://github.com/your-username/AB-Maker/discussions)
- 📧 Community forums (when available)

---

## Still Have Questions?

Can't find your answer? 

1. Search the [full documentation](Home.md)
2. Check [Troubleshooting Guide](Troubleshooting.md)
3. Ask in [GitHub Discussions](https://github.com/your-username/AB-Maker/discussions)

We're here to help! 🎧
