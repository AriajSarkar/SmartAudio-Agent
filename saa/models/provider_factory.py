"""
LLM Provider Factory

Dynamically selects LLM provider (Gemini, Ollama, OpenRouter) based on environment configuration.
Uses Google ADK's LiteLlm wrapper for OpenAI-compatible endpoints (Ollama, OpenRouter).
"""
from typing import Union
from google.adk.models import Gemini, BaseLlm
from google.adk.models.lite_llm import LiteLlm
from saa.config import get_settings


def get_model_provider(model_override: str = None) -> Union[Gemini, LiteLlm]:
    """
    Get configured LLM provider based on environment settings.
    
    **Provider Selection Logic**:
    1. Check LLM_PROVIDER env var ("gemini" | "ollama" | "openrouter")
    2. If model_override provided, use that directly with LiteLlm
    3. Fallback to Gemini with configured model
    
    **Ollama Setup**:
    - Set LLM_PROVIDER=ollama
    - Set OLLAMA_API_BASE=http://localhost:11434 (optional)
    - Set OLLAMA_MODEL=mistral-small3.1 (or any installed model)
    - No API key needed for local Ollama
    
    **OpenRouter Setup**:
    - Set LLM_PROVIDER=openrouter
    - Set OPENROUTER_API_KEY=your_key_here
    - Set OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
    
    **Gemini Setup** (default):
    - Set GOOGLE_API_KEY=your_google_key
    - Uses GEMINI_TEXT_MODEL from settings
    
    Args:
        model_override: Optional model string to override config (e.g., "ollama_chat/llama3.1")
    
    Returns:
        Configured LLM provider (Gemini or LiteLlm wrapper)
    
    Example:
        >>> # Using environment-based selection
        >>> provider = get_model_provider()
        >>> agent = LlmAgent(model=provider, ...)
        
        >>> # Direct model override
        >>> provider = get_model_provider("ollama_chat/mistral-small3.1")
    """
    settings = get_settings()
    
    # Direct model override (for testing or programmatic use)
    if model_override:
        return LiteLlm(model=model_override)
    
    # Environment-based provider selection
    llm_provider = settings.llm_provider.lower()
    
    if llm_provider == "ollama":
        # Ollama via LiteLlm (OpenAI-compatible)
        # CRITICAL: Use "ollama_chat" prefix to avoid infinite loops
        # See: https://github.com/google/adk-python/tree/main/contributing/samples/hello_world_ollama
        ollama_model = settings.ollama_model
        return LiteLlm(model=f"ollama_chat/{ollama_model}")
    
    elif llm_provider == "openrouter":
        # OpenRouter via LiteLlm
        openrouter_model = settings.openrouter_model
        return LiteLlm(model=f"openrouter/{openrouter_model}")
    
    else:
        # Default: Gemini
        return Gemini(model=settings.gemini_text_model)


def get_text_model() -> Union[Gemini, LiteLlm]:
    """
    Get text model provider (convenience wrapper).
    
    Returns:
        Configured LLM for text agents (11/12 agents use this)
    """
    return get_model_provider()


def get_pro_model() -> Union[Gemini, LiteLlm]:
    """
    Get pro model provider for complex tasks.
    
    If using Gemini, returns pro model. For Ollama/OpenRouter, 
    uses same model as text (user can override via OLLAMA_MODEL).
    
    Returns:
        Configured LLM for complex reasoning tasks
    """
    settings = get_settings()
    
    if settings.llm_provider.lower() == "gemini":
        return Gemini(model=settings.gemini_pro_model)
    else:
        # For Ollama/OpenRouter, use same model (or user can set different via env)
        return get_model_provider()
