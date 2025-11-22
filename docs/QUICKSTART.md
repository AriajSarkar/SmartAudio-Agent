# Quick Start Guide

This guide will help you get your first audiobook generated in minutes.

## 1. Installation

### Prerequisites
- Python 3.11+
- NVIDIA GPU (Recommended for local TTS)
- FFmpeg (Required for MP3 export)

### Install PyTorch (Critical Step)
You must install PyTorch with CUDA support **before** installing SAA:

```powershell
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Install SAA
```powershell
git clone https://github.com/AriajSarkar/SmartAudio-Agent.git
cd SmartAudio-Agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## 2. Configuration

Copy the example environment file:
```powershell
cp .env.example .env
```

Edit `.env` with your API keys:
- **GOOGLE_API_KEY**: Required for the agent intelligence (Gemini).
- **REPLICATE_API_TOKEN**: Optional, for cloud-based TTS.

## 3. Generate Your First Audiobook

### Using a Sample File
```powershell
python -m saa generate input/sample.txt -o output/sample_book
```

### Using Your Own PDF
1. Place your PDF in the `input/` folder.
2. Run the generation command:
```powershell
python -m saa generate input/mybook.pdf
```

## 4. Check the Output
Your audiobook will be saved in `output/{job_id}/final.mp3`.

## Next Steps
- Learn about [Character Voice Cloning](CHARACTER_VOICE_GUIDE.md)
- View [Troubleshooting](TROUBLESHOOTING.md) if you encounter issues.
