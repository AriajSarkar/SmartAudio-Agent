# LLM Provider Support

SAA now supports **3 LLM providers** for agent reasoning:

1. **Gemini** (default) - Google's Gemini models via API
2. **Ollama** (local) - Run models locally on your machine (free, no API costs)
3. **OpenRouter** (cloud) - Access to multiple LLM providers through one API

**IMPORTANT**: This is for **agent reasoning only**, NOT for TTS (text-to-speech). TTS continues to use Replicate (cloud) or local XTTS-v2.

## Configuration

### Gemini (Default)
```bash
# .env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key
GEMINI_TEXT_MODEL=gemini-2.0-flash-lite  # Optional, has default
```

### Ollama (Local LLM - No API Key Needed)
```bash
# .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral-small3.1
OLLAMA_API_BASE=http://localhost:11434  # Optional, defaults to this
OLLAMA_API_KEY=placeholder  # Placeholder for future cloud Ollama support
```

**Setup Ollama**:
1. Install: https://ollama.ai/download
2. Start server: `ollama serve`
3. Pull model: `ollama pull mistral-small3.1`
4. Recommended models with tool support:
   - `mistral-small3.1` (24B params, excellent for agents)
   - `llama3.1:70b` (powerful, slower)
   - `qwen2.5-coder:32b` (code-focused)

**Verify Ollama**:
```powershell
# Check running models
ollama list

# Test model
ollama run mistral-small3.1
```

### OpenRouter (Cloud LLM - Multiple Providers)
```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=your_openrouter_key
```

**Get OpenRouter Key**: https://openrouter.ai/keys

**Popular Models**:
- `anthropic/claude-3.5-sonnet` (recommended for agents)
- `google/gemini-2.5-flash` (fast, cost-effective)
- `meta-llama/llama-3.3-70b-instruct` (open-source)
- `openai/gpt-4o` (powerful, expensive)

## Usage

### Environment-Based (Recommended)
All agents automatically use the configured provider from `.env`:

```python
from saa.agents.orchestrator import AudiobookOrchestrator

# Uses provider from LLM_PROVIDER env var
orchestrator = AudiobookOrchestrator(
    input_file="input/book.pdf"
)
result = await orchestrator.run_async()
```

### Programmatic Override
Override provider for specific agents:

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Use specific Ollama model
agent = LlmAgent(
    name="CustomAgent",
    model=LiteLlm(model="ollama_chat/llama3.1"),
    instruction="..."
)
```

### Provider Factory API
Direct access to provider factory:

```python
from saa.models import get_model_provider

# Get configured provider
provider = get_model_provider()

# Override with specific model
custom_provider = get_model_provider("ollama_chat/mistral-small3.1")
```

## Examples

See `examples/llm_providers.py` for complete examples:

```powershell
# Run examples (shows configuration without executing pipeline)
python examples/llm_providers.py
```

Examples demonstrate:
1. Using Gemini (default)
2. Using local Ollama
3. Using OpenRouter
4. Programmatic model override

## Technical Details

### LiteLlm Integration
SAA uses Google ADK's `LiteLlm` wrapper for OpenAI-compatible endpoints:

```python
from google.adk.models.lite_llm import LiteLlm

# Ollama (IMPORTANT: Use "ollama_chat" prefix to avoid loops)
ollama_model = LiteLlm(model="ollama_chat/mistral-small3.1")

# OpenRouter
openrouter_model = LiteLlm(model="openrouter/anthropic/claude-3.5-sonnet")
```

### Environment Variables Required

**Ollama**:
```bash
OLLAMA_API_BASE=http://localhost:11434  # Auto-detected if omitted
# NO API KEY NEEDED for local Ollama
```

**OpenRouter**:
```bash
OPENROUTER_API_KEY=your_key  # REQUIRED
```

### Provider Selection Logic
`saa/models/provider_factory.py`:

1. Check `LLM_PROVIDER` env var
2. If "ollama" → `LiteLlm(model="ollama_chat/{OLLAMA_MODEL}")`
3. If "openrouter" → `LiteLlm(model="openrouter/{OPENROUTER_MODEL}")`
4. Default → `Gemini(model={GEMINI_TEXT_MODEL})`

### Adding New Providers

To add a new LiteLlm-compatible provider:

1. Add provider enum to `settings.py`:
```python
llm_provider: Literal["gemini", "ollama", "openrouter", "yourprovider"]
```

2. Add configuration fields:
```python
yourprovider_model: str = Field(default="default-model")
yourprovider_api_key: Optional[str] = Field(default=None)
```

3. Update `provider_factory.py`:
```python
elif llm_provider == "yourprovider":
    return LiteLlm(model=f"yourprovider/{settings.yourprovider_model}")
```

4. Update `.env.example` with configuration template

## Troubleshooting

### Ollama Connection Failed
```
Error: Connection refused to http://localhost:11434
```
**Solution**: Start Ollama server
```powershell
ollama serve
```

### Ollama Model Not Found
```
Error: model "mistral-small3.1" not found
```
**Solution**: Pull the model
```powershell
ollama pull mistral-small3.1
```

### OpenRouter Authentication Error
```
Error: Invalid API key
```
**Solution**: Get valid key from https://openrouter.ai/keys

### Infinite Tool Call Loops (Ollama)
```
Agent keeps calling same tool repeatedly
```
**Solution**: Use `ollama_chat` prefix, NOT `ollama`
```python
# ✅ CORRECT
LiteLlm(model="ollama_chat/mistral-small3.1")

# ❌ WRONG (causes loops)
LiteLlm(model="ollama/mistral-small3.1")
```

## Performance Comparison

| Provider | Speed | Cost | Quality | Notes |
|----------|-------|------|---------|-------|
| **Gemini 2.0 Flash** | ⚡⚡⚡ | $ | ⭐⭐⭐⭐ | Best balance, cloud API |
| **Ollama (Mistral)** | ⚡⚡ | FREE | ⭐⭐⭐ | Local, no API costs, GPU needed |
| **OpenRouter (Claude)** | ⚡⚡ | $$$ | ⭐⭐⭐⭐⭐ | Highest quality, expensive |
| **OpenRouter (Llama)** | ⚡ | $ | ⭐⭐⭐ | Open-source, cost-effective |

## Best Practices

1. **Development**: Use Gemini (fast iteration, reliable)
2. **Production (cost-sensitive)**: Use Ollama (free, requires GPU)
3. **Production (quality-critical)**: Use OpenRouter Claude (best reasoning)
4. **Testing**: Mix providers to ensure provider-agnostic code

## Known Limitations

1. **Ollama requires local GPU**: CPU-only Ollama is very slow
2. **OpenRouter rate limits**: Varies by model, check dashboard
3. **Gemini API quotas**: Free tier has limits, upgrade for production
4. **Model compatibility**: Not all models support function calling equally well

## Future Enhancements

- [ ] Cloud Ollama support (when available)
- [ ] Custom LiteLlm configurations (temperature, etc.)
- [ ] Provider-specific optimizations
- [ ] Cost tracking per provider
- [ ] Automatic provider failover (Gemini → Ollama)

## Related Documentation

- ADK LiteLlm: https://github.com/google/adk-python/tree/main/src/google/adk/models/lite_llm.py
- Ollama Models: https://ollama.com/library
- OpenRouter Models: https://openrouter.ai/models
- Gemini Pricing: https://ai.google.dev/pricing
