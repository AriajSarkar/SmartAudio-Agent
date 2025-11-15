# SAA (Smart Audio Agent) 🎙️

**AI-powered audiobook generation with multi-agent orchestration**

Convert PDF and TXT documents into audiobooks with character voice cloning using Google ADK, Replicate cloud TTS, and local XTTS-v2 models.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4?logo=google)](https://google.github.io/adk-docs/)

---

## ✨ Features

- **🤖 Multi-Agent Architecture**: Built with Google ADK for intelligent task orchestration
- **🎭 Character Voice Cloning**: Automatic detection and voice assignment using AI
- **☁️ Cloud + Local TTS**: Replicate API with automatic fallback to local XTTS-v2
- **📄 Smart Document Processing**: PDF and TXT extraction with OCR cleanup
- **🔊 Professional Audio**: Normalization, crossfade merging, multi-format export
- **💾 Checkpoint/Resume**: Long audiobook support with MessagePack serialization
- **🖥️ CLI & API**: Command-line tool + FastAPI REST server (planned)
- **🎯 GPU Optimized**: CUDA acceleration with automatic memory management

---

## 🚀 Quick Start

### Installation

```powershell
# Clone repository
git clone https://github.com/AriajSarkar/saa.git
cd saa

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install PyTorch with CUDA (CRITICAL - do this FIRST!)
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Install SAA in editable mode
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY and REPLICATE_API_TOKEN
```

### Basic Usage

```powershell
# Generate audiobook from PDF
python -m saa generate input/mybook.pdf -o output/mybook

# Show configuration
python -m saa config

# Generate sample preview (coming soon)
python -m saa sample reference_audio/narrator.wav --text "Hello world"
```

### Python API

```python
from saa import create_audiobook_pipeline
import asyncio

async def main():
    pipeline = create_audiobook_pipeline()
    
    # Run pipeline
    from saa.agents.orchestrator import run_audiobook_generation
    result = await run_audiobook_generation(
        input_file="input/book.pdf",
        output_dir="output/audiobook"
    )
    
    print(f"Status: {result['status']}")

asyncio.run(main())
```

---

## 🏗️ Architecture

SAA uses a **Custom Agent** inheriting from `BaseAgent` with deterministic 5-stage execution:

```
┌─────────────────────────────────────────────────────────────┐
│          CUSTOM AGENT (AudiobookPipelineAgent)              │
│              Deterministic Pipeline Execution                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. DocumentExtractor     → Extract + understand structure   │
│     Tools: extract_text, get_metadata                        │
│     Gemini: Chapter breaks, dialogue detection               │
│                                                               │
│  2. TextPreprocessor      → Clean + segment intelligently    │
│     Tools: clean_text, filter_content, segment              │
│     Gemini: Garbage removal, structural meaning              │
│                                                               │
│  3. VoicePlanner          → Assign voices with context       │
│     Tools: detect_characters, analyze_gender, assign_voice   │
│     Gemini: Emotional tone, speed, prosody decisions         │
│                                                               │
│  4. AudioSynthesizer      → Generate TTS (with retry)        │
│     Tools: synthesize_audio, cleanup_resources               │
│     Gemini: Retry logic, cloud vs local, error recovery      │
│                                                               │
│  5. AudioFinalizer        → Merge + normalize + export       │
│     Tools: merge_chunks, normalize, export, get_info         │
│     Gemini: Quality checks, normalization levels             │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Philosophy:
- Tools = Actions (do the work)
- Gemini = Intelligence (make decisions)
- Agents = Orchestrators (combine intelligence + tools)
```

### Why Custom Agent?

**Deterministic Execution:**
- ✅ GUARANTEED no step skipping (Python control flow)
- ✅ Explicit retry logic for TTS failures  
- ✅ State validation between stages
- ✅ No wasted LLM calls for routing decisions

**vs. SequentialAgent:**
- ❌ LLM-based routing can skip steps
- ❌ Non-deterministic execution order
- ❌ Extra tokens spent on orchestration

### Agent Tools (15 Functions)

| Domain | Tools | Purpose |
|--------|-------|---------|
| **Document** | `extract_text_from_pdf`, `extract_text_from_txt`, `get_document_metadata` | Extract and understand structure |
| **Text** | `clean_text`, `segment_text`, `filter_unwanted_content` | Clean and intelligently segment |
| **Voice** | `detect_characters`, `assign_voice_profile`, `analyze_text_gender` | Assign contextual voices |
| **TTS** | `synthesize_audio`, `cleanup_tts_resources` | Generate audio with retry logic |
| **Audio** | `merge_audio_chunks`, `normalize_audio`, `export_audio_format`, `get_audio_info` | Finalize audiobook |

### TTS Providers

1. **Replicate (Cloud)**: Fast, scalable, no GPU required
2. **Local XTTS-v2**: Coqui TTS with voice cloning, requires NVIDIA GPU

**Fallback Strategy**: Replicate → Local (automatic on API failure)

---

## 📋 Requirements

### System Requirements
- **Python**: 3.11+ and <3.13 (tested with 3.11, 3.12)
- **GPU**: NVIDIA GPU with 4GB+ VRAM (for local TTS)
- **CUDA**: 11.8 (for PyTorch)
- **FFmpeg**: Required for MP3 export
- **OS**: Windows (PowerShell), Linux, macOS

### API Keys
- **Google API Key**: Required for ADK agents (Gemini models)
- **Replicate API Token**: Optional (for cloud TTS)

Get API keys:
- Google AI Studio: https://aistudio.google.com/app/apikey
- Replicate: https://replicate.com/account/api-tokens

---

## 🎛️ Configuration

All settings in `.env`:

```bash
# Google ADK (REQUIRED)
GOOGLE_API_KEY=AIza...
GEMINI_TEXT_MODEL=gemini-2.5-flash-lite

# Replicate Cloud TTS (OPTIONAL)
REPLICATE_API_TOKEN=r8_...

# TTS Settings
TTS_PROVIDER=auto  # auto, replicate, local
TTS_USE_GPU=true
TTS_TEMPERATURE=0.75
TTS_SPEED=1.0

# Audio Settings
AUDIO_FORMAT=mp3
NORMALIZE_AUDIO=true
CROSSFADE_DURATION=100

# System
MAX_SEGMENT_LENGTH=800  # chars per TTS call
SESSION_DB_PATH=./sessions.db
```

---

## 📁 Project Structure

```
SAA/
├── saa/                        # Main package
│   ├── agents/                 # ADK agents
│   │   └── orchestrator.py     # SequentialAgent pipeline
│   ├── tools/                  # 17 ADK function tools
│   │   ├── document_tools.py   # PDF/TXT extraction
│   │   ├── text_tools.py       # Cleaning & segmentation
│   │   ├── voice_tools.py      # Character detection
│   │   ├── tts_tools.py        # Synthesis orchestration
│   │   └── audio_tools.py      # Merging & export
│   ├── providers/              # TTS backends
│   │   ├── local_provider.py   # Coqui XTTS-v2
│   │   └── replicate_provider.py  # Cloud API
│   ├── models/                 # Data models
│   │   ├── text_segment.py
│   │   ├── voice_profile.py
│   │   ├── audio_metadata.py
│   │   └── job_state.py
│   ├── config/                 # Pydantic settings
│   │   └── settings.py
│   ├── cli/                    # Click CLI
│   │   └── app.py
│   └── exceptions.py           # Custom errors
├── reference_audio/            # Voice cloning samples
│   ├── narrator.wav            # Narrator voice
│   ├── male.wav                # Male character
│   └── female.wav              # Female character
├── input/                      # Input documents
├── output/                     # Generated audiobooks
├── tests/                      # Test suite (coming soon)
├── .env                        # Environment config
├── pyproject.toml              # Package metadata
└── README.md                   # This file
```

---

## 🎤 Voice Cloning Setup

SAA requires **reference audio files** for voice cloning:

1. **Create** 6-15 second WAV files of clear speech
2. **Place** in `reference_audio/` folder:
   - `narrator.wav` - Default narrator voice
   - `male.wav` - Male characters
   - `female.wav` - Female characters
3. **Run** audiobook generation

**Tips for best results:**
- Use 22050 Hz sample rate
- Remove background noise
- Clear pronunciation, natural speech
- 6-15 seconds duration (not too short/long)

See `docs/CHARACTER_VOICE_GUIDE.md` for detailed instructions.

---

## 🔧 Development

### Setup Development Environment

```powershell
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black saa/
ruff check saa/

# Type checking
mypy saa/
```

### Running Tests

```powershell
# All tests
pytest

# With coverage
pytest --cov=saa --cov-report=html

# Specific test
pytest tests/unit/test_tools.py -v
```

---

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Installation & first audiobook
- **[CHARACTER_VOICE_GUIDE.md](docs/CHARACTER_VOICE_GUIDE.md)** - Voice cloning setup
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common errors
- **[TODO.md](TODO.md)** - Planned features
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines

---

## 🐛 Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'TTS'"**
```powershell
pip install TTS==0.22.0
```

**"CUDA out of memory"**
- Reduce `MAX_SEGMENT_LENGTH` in `.env`
- Use `TTS_PROVIDER=replicate` for cloud fallback

**"FFmpeg not found"**
```powershell
# Windows (WinGet)
winget install Gyan.FFmpeg

# Or download from: https://ffmpeg.org/download.html
```

**"Replicate API authentication failed"**
- Check `REPLICATE_API_TOKEN` in `.env`
- Verify token at https://replicate.com/account/api-tokens
- Fallback to local: `TTS_PROVIDER=local`

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

---

## 🗺️ Roadmap

### v2.0.0 (Current)
- ✅ Google ADK multi-agent architecture
- ✅ Replicate cloud TTS + local fallback
- ✅ Character voice detection & assignment
- ✅ CLI interface (basic)
- 🔄 FastAPI REST API (in progress)
- 🔄 Checkpoint/resume (in progress)

### v2.1.0 (Planned)
- 📋 Web UI for audiobook management
- 📋 Authentication & user system
- 📋 Multi-model TTS support (ElevenLabs, Azure)
- 📋 Advanced character detection (NER, dialogue tracking)
- 📋 Audio caching for repeated segments

### v3.0.0 (Future)
- 📋 Real-time streaming TTS
- 📋 Custom voice training
- 📋 Emotion/prosody control
- 📋 Multi-language support
- 📋 Cloud deployment (Docker, K8s)

See [TODO.md](TODO.md) for complete roadmap.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Key Areas Needing Help
- **Testing**: Unit tests for all tools and agents
- **Documentation**: Tutorials, examples, API docs
- **Features**: Web UI, additional TTS providers
- **Optimization**: GPU memory, inference speed

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Google ADK**: Multi-agent orchestration framework
- **Coqui TTS**: Open-source XTTS-v2 model
- **Replicate**: Cloud GPU infrastructure
- **PyTorch**: Deep learning framework

---

## 📧 Contact

- **GitHub Issues**: https://github.com/AriajSarkar/saa/issues
- **Email**: your.email@example.com

---

**Made with ❤️ using Google ADK**
