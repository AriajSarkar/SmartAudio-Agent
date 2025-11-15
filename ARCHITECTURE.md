# SAA Architecture - Professional-Grade Custom Agent System

## Overview

SAA (Smart Audio Agent) uses Google ADK's Custom Agent pattern for deterministic, reliable audiobook generation. This document explains the architectural decisions and implementation philosophy.

---

## Core Philosophy

```
Tools = Actions (extract, clean, synthesize, merge)
Gemini = Intelligence (decisions, structure, judgment)
Agents = Orchestrators (intelligence + tools combined)
```

### What Each Component Does

**Tools** (15 functions in `saa/tools/`):
- Perform actual work (PDF extraction, TTS synthesis, audio merging)
- Return structured data (`Dict[str, Any]` with status)
- No decision-making - just execute and report

**Gemini** (LLM reasoning engine):
- Understands document structure (chapters, dialogue, narration)
- Makes cleaning decisions (garbage text, headers, metadata)
- Interprets meaning (emotional tone, voice selection, pacing)
- Handles error recovery (rewrite messy text, retry with different params)
- Does NOT do TTS or PDF parsing itself

**Agents** (5 specialized LlmAgents):
- Combine Gemini's intelligence with relevant tools
- Each has focused responsibility and specific tools
- Pass state via `output_key` (e.g., `raw_text`, `text_segments`)
- Use Gemini to make intelligent decisions before calling tools

---

## Architecture: Custom Agent Pattern

### Why Custom Agent?

**Problem with SequentialAgent:**
- LLM-based routing decides when to stop execution
- Can skip entire stages (we saw synthesis agent being skipped)
- Non-deterministic behavior (LLM interprets instructions differently)
- Wastes tokens on orchestration decisions

**Solution: Custom Agent inheriting from BaseAgent:**
```python
class AudiobookPipelineAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        # YOU control execution order with Python code
        # GUARANTEED to run all stages
```

**Benefits:**
- ✅ **Deterministic**: Python control flow, no LLM skipping
- ✅ **Reliable**: Explicit error handling and retry logic
- ✅ **Efficient**: No wasted LLM calls for routing
- ✅ **Validated**: State checked between stages
- ✅ **Professional**: Industry-standard pattern for fixed pipelines

---

## Pipeline Stages

### Stage 1: DocumentExtractor
**Agent**: `LlmAgent` with document tools
**Tools**: `extract_text_from_txt`, `extract_text_from_pdf`, `get_document_metadata`
**Gemini Role**:
- Identify chapter breaks
- Detect dialogue vs narration
- Recognize metadata (TOC, headers, footers)
- Understand document structure

**Output**: `raw_text` → session state

---

### Stage 2: TextPreprocessor
**Agent**: `LlmAgent` with text tools
**Tools**: `clean_text`, `filter_unwanted_content`, `segment_text`
**Gemini Role**:
- Recognize garbage text vs meaningful content
- Identify repeated headers
- Understand structural meaning
- Find natural speech breaks
- Distinguish chapter intros from transitions

**Input**: `raw_text` from state
**Output**: `text_segments` → session state

---

### Stage 3: VoicePlanner
**Agent**: `LlmAgent` with voice tools
**Tools**: `detect_characters`, `analyze_text_gender`, `assign_voice_profile`
**Gemini Role**:
- Determine male/female voice
- Identify dialogue vs narration style
- Choose emotional tone (calm, excited, dramatic)
- Decide speed and prosody for sections
- Plan pacing for dramatic moments

**Input**: `text_segments` from state
**Output**: `voice_assignments` → session state

---

### Stage 4: AudioSynthesizer
**Agent**: `LlmAgent` with TTS tools
**Tools**: `synthesize_audio`, `cleanup_tts_resources`
**Gemini Role**:
- Decide retry parameters if synthesis fails
- Choose cloud vs local TTS
- Determine if text needs rewriting for TTS
- Handle error recovery
- Validate audio quality

**Input**: `text_segments`, `voice_assignments` from state
**Output**: `audio_chunks` → session state

**Special Feature**: Automatic retry logic (up to 3 attempts)
```python
for attempt in range(max_retries):
    try:
        async for event in self.synthesis_agent.run_async(ctx):
            yield event
        break
    except Exception as e:
        if attempt < max_retries - 1:
            logger.warning(f"Retrying... (attempt {attempt + 1})")
```

---

### Stage 5: AudioFinalizer
**Agent**: `LlmAgent` with audio tools
**Tools**: `merge_audio_chunks`, `normalize_audio`, `export_audio_format`, `get_audio_info`
**Gemini Role**:
- Verify all chunks are present
- Decide normalization levels
- Validate final audio quality
- Choose crossfade timing

**Input**: `audio_chunks` from state
**Output**: `final_audiobook` → session state

---

## State Management

### Session State Flow
```
DocumentExtractor → raw_text
                      ↓
TextPreprocessor   → text_segments
                      ↓
VoicePlanner       → voice_assignments
                      ↓
AudioSynthesizer   → audio_chunks
                      ↓
AudioFinalizer     → final_audiobook
```

### Validation Between Stages
Each stage validates required state exists before proceeding:
```python
if "raw_text" not in ctx.session.state:
    raise ValueError("Document extraction failed!")
```

This catches failures immediately instead of propagating errors.

---

## Error Handling

### Three Levels of Error Handling

**1. Tool Level** (`saa/tools/*.py`):
```python
def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    try:
        # ... extraction logic ...
        return {"status": "success", "text": extracted_text}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**2. Agent Level** (Gemini decides):
- Interprets tool errors
- Decides whether to retry
- Can rewrite problematic text
- Chooses alternative approaches

**3. Pipeline Level** (`_run_async_impl`):
```python
# Retry loop for critical stages
max_retries = 3
for attempt in range(max_retries):
    try:
        # Run synthesis agent
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        logger.warning("Retrying...")
```

---

## TTS Provider Strategy

### Dual Provider Architecture

**Replicate (Cloud)**:
- Fast, scalable
- No GPU required
- Requires API token
- Used first if available

**Local XTTS-v2 (GPU)**:
- Voice cloning capability
- Requires NVIDIA GPU
- Fallback if Replicate fails
- Module-level singleton for efficiency

### Automatic Fallback
```python
# In synthesize_audio tool
if settings.has_replicate_token:
    try:
        return replicate_provider.synthesize(...)
    except ReplicateAPIError:
        return {"status": "fallback_required"}

# Pipeline detects fallback and uses local
return local_provider.synthesize(...)
```

### Lazy Loading Pattern
```python
# saa/providers/__init__.py
def __getattr__(name):
    if name == "LocalTTSProvider":
        from .local_provider import LocalTTSProvider
        return LocalTTSProvider
```

**Why?** Direct scipy import hangs 60+ seconds on Windows. Lazy loading defers import until actually needed.

---

## Configuration Management

### Centralized Settings (Pydantic)
```python
# saa/config/settings.py
class Settings(BaseSettings):
    google_api_key: str
    gemini_text_model: str = "gemini-2.0-flash-lite"
    replicate_api_token: Optional[str] = None
    # ... 30+ settings ...

@lru_cache()
def get_settings() -> Settings:
    return Settings()  # Auto-loads .env
```

### Usage Throughout Codebase
```python
from saa.config import get_settings

settings = get_settings()
agent = LlmAgent(model=Gemini(model=settings.gemini_text_model))
```

**Never hardcode**:
- ❌ `model="gemini-2.0-flash-lite"`
- ❌ `load_dotenv(Path(...) / ".env")`

**Always use**:
- ✅ `model=settings.gemini_text_model`
- ✅ `settings = get_settings()`

---

## What Gemini Actually Does

### Document Understanding
- "Is this a chapter break?"
- "Should paragraphs be merged?"
- "Is this dialogue or narration?"
- "Is this metadata (TOC, footer, header)?"

### Cleaning Decisions
- Recognize garbage text
- Identify repeated headers
- Fix weird formatting
- Decide when to remove or keep a line

### Segmentation (Beyond Regex)
- "This paragraph feels like a chapter intro"
- "This looks like a new topic"
- "This part is a transition"

### Voice Planning
- Male/female voice selection
- Speed and prosody
- Emotional tone
- Dialogue vs narration style
- Pacing for dramatic sections

### Error Recovery
- Rewrite messy text
- Fix grammar
- Simplify sentences for TTS
- Reformat broken lines

### Pipeline Reasoning
- When to split more segments
- When to merge segments
- When to retry with different params
- When to use cloud vs local TTS
- When text chunk is too long
- When to remove entire junk block

---

## Comparison: Before vs After

### Before (Single LlmAgent)
```python
root_agent = LlmAgent(
    tools=[...15 tools...],
    instruction="Do all steps..."
)
# Problem: LLM decides which tools to call and when to stop
```

**Issues**:
- ❌ LLM skipped synthesis stage
- ❌ Non-deterministic execution
- ❌ Hard to debug which stage failed
- ❌ No retry logic

### After (Custom Agent)
```python
class AudiobookPipelineAgent(BaseAgent):
    async def _run_async_impl(self, ctx):
        async for event in self.document_agent.run_async(ctx):
            yield event
        # Validate state
        async for event in self.preprocessing_agent.run_async(ctx):
            yield event
        # Continue with guaranteed execution...
```

**Benefits**:
- ✅ All stages GUARANTEED to run
- ✅ Deterministic Python control flow
- ✅ Clear error messages per stage
- ✅ Automatic retry for TTS failures
- ✅ State validation between stages

---

## File Organization

```
AudioBook/
├── agents/
│   └── audiobook_pipeline/
│       ├── __init__.py
│       └── agent.py              # Custom Agent (300 lines)
├── saa/
│   ├── tools/                    # 15 function tools
│   │   ├── document_tools.py
│   │   ├── text_tools.py
│   │   ├── voice_tools.py
│   │   ├── tts_tools.py
│   │   └── audio_tools.py
│   ├── providers/                # TTS backends
│   │   ├── __init__.py           # Lazy loading
│   │   ├── local_provider.py     # XTTS-v2
│   │   └── replicate_provider.py # Cloud TTS
│   ├── config/
│   │   └── settings.py           # Pydantic config
│   └── cli/
│       └── app.py                # Click CLI
├── .env                          # API keys
└── .github/
    └── copilot-instructions.md   # AI agent guide
```

---

## Testing the System

### Quick Verification
```powershell
refreshenv
.\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING="utf-8"

# Test agent loads
python -c "from agents.audiobook_pipeline.agent import root_agent; print(root_agent.name)"
# Output: AudiobookPipeline

# Check config
python -m saa config

# Generate audiobook
python -m saa generate pre-input/sample.txt
```

### Expected Flow
1. **DocumentExtractor** extracts text (10s)
2. **TextPreprocessor** cleans and segments (15s)
3. **VoicePlanner** assigns voices (10s)
4. **AudioSynthesizer** generates TTS (60-120s for sample)
5. **AudioFinalizer** merges and exports (10s)

**Total**: ~2 minutes for sample.txt (37-second audiobook)

---

## Key Takeaways

1. **Custom Agent Pattern** = Professional-grade reliability
2. **5 Specialized Sub-Agents** = Clear separation of concerns
3. **Gemini Provides Intelligence** = Not just tool calling
4. **Tools Do The Work** = Actual extraction, synthesis, merging
5. **Deterministic Execution** = Python control flow, not LLM routing
6. **Robust Error Handling** = Retry logic, state validation
7. **Centralized Configuration** = Never hardcode settings

---

## Future Enhancements

- [ ] Parallel synthesis for multiple chunks (ParallelAgent for Stage 4)
- [ ] Memory integration for cross-session character voice consistency
- [ ] Streaming synthesis for real-time preview
- [ ] Multi-language support with language detection sub-agent
- [ ] Advanced emotion detection (integrate emotion_controller.py)
- [ ] Checkpoint/resume for long audiobooks (session system ready)

---

**Last Updated**: November 15, 2025  
**Architecture Version**: 2.0 (Custom Agent)  
**ADK Version**: 1.18.0+
