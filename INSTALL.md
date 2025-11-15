# SAA v2.0 - Quick Installation & Testing Guide

## 🚀 Installation

### Step 1: Install PyTorch with CUDA (CRITICAL FIRST STEP)

```powershell
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
```

### Step 2: Install SAA Package

```powershell
# From repository root
pip install -e .
```

This installs:
- google-adk >= 1.18.0
- replicate >= 0.25.0
- TTS == 0.22.0 (Coqui voice cloning)
- pydantic-settings >= 2.0.0
- click >= 8.1.0
- rich >= 13.7.0
- All other dependencies

### Step 3: Configure Environment

```powershell
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
notepad .env
```

**Required:**
- `GOOGLE_API_KEY` - Get from https://aistudio.google.com/app/apikey

**Optional:**
- `REPLICATE_API_TOKEN` - Get from https://replicate.com/account/api-tokens

---

## ✅ Verify Installation

### Check Package Installed

```powershell
python -c "import saa; print(saa.__version__)"
# Should print: 2.0.0
```

### Check Configuration

```powershell
python -m saa config
```

Expected output:
```
┌───────────────────────────────────────────┐
│            SAA Configuration              │
├───────────────────────────────────────────┤
│ TTS Provider: auto                        │
│ Effective Provider: replicate (or local)  │
│ Replicate Available: true (or false)      │
│ Gemini Model: gemini-2.5-flash-lite       │
│ GPU Enabled: true                         │
│ Max Segment Length: 800                   │
│ Output Format: mp3                        │
│ Session DB: ./sessions.db                 │
└───────────────────────────────────────────┘
```

### Check CLI Commands

```powershell
python -m saa --help
```

Expected output:
```
Usage: python -m saa [OPTIONS] COMMAND [ARGS]...

  🎙️ Smart Audio Agent (SAA) - AI-powered audiobook generator

Commands:
  config          Show current configuration
  generate        Generate audiobook from PDF or TXT file
  list-sessions   List all saved sessions
  resume          Resume audiobook generation from checkpoint
  sample          Generate a short audio sample for testing
```

---

## 🧪 Test with Sample File

### Option 1: Quick Test (Text File)

```powershell
# Create simple test file
@"
This is a test of the Smart Audio Agent.
The agent will convert this text to speech.
"@ | Out-File -Encoding UTF8 test_input.txt

# Generate audiobook
python -m saa generate test_input.txt -o output/test
```

### Option 2: Full Test (Existing Sample)

```powershell
# Use pre-existing sample file
python -m saa generate pre-input/sample.txt -o output/sample_audiobook

# Check output
dir output/sample_audiobook
```

Expected:
- Audiobook MP3 file (or WAV if FFmpeg not installed)
- Processing logs showing 5 agents executing

---

## 🔍 Troubleshooting

### "ModuleNotFoundError: No module named 'google.adk'"

```powershell
# Reinstall with clean cache
pip install --no-cache-dir google-adk>=1.18.0
```

### "ModuleNotFoundError: No module named 'TTS'"

```powershell
# Install Coqui TTS
pip install TTS==0.22.0
```

### "pydantic-settings module not found"

```powershell
# Install pydantic-settings
pip install pydantic-settings>=2.0.0
```

### "CUDA not available"

Check PyTorch CUDA:
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

If `False`:
```powershell
# Reinstall PyTorch with CUDA
pip uninstall torch torchaudio
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
```

### "GOOGLE_API_KEY not found"

```powershell
# Check .env file exists
Test-Path .env

# Add API key manually
@"
GOOGLE_API_KEY=AIza...your-actual-key...
"@ | Add-Content .env
```

### "FFmpeg not found" (MP3 Export)

```powershell
# Install FFmpeg via WinGet
winget install Gyan.FFmpeg

# Or download from: https://ffmpeg.org/download.html
```

**Note**: Without FFmpeg, audiobooks export as WAV (larger files).

---

## 📋 What to Test

### 1. Configuration Loading

```powershell
python -m saa config
# Should show all settings from .env
```

### 2. PDF Extraction

```powershell
# Test with any PDF
python -m saa generate input/your_document.pdf
```

### 3. Character Detection

```powershell
# Use pre-input/test-character-voices.txt if it exists
python -m saa generate pre-input/test-character-voices.txt
# Should detect multiple speakers
```

### 4. TTS Fallback

```powershell
# Test with local TTS (force, ignore Replicate)
$env:TTS_PROVIDER="local"
python -m saa generate test_input.txt
```

### 5. GPU Cleanup

```powershell
# Generate audiobook, then check GPU memory
python -m saa generate test_input.txt
python -c "import torch; print(f'GPU Memory: {torch.cuda.memory_allocated()/1e9:.2f} GB')"
# Should show minimal memory used (cleanup worked)
```

---

## ✅ Success Criteria

Installation successful if:

- [x] `python -m saa config` shows configuration
- [x] `python -m saa generate test.txt` completes without errors
- [x] Output audiobook file created in `output/` folder
- [x] No Python import errors
- [x] GPU cleanup happens (VRAM freed after generation)

---

## 🎉 Ready to Use!

If all tests pass, SAA v2.0 is ready for audiobook generation.

**Next Steps:**
- Generate your first audiobook: `python -m saa generate input/mybook.pdf`
- Read documentation: [README.md](README.md)
- Report issues: GitHub Issues

---

## 📧 Need Help?

- **Documentation**: [README.md](README.md), [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **GitHub Issues**: https://github.com/yourusername/saa/issues
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
