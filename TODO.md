# TODO - SAA Development Roadmap

## 🚀 v2.0.0 - Current Release

### ✅ Completed
- [x] Google ADK multi-agent architecture
- [x] SequentialAgent orchestration (5 agents)
- [x] 17 ADK function tools
- [x] Replicate cloud TTS provider
- [x] Local XTTS-v2 provider with GPU management
- [x] Pydantic settings with .env loading
- [x] Custom exception hierarchy
- [x] Data models (TextSegment, VoiceProfile, etc.)
- [x] CLI interface (Click + Rich)
- [x] Character voice detection
- [x] Audio merging and normalization
- [x] Text Refinement Agent (Stage 2.5)
- [x] Comprehensive documentation

### 🔄 In Progress
- [ ] FastAPI REST API server
  - [ ] Endpoint: POST /audiobooks (create job)
  - [ ] Endpoint: GET /audiobooks/{id} (status)
  - [ ] Endpoint: GET /audiobooks/{id}/download
  - [ ] Session management with DatabaseSessionService
  - [ ] Background task processing
- [ ] Checkpoint/resume functionality
  - [ ] MessagePack serialization
  - [ ] JobState persistence
  - [ ] Resume from ProcessingStage
  - [ ] CLI resume command implementation
- [ ] Testing infrastructure
  - [ ] Unit tests for all tools
  - [ ] Integration tests for pipeline
  - [ ] Mocked TTS providers
  - [ ] GitHub Actions CI

---

## 🎯 v2.1.0 - Feature Expansion

### High Priority
- [ ] **Web UI**
  - [ ] Dashboard for audiobook library
  - [ ] Upload PDF/TXT interface
  - [ ] Real-time generation progress
  - [ ] Audio player with waveform
  - [ ] Voice profile management
  - [ ] Technology: Svelte or React + FastAPI backend

- [ ] **Authentication & User System**
  - [ ] JWT-based authentication
  - [ ] User registration and login
  - [ ] Per-user audiobook library
  - [ ] API key management
  - [ ] Usage quotas and rate limiting

- [ ] **Multi-Model TTS Support**
  - [ ] ElevenLabs API integration
  - [ ] Azure Cognitive Services TTS
  - [ ] Google Cloud TTS
  - [ ] Provider selection per character
  - [ ] Cost estimation before generation

- [ ] **Advanced Character Detection**
  - [ ] Named Entity Recognition (spaCy)
  - [ ] Dialogue tracking across chapters
  - [ ] Character relationship mapping
  - [ ] Manual character override UI

- [ ] **Audio Caching**
  - [ ] Content-addressable storage (hash-based)
  - [ ] Reuse identical segments across books
  - [ ] Cache hit rate monitoring
  - [ ] Configurable cache size limits

### Medium Priority
- [ ] **Emotion & Prosody Control**
  - [ ] Sentiment analysis per segment
  - [ ] Emotion tags (happy, sad, angry, etc.)
  - [ ] Dynamic TTS parameter adjustment
  - [ ] Manual emotion override

- [ ] **Progress Indicators**
  - [ ] Estimated time remaining
  - [ ] Per-stage progress bars
  - [ ] GPU utilization monitoring
  - [ ] Real-time logs in Web UI

- [ ] **Audio Enhancements**
  - [ ] Background music support
  - [ ] Sound effects library
  - [ ] Chapter markers
  - [ ] Variable playback speed

- [ ] **Document Support**
  - [ ] EPUB support
  - [ ] DOCX support
  - [ ] HTML/Markdown support
  - [ ] OCR for image-only PDFs

### Low Priority
- [ ] Batch processing (multiple books)
- [ ] Custom voice training wizard
- [ ] Voice style transfer
- [ ] Pronunciation dictionary
- [ ] Chapter-based splitting
- [ ] Metadata editor (title, author, narrator)

---

## 🌐 v3.0.0 - Enterprise & Scale

### Infrastructure
- [ ] **Docker & Kubernetes**
  - [ ] Multi-container setup (API, Worker, Database)
  - [ ] Helm charts for deployment
  - [ ] Auto-scaling based on queue depth
  - [ ] Health checks and monitoring

- [ ] **Distributed Processing**
  - [ ] Celery task queue
  - [ ] Redis for coordination
  - [ ] Multi-GPU support
  - [ ] Cloud GPU autoscaling (AWS, GCP)

- [ ] **Real-Time Streaming**
  - [ ] WebSocket-based streaming
  - [ ] Server-Sent Events for progress
  - [ ] Incremental audio delivery
  - [ ] Live audiobook preview

### Advanced Features
- [ ] **Custom Voice Training**
  - [ ] Fine-tune XTTS-v2 on user audio
  - [ ] Transfer learning pipeline
  - [ ] Voice quality evaluation
  - [ ] Training progress tracking

- [ ] **Multi-Language Support**
  - [ ] Language detection per segment
  - [ ] Language-specific TTS models
  - [ ] Translation integration (Google Translate)
  - [ ] Mixed-language audiobooks

- [ ] **Observability**
  - [ ] ADK LoggingPlugin integration
  - [ ] Custom metrics (synthesis time, cost, etc.)
  - [ ] Distributed tracing (OpenTelemetry)
  - [ ] Grafana dashboards

- [ ] **Cost Optimization**
  - [ ] Smart provider routing (cheapest first)
  - [ ] Budget caps per user/project
  - [ ] Cost breakdown reports
  - [ ] Reserved capacity discounts

---

## 🐛 Known Issues

### Critical
- [x] Session database not yet implemented (InMemorySessionService placeholder)
- [x] Checkpoint save/load not functional
- [x] CLI `resume` command not implemented
- [ ] CLI `sample` command not implemented
- [ ] No tests written yet

### Major
- [ ] GPU memory not freed between long sessions
- [ ] Large PDFs (>500 pages) cause memory issues
- [ ] Character detection fails on non-English dialogue
- [ ] No progress feedback during synthesis (blocks for minutes)

### Minor
- [ ] FFmpeg path detection fails on some Windows setups
- [ ] MP3 export quality not configurable
- [ ] Reference audio validation missing (accepts non-WAV files)
- [ ] Verbose logging too chatty in CLI

---

## 🔧 Technical Debt

### Code Quality
- [ ] Add type hints to all functions
- [ ] Improve error messages (more context)
- [ ] Reduce code duplication in tools
- [ ] Refactor long functions (>50 lines)
- [ ] Add docstring examples to all tools

### Testing
- [ ] Unit test coverage <10% (target 85%)
- [ ] No integration tests
- [ ] No performance benchmarks
- [ ] No load testing

### Documentation
- [ ] API reference docs (Sphinx)
- [ ] Architecture diagrams
- [ ] Tutorial videos
- [ ] Developer onboarding guide

### Dependencies
- [ ] Pin all dependencies (not using >=)
- [ ] Audit for security vulnerabilities
- [ ] Remove unused dependencies
- [ ] Evaluate lighter alternatives (pydub → wave?)

---

## 💡 Ideas for Exploration

- **Voice Profiles Library**: Pre-trained voices for common character archetypes
- **Audiobook Marketplace**: Share/sell generated audiobooks (legal issues?)
- **Podcast Generation**: Auto-convert blog posts to podcast episodes
- **Accessibility**: Screen reader integration, dyslexia-friendly fonts
- **Educational**: Language learning with pronunciation guides
- **Gaming**: NPC dialogue generation for games
- **Storytelling**: Interactive choose-your-own-adventure audiobooks

---

## 📝 Notes

### Migration from v1.x to v2.0
1. Install new dependencies: `pip install -e .`
2. Create `.env` file from `.env.example`
3. Add Google API key and Replicate token
4. Move input files to `input/` folder
5. Run: `python -m saa generate input/mybook.pdf`
6. Old scripts (audiobook.py) still work but deprecated

### Breaking Changes in v2.0
- CLI changed from `python audiobook.py` to `python -m saa`
- Configuration moved from `config.py` to `.env`
- Output structure changed (no more intermediate chunks by default)
- Character detection now requires explicit reference audio files

---

**Last Updated**: 2024-01-XX
