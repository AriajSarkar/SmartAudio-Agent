# AudioBook TTS System - Setup Guide

**Convert PDF and TXT files to audiobooks with AI voice cloning!**

## 📋 System Requirements

- **Python**: 3.8 - 3.11 (recommended 3.10)
- **GPU**: NVIDIA RTX 3050 4GB (CUDA support)
- **RAM**: 8GB+ recommended
- **Storage**: 5GB+ for models and dependencies

---

## 🚀 Installation Steps

### 1. Activate Your Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install PyTorch with CUDA Support (for RTX 3050)

```powershell
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Install FFmpeg (Optional but Recommended)

**Option A: Using Chocolatey (easiest)**
```powershell
choco install ffmpeg
```

**Option B: Manual Installation**
1. Download from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH

### 5. Verify Installation

```powershell
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
```

Should output: `CUDA Available: True`

---

## 📖 Usage

### Step 1: Place Your File

Drop your PDF or TXT file into the `input/` folder:
```
AudioBook/input/mybook.pdf
AudioBook/input/story.txt
```

### Step 2: Generate Sample First (RECOMMENDED)

```powershell
python audiobook.py
```

The system will auto-detect your file!

This will:
1. Auto-detect your file from `input/` folder
2. Generate a **sample audio** from the first ~1000 characters
3. Save it to `samples/` folder
4. Ask if you want to continue with full generation

### Step 3: Listen to Sample & Adjust Settings

1. **Play the sample audio** to check voice quality
2. **Edit `config.py`** to adjust:
   - `temperature`: Voice expressiveness (0.1-1.0)
   - `speed`: Playback speed (0.5-2.0)
   - `language`: Language code
   - `bitrate`: Audio quality (128k, 192k, 320k)

3. **Re-run** to generate new sample with adjusted settings

### Step 4: Generate Full Audiobook

Once satisfied with sample:
```powershell
python audiobook.py
```

Choose `y` when prompted to generate full audiobook.

---

## 📁 Project Structure

```
AudioBook/
├── input/                      # ← Place your files here!
│   ├── mybook.pdf             # PDF documents
│   └── story.txt              # Text files
├── output/                     # Generated audiobooks
│   └── mybook_audiobook_[timestamp].mp3
├── samples/                    # Sample previews
│   └── sample_[timestamp].mp3
├── reference_audio/            # Voice samples for cloning
│   └── female_en_1_reference.wav
├── audiobook.py               # Main script
├── config.py                  # Configuration
└── requirements.txt           # Dependencies
```

---

## ⚙️ Configuration Options

Edit `config.py` to customize:

### Voice Quality
```python
TTS_CONFIG = {
    "temperature": 0.75,  # 0.1 (monotone) to 1.0 (expressive)
    "speed": 1.0,         # 0.5 (slow) to 2.0 (fast)
    "language": "en",     # en, es, fr, de, it, pt, etc.
}
```

### Audio Export
```python
AUDIO_CONFIG = {
    "format": "mp3",      # mp3, wav, ogg
    "bitrate": "192k",    # 128k, 192k, 320k
}
```

### Voice Cloning (Optional)
```python
TTS_CONFIG = {
    "speaker_wav": "path/to/reference_audio.wav",  # 6+ seconds of speech
}
```

---

## 📁 File Structure

```
AudioBook/
├── audiobook.py        # Main script (renamed from TTS.py)
├── config.py           # Settings
├── pdf_processor.py    # PDF extraction
├── tts_engine.py       # TTS generation
├── audio_utils.py      # Audio processing
├── requirements.txt    # Dependencies
├── TTS.pdf            # Your PDF file
├── output/            # Generated audiobooks
└── samples/           # Sample previews
```

---

## 🎯 Optimization for RTX 3050 4GB

Your GPU is perfect for this! The system is optimized for 4GB VRAM:

- ✅ **Chunk processing**: Processes text in small chunks to avoid memory overflow
- ✅ **GPU acceleration**: Uses CUDA for 5-10x faster generation
- ✅ **Auto memory cleanup**: Clears GPU memory after generation

### Expected Performance:
- **Sample generation**: 10-30 seconds
- **Full audiobook**: ~1-3 minutes per page (GPU)
- **Memory usage**: 2-3GB VRAM

---

## 🐛 Troubleshooting

### CUDA Not Available
```powershell
# Reinstall PyTorch with CUDA
pip uninstall torch torchaudio
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory Error
Reduce chunk size in `config.py`:
```python
PDF_CONFIG = {
    "chunk_size": 300,  # Default is 500
}
```

### Poor Audio Quality
1. Increase bitrate: `"bitrate": "320k"`
2. Install FFmpeg for better encoding
3. Adjust temperature: `"temperature": 0.65`

---

## 🎤 Available Languages

Supported by XTTS-v2:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Polish (pl)
- Turkish (tr)
- Russian (ru)
- Dutch (nl)
- Czech (cs)
- Arabic (ar)
- Chinese (zh-cn)
- Japanese (ja)
- Hungarian (hu)
- Korean (ko)

---

## 📝 Tips for Best Results

1. **Always test with sample first** - Saves time if settings need adjustment
2. **Use clean PDFs** - Better text extraction = better audio
3. **Adjust temperature** - Lower for technical content, higher for fiction
4. **Enable FFmpeg** - Significantly better audio quality
5. **Keep chunks small** - Better pronunciation and pacing

---

## 🆘 Support

If you encounter issues:
1. Check Python version (3.8-3.11)
2. Verify CUDA installation
3. Ensure .venv is activated
4. Check `samples/` folder for test output

Enjoy your AI-generated audiobook! 🎧📚
