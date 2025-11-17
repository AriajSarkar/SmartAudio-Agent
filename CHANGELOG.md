# Changelog

All notable changes to SAA (Smart Audio Agent) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-XX

### 🎉 Major Rewrite - Google ADK Integration

Complete architectural redesign from monolithic scripts to multi-agent system.

### Added
- **Google ADK Integration**: Full multi-agent orchestration with AgentTool Coordinator
- **17 ADK Function Tools**: Modular tools for document, text, voice, TTS, and audio processing
- **Replicate Cloud TTS**: Cloud-based synthesis with automatic fallback
- **LocalTTSProvider**: GPU-optimized Coqui XTTS-v2 wrapper with memory management
- **Pydantic Settings**: Environment-based configuration with validation
- **CLI Application**: Click-based command-line interface with Rich output
- **Custom Exception Hierarchy**: 15+ error types with recovery flags
- **Data Models**: TextSegment, VoiceProfile, AudioChunk, JobState
- **Session Management**: DatabaseSessionService for checkpoints (planned)
- **Comprehensive Documentation**: README, CHANGELOG, TODO, CONTRIBUTING

### Changed
- **BREAKING**: Renamed project from AudioBook to SAA (Smart Audio Agent)
- **BREAKING**: New package structure: `saa/` instead of flat scripts
- **BREAKING**: CLI now `python -m saa` instead of `python audiobook.py`
- **BREAKING**: Configuration moved from `config.py` to `.env` + Pydantic
- **Architecture**: Monolithic → AgentTool coordinator with file-based verification
- **TTS**: Single provider → Replicate + local with auto-fallback
- **Character Detection**: Preserved multi-strategy algorithm, now as function tool
- **GPU Management**: Enhanced monitoring with 90% VRAM threshold

### Removed
- **Legacy Scripts**: audiobook.py, audiobook_tts_pdf.py (replaced by agents)
- **Old Config**: config.py (replaced by settings.py)
- **Emotion Controller**: Removed (will be re-added in v2.1.0)
- **Direct TTS Calls**: Replaced by provider abstraction

### Fixed
- GPU memory leaks through automatic cleanup after synthesis
- Character detection false positives (improved dialogue attribution)
- PDF extraction failures with multi-strategy fallback (pdfplumber → PyPDF2)
- TTS truncation warnings (reduced segment limit from 800 to 250 chars)
- ADK app name mismatch (explicit app_name="saa" in all 6 agents)
- Path nesting issues (output/output/ bug fixed)

### Migrated
All functionality from v1.x preserved:
- ✅ PDF/TXT extraction with OCR cleanup
- ✅ Character voice detection (dialogue patterns + pronouns)
- ✅ Voice cloning with reference audio
- ✅ Audio merging with crossfade
- ✅ Normalization and format conversion
- ✅ Multi-format export (MP3, WAV, OGG, FLAC)

---

## [1.0.0] - 2023-XX-XX

### Initial Release (Legacy)
- Monolithic audiobook.py and audiobook_tts_pdf.py scripts
- PDF to audiobook conversion
- Character voice detection
- Local Coqui TTS integration
- Basic progress tracking
- Sample generation workflow

---

## [Unreleased]

### Planned for v2.1.0
- FastAPI REST API server
- Checkpoint/resume with MessagePack
- Web UI for audiobook management
- Multi-model TTS support (ElevenLabs, Azure)
- Advanced character detection with NER
- Audio caching for repeated segments
- Authentication and user system

### Planned for v3.0.0
- Real-time streaming TTS
- Custom voice training pipeline
- Emotion and prosody control
- Multi-language support
- Docker and Kubernetes deployment
- Distributed processing

---

[2.0.0]: https://github.com/AriajSarkar/saa/releases/tag/v2.0.0
[1.0.0]: https://github.com/AriajSarkar/saa/releases/tag/v1.0.0
