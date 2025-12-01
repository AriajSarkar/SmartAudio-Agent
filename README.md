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
git clone https://github.com/AriajSarkar/SmartAudio-Agent.git
cd SmartAudio-Agent

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install PyTorch with CUDA (CRITICAL - do this FIRST!)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

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

### Advanced Features

SAA includes production-ready features for Google ADK:

```python
# Observability with LoggingPlugin
from saa.observability import create_observability_plugin
runner = Runner(agent=pipeline, plugins=[create_observability_plugin()])

# Session management
from saa.sessions import create_session_service
session_service = create_session_service(persistent=True)
runner = Runner(agent=pipeline, session_service=session_service)

# Agent evaluation
from saa.evaluation import create_evaluator
evaluator = create_evaluator()
results = evaluator.evaluate_extraction(input_file)
```

**See**: `examples/advanced_features.py` for complete demonstrations

---

## 🏗️ Architecture

SAA uses **Google ADK's AgentTool Coordinator pattern** for intelligent, file-based audiobook generation:

```
┌─────────────────────────────────────────────────────────────┐
│          PIPELINE COORDINATOR (Gemini-Powered)              │
│        Calls Stage Agents as Tools + Verifies Files         │
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

### Why AgentTool Coordinator?

**Gemini-Powered Intelligence:**
- ✅ Coordinator uses Gemini to orchestrate workflow
- ✅ File-based verification between stages (no hallucinations)
- ✅ Explicit error handling with retry logic
- ✅ Clear progress communication to user

**vs. SequentialAgent (initial approach):**
- ❌ LLM-based routing skipped synthesis stage entirely
- ❌ output_key state passing caused hallucinations
- ❌ No explicit file verification

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
REPLICATE_MODEL=lucataco/xtts-v2
REPLICATE_MODEL_VERSION=684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e

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
MAX_SEGMENT_LENGTH=250  # chars per TTS call (prevents truncation warnings)
SESSION_DB_PATH=./sessions.db
```

---

## 📁 Project Structure

```
SAA/
├── saa/                        # Main package
│   ├── agents/                 # ADK agents
│   │   └── orchestrator.py     # AgentTool coordinator pipeline
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
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[INSTALL.md](docs/INSTALL.md)** - Detailed installation guide
- **[LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md)** - LLM provider configuration
- **[RELEASE_NOTES.md](docs/RELEASE_NOTES.md)** - Release notes

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

## ☁️ Deployment

### Production Deployment Options

SAA can be deployed to Google Cloud Platform for production use:

#### 1. Vertex AI Agent Engine (Recommended)
**Best for**: Production AI agents with auto-scaling

```powershell
# Deploy to Agent Engine
adk deploy agent_engine . --project=your-project-id --region=us-central1
```

**Configuration** (`.agent_engine_config.json`):
```json
{
  "min_instances": 0,
  "max_instances": 3,
  "resource_limits": {
    "cpu": "2",
    "memory": "4Gi"
  }
}
```

#### 2. Cloud Run (Serverless)
**Best for**: Simple deployments, cost-effective small workloads

```powershell
# Build and deploy
docker build -t gcr.io/PROJECT_ID/saa .
gcloud run deploy saa --image gcr.io/PROJECT_ID/saa --memory 4Gi
```

#### 3. Google Kubernetes Engine
**Best for**: Enterprise deployments with full control

```powershell
# Create cluster and deploy
gcloud container clusters create saa-cluster
kubectl apply -f k8s/deployment.yaml
```

### Deployment Checklist

- ✅ Set `GOOGLE_GENAI_USE_VERTEXAI=1` in production `.env`
- ✅ Use Secret Manager for API keys (never commit `.env`)
- ✅ Configure resource limits based on workload
- ✅ Enable auto-scaling (`min_instances: 0` for dev, `1+` for prod)
- ✅ Set up monitoring and logging
- ✅ Configure budget alerts to control costs

**Detailed deployment guide**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 🗺️ Roadmap

### v2.0.0 (Current)
- ✅ Google ADK multi-agent architecture
- ✅ Replicate cloud TTS + local fallback
- ✅ Character voice detection & assignment
- ✅ CLI interface (basic)
- ✅ Observability with LoggingPlugin
- ✅ Session management (multi-turn conversations)
- ✅ Agent evaluation framework
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
