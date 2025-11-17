# SAA Architecture - AgentTool Coordinator Pattern

## Overview

SAA (Smart Audio Agent) uses Google ADK's **AgentTool Coordinator pattern** for intelligent, file-based audiobook generation. This document explains the architectural decisions and actual implementation.

---

## Core Philosophy

```
Tools = Actions (extract, clean, synthesize, merge, verify files)
Gemini = Intelligence (workflow decisions, file verification, error handling)
Agents = Stage Executors (intelligence + tools for specific tasks)
Coordinator = Orchestrator (Gemini-powered agent that calls other agents as tools)
```

### What Each Component Does

**Tools** (17 functions in `saa/tools/` + 2 helpers):
- Perform actual work (PDF extraction, TTS synthesis, audio merging)
- Return structured data (`Dict[str, Any]` with status)
- No decision-making - just execute and report
- Examples: `extract_text_from_pdf`, `synthesize_audio`, `merge_audio_chunks`

**Gemini** (LLM reasoning engine):
- Understands document structure (chapters, dialogue, narration)
- Makes cleaning decisions (garbage text, headers, metadata)
- Interprets meaning (emotional tone, voice selection, pacing)
- **Coordinates workflow** (decides when to call which agent)
- **Verifies file outputs** (checks if stage completed successfully)
- Handles error recovery (rewrite messy text, retry with different params)

**Stage Agents** (5 specialized LlmAgents):
- Each wrapped as `AgentTool` for coordinator to call
- Focused responsibility and specific tools
- File-based I/O (read/write to `.temp/` directories)
- Use Gemini to make intelligent decisions before calling tools
- All have explicit `app_name="saa"` to avoid ADK warnings

**PipelineCoordinator** (LlmAgent with sub-agents as tools):
- Gemini-powered orchestrator that calls stage agents in order
- Verifies file outputs between stages using `verify_stage_output` tool
- Handles errors with `report_stage_error` tool
- Communicates progress to user

---

## Architecture: AgentTool Coordinator Pattern

### Why AgentTool Coordinator (Not SequentialAgent)?

**Initial Approach: SequentialAgent** ❌
```python
# This didn't work reliably
workflow = SequentialAgent(sub_agents=[agent1, agent2, agent3])
```
**Problems:**
- LLM decides when each sub-agent is "done" → skipped synthesis stage entirely
- `output_key` state passing caused hallucinations (LLM invented non-existent tools)
- No explicit file verification between stages
- Non-deterministic execution order

**Current Solution: AgentTool Coordinator** ✅
```python
# Coordinator agent with sub-agents as callable tools
coordinator = LlmAgent(
    name="PipelineCoordinator",
    app_name="saa",
    tools=[
        AgentTool(extraction_agent),
        AgentTool(staging_agent),
        AgentTool(voice_agent),
        AgentTool(merge_agent),
        AgentTool(cleanup_agent),
        verify_stage_output,  # File verification
        report_stage_error    # Error handling
    ]
)
```

**Benefits:**
- ✅ **Gemini Intelligence**: Coordinator uses Gemini to decide workflow logic
- ✅ **File-Based Verification**: Explicit file checks between stages
- ✅ **Error Recovery**: Coordinator can retry or skip failed stages intelligently
- ✅ **Clear Communication**: Coordinator reports "OK - Stage X complete" messages
- ✅ **Flexible**: Can handle partial failures and continue

---

## Pipeline Stages (File-Based Coordination)

### Stage 1: ExtractionAgent
**File**: `saa/agents/extraction_agent.py`  
**Tools**: `extract_text_from_txt`, `extract_text_from_pdf`, `get_document_metadata`

**Gemini Intelligence**:
- Identifies document type (PDF/TXT)
- Chooses appropriate extraction tool
- Handles multi-page PDFs
- Detects chapter breaks in text

**File Output**: `output/.temp/extracted/extracted.txt`

**Coordinator Verification**:
```python
verify_stage_output("ExtractionAgent", "output/.temp/extracted/extracted.txt")
# Returns: {"exists": true, "path": "...", "size_bytes": 899}
```

---

### Stage 2: StagingAgent
**File**: `saa/agents/staging_agent.py`  
**Tools**: `read_text_file`, `clean_text`, `segment_text`, `filter_unwanted_content`, `detect_characters`, `analyze_text_gender`, `assign_voice_profile`

**Gemini Intelligence**:
- Recognizes garbage text vs meaningful content
- Understands natural speech breaks
- Detects gender/emotion from context
- Assigns appropriate voice profiles
- Plans pacing and prosody adjustments

**Workflow**:
1. Read `output/.temp/extracted/extracted.txt`
2. Clean text (remove OCR artifacts, normalize whitespace)
3. Segment into chunks (200 chars max for TTS quality)
4. Detect characters and assign voices
5. Save chunks.json with voice metadata

**File Output**: `output/.temp/staged/chunks.json`

**JSON Format**:
```json
{
  "chunks": [
    {
      "id": 0,
      "text": "cleaned chunk text",
      "voice": "male",
      "speed": 1.0,
      "emotion": "neutral"
    }
  ]
}
```

**Coordinator Verification**:
```python
verify_stage_output("StagingAgent", "output/.temp/staged/chunks.json")
```

---

### Stage 3: VoiceGenerationAgent
**File**: `saa/agents/voice_generation_agent.py`  
**Tools**: `read_json_file`, `synthesize_audio`, `cleanup_tts_resources`

**Gemini Intelligence**:
- Decides retry parameters for failed synthesis
- Chooses cloud vs local TTS strategy
- Handles error recovery (text rewriting)
- Optimizes synthesis quality settings
- Manages GPU resources

**Workflow**:
1. Read `output/.temp/staged/chunks.json`
2. For each chunk, call `synthesize_audio`:
   - Map voice to reference audio: `neutral/male/narrator` → `male.wav`, `female` → `female.wav`
   - Set output path: `voices/chunk_XXXX.wav` (preserves subdirectory)
   - Use `use_temp_dir=True` to save to `.temp/`
3. Cleanup GPU resources after synthesis

**File Output**: `output/.temp/voices/chunk_0000.wav`, `chunk_0001.wav`, ...

**Coordinator Verification**:
```python
verify_stage_output("VoiceGenerationAgent", "output/.temp/voices")
# Checks directory exists and contains WAV files
```

---

### Stage 4: MergeAgent
**File**: `saa/agents/merge_agent.py`  
**Tools**: `list_audio_files`, `merge_audio_chunks`, `normalize_audio`, `export_audio_format`, `get_audio_info`

**Gemini Intelligence**:
- Decides merge strategy (concat vs crossfade)
- Chooses normalization levels
- Adjusts export quality settings
- Handles large file optimization

**Workflow**:
1. List all files: `list_audio_files("output/.temp/voices")`
2. Merge chunks: `merge_audio_chunks(chunks, ".temp/voices/merged.wav")`
   - **CRITICAL**: Do NOT use `"output/"` prefix - tools add it automatically
   - Avoids `output/output/` double nesting bug
3. Export to final formats:
   - WAV: `{job_id}/final.wav`
   - MP3: `{job_id}/final.mp3` (with `cleanup_input=False` to preserve WAV)

**File Output**: `output/{job_id}/final.wav`, `output/{job_id}/final.mp3`

**Coordinator Verification**:
```python
verify_stage_output("MergeAgent", "output/{job_id}/final.wav")
```

---

### Stage 5: CleanupAgent
**File**: `saa/agents/cleanup_agent.py`  
**Tools**: None (instructs WorkspaceManager via coordinator)

**Gemini Intelligence**:
- Verifies final audiobook exists before cleanup
- Decides what to keep for debugging
- Handles cleanup errors gracefully

**Workflow**:
1. Verify final output files exist
2. Report success to coordinator
3. Coordinator calls `workspace.cleanup()` to delete `.temp/` files

**File Output**: None (cleanup stage)

**Coordinator Action**: Delete all files in `.temp/extracted/`, `.temp/staged/`, `.temp/voices/`

---

## Temp Folder Structure

**Managed by**: `saa/utils/workspace.py` → `WorkspaceManager`

```
output/
  .temp/
    extracted/
      extracted.txt          # Stage 1 output
    staged/
      chunks.json            # Stage 2 output (with voice metadata)
    voices/
      chunk_0000.wav         # Stage 3 output
      chunk_0001.wav
      ...
  {job_id}/
    final.wav                # Stage 4 output
    final.mp3                # Stage 4 output (converted)
```

**WorkspaceManager Methods**:
- `setup()` - Create all temp directories
- `cleanup()` - Delete files, keep structure
- `save_extracted_text(text)` - Save to `.temp/extracted/`
- `save_chunks_json(chunks)` - Save to `.temp/staged/`
- `get_voice_chunk_path(id)` - Get path for voice chunk

---

## What Gemini Actually Does

### Document Understanding (Stage 1)
- "Is this a PDF or TXT file?"
- "Which extraction tool should I use?"
- "Does this have multiple pages?"

### Text Processing (Stage 2)
- "Is this garbage text or meaningful content?"
- "Where are natural sentence breaks?"
- "Should I split this paragraph?"
- "Is this dialogue or narration?"
- "What gender/emotion does this text convey?"

### Voice Planning (Stage 2 continued)
- "Male or female voice?"
- "What emotional tone?"
- "Speed and pacing?"

### Synthesis Coordination (Stage 3)
- "Which reference audio file for this voice?"
- "Did synthesis succeed?"
- "Should I retry or report error?"

### Merge Coordination (Stage 4)
- "Are all audio chunks present?"
- "What normalization level?"
- "Which export formats?"

### Pipeline Orchestration (Coordinator)
- "Did Stage 1 create the expected file?"
- "Should I proceed to Stage 2?"
- "Stage failed - should I retry or abort?"
- "Report progress: 'OK - Stage X complete'"

---

## TTS Character Limit Fix

**Problem**: XTTS-v2 warns about text >250 characters causing truncation.

**Solution**: Reduced segment sizes in `saa/constants.py`:
```python
MAX_SEGMENT_LENGTH: Final[int] = 250  # Actual TTS limit
SAFE_SEGMENT_LENGTH: Final[int] = 200  # Safety margin (prevents warnings)
```

**Impact**:
- More chunks created (better quality, no truncation)
- Slightly longer synthesis time
- Better voice consistency across segments

---

## ADK App Name Fix

**Problem**: ADK warning about app name mismatch:
```
WARNING: App name mismatch detected. Runner uses "saa" but agent loaded from "google.adk.agents"
```

**Solution**: Explicitly set `app_name="saa"` in all 6 agents:
```python
agent = LlmAgent(
    name="AgentName",
    model=Gemini(...),
    app_name="saa",  # FIX: Matches runner configuration
    ...
)
```

**Applied to**:
- ExtractionAgent
- StagingAgent
- VoiceGenerationAgent
- MergeAgent
- CleanupAgent
- PipelineCoordinator

---

## Error Handling

### Tool Level
All tools return `{"status": "success|error", ...}`:
```python
def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    try:
        # ... extraction logic ...
        return {"status": "success", "text": extracted_text}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### Agent Level
Gemini interprets tool errors and decides recovery:
- Retry with different parameters
- Rewrite problematic text
- Choose alternative approach

### Coordinator Level
File verification catches stage failures:
```python
result = verify_stage_output("StagingAgent", "output/.temp/staged/chunks.json")
if not result["exists"]:
    report_stage_error("StagingAgent", "chunks.json not created", ...)
    # Coordinator stops pipeline
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

# Coordinator detects fallback and retries with local
return local_provider.synthesize(...)
```

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
- ✅ `model=settings.gemini_text_model`

---

## File Organization

```
AudioBook/
├── saa/
│   ├── agents/                    # 5 stage agents + orchestrator
│   │   ├── extraction_agent.py
│   │   ├── staging_agent.py
│   │   ├── voice_generation_agent.py
│   │   ├── merge_agent.py
│   │   ├── cleanup_agent.py
│   │   └── orchestrator.py
│   ├── tools/                     # 17 ADK function tools
│   │   ├── document_tools.py
│   │   ├── text_tools.py
│   │   ├── voice_tools.py
│   │   ├── tts_tools.py
│   │   └── audio_tools.py
│   ├── providers/                 # TTS backends
│   │   ├── local_provider.py     # XTTS-v2
│   │   └── replicate_provider.py # Cloud TTS
│   ├── config/
│   │   └── settings.py           # Pydantic config
│   ├── cli/
│   │   └── app.py                # Click CLI
│   ├── utils/
│   │   ├── workspace.py          # Temp folder management
│   │   ├── logger.py
│   │   └── gpu_monitor.py
│   └── models/                    # Data classes
├── .env                           # API keys
└── output/
    ├── .temp/                     # Temp files (cleaned up)
    └── {job_id}/                  # Final audiobooks
```

---

## Testing the System

### Quick Verification
```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING="utf-8"

# Test config
python -m saa config

# Generate audiobook
python -m saa generate input/sample.txt
```

### Expected Flow
1. **ExtractionAgent** extracts text (5-10s)
2. **StagingAgent** creates chunks with voice metadata (10-15s)
3. **VoiceGenerationAgent** synthesizes audio (60-120s for sample)
4. **MergeAgent** merges and exports (10s)
5. **CleanupAgent** removes temp files (2s)

**Total**: ~2-3 minutes for short sample

---

## Key Takeaways

1. **AgentTool Pattern** = Gemini-powered orchestration with file verification
2. **5 Specialized Stage Agents** = Clear separation of concerns
3. **File-Based Coordination** = No output_key hallucinations, explicit verification
4. **Gemini Provides Intelligence** = Not just tool calling, but workflow decisions
5. **Tools Do The Work** = Actual extraction, synthesis, merging
6. **Explicit app_name** = Avoids ADK warnings
7. **200-char TTS Limit** = Prevents truncation warnings, better quality

---

## Common Pitfalls (Fixed!)

1. ❌ ~~Using SequentialAgent with output_key~~ → ✅ AgentTool coordinator with file verification
2. ❌ ~~750-char TTS segments causing warnings~~ → ✅ 200-char segments for quality
3. ❌ ~~Missing app_name causing warnings~~ → ✅ Explicit `app_name="saa"` in all agents
4. ❌ ~~Double `output/output/` path nesting~~ → ✅ Tools handle path prefixing
5. ❌ ~~Auto-deleting WAV after MP3 export~~ → ✅ `cleanup_input=False` parameter

---

**Last Updated**: November 17, 2025  
**Architecture Version**: 3.0 (AgentTool Coordinator)  
**ADK Version**: 1.18.0+
