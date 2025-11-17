"""
Example: Using SAA with Different LLM Providers
Demonstrates Ollama, OpenRouter, and Gemini configuration
"""
import asyncio
import logging
from pathlib import Path
import os

# SAA imports
from saa.agents.orchestrator import AudiobookOrchestrator
from saa.models import get_model_provider
from saa.config import get_settings


async def example_with_gemini():
    """
    Example 1: Generate audiobook with Gemini (default).
    
    Configuration (.env):
    LLM_PROVIDER=gemini
    GOOGLE_API_KEY=your_google_api_key
    GEMINI_TEXT_MODEL=gemini-2.0-flash-lite
    """
    print("=" * 60)
    print("EXAMPLE 1: Using Gemini (Default Provider)")
    print("=" * 60)
    
    settings = get_settings()
    print(f"\n✅ LLM Provider: {settings.llm_provider}")
    print(f"📦 Model: {settings.gemini_text_model}")
    
    # Create orchestrator (uses Gemini automatically)
    orchestrator = AudiobookOrchestrator(
        input_file=Path("input/sample.txt"),
        output_dir=Path("output")
    )
    
    print("\n🚀 Pipeline created with Gemini")
    print("   All 5 agents will use Gemini for reasoning")
    
    # Uncomment to run:
    # result = await orchestrator.run_async()
    # print(f"\n✅ Audiobook generated: {result['output_files']['final_mp3']}")


async def example_with_ollama():
    """
    Example 2: Generate audiobook with local Ollama.
    
    Configuration (.env):
    LLM_PROVIDER=ollama
    OLLAMA_MODEL=mistral-small3.1
    OLLAMA_API_BASE=http://localhost:11434
    
    Prerequisites:
    1. Install Ollama: https://ollama.ai/download
    2. Start Ollama: `ollama serve`
    3. Pull model: `ollama pull mistral-small3.1`
    """
    print("=" * 60)
    print("EXAMPLE 2: Using Local Ollama")
    print("=" * 60)
    
    settings = get_settings()
    print(f"\n✅ LLM Provider: {settings.llm_provider}")
    print(f"📦 Ollama Model: {settings.ollama_model}")
    print(f"🌐 API Base: {settings.ollama_api_base or 'http://localhost:11434 (default)'}")
    
    # Verify Ollama is running
    print("\n🔍 Verifying Ollama connection...")
    # Add health check here if needed
    
    # Create orchestrator (uses Ollama automatically)
    orchestrator = AudiobookOrchestrator(
        input_file=Path("input/sample.txt"),
        output_dir=Path("output")
    )
    
    print("\n🚀 Pipeline created with Ollama")
    print("   All 5 agents will use local Ollama for reasoning")
    print("   No API costs - runs entirely on your machine!")
    
    # Uncomment to run:
    # result = await orchestrator.run_async()


async def example_with_openrouter():
    """
    Example 3: Generate audiobook with OpenRouter.
    
    Configuration (.env):
    LLM_PROVIDER=openrouter
    OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
    OPENROUTER_API_KEY=your_openrouter_key
    
    Available Models:
    - anthropic/claude-3.5-sonnet (recommended)
    - google/gemini-2.5-flash
    - meta-llama/llama-3.3-70b-instruct
    - openai/gpt-4o
    """
    print("=" * 60)
    print("EXAMPLE 3: Using OpenRouter")
    print("=" * 60)
    
    settings = get_settings()
    print(f"\n✅ LLM Provider: {settings.llm_provider}")
    print(f"📦 OpenRouter Model: {settings.openrouter_model}")
    
    # Create orchestrator (uses OpenRouter automatically)
    orchestrator = AudiobookOrchestrator(
        input_file=Path("input/sample.txt"),
        output_dir=Path("output")
    )
    
    print("\n🚀 Pipeline created with OpenRouter")
    print("   All 5 agents will use OpenRouter for reasoning")
    print("   Access to multiple LLM providers through one API")
    
    # Uncomment to run:
    # result = await orchestrator.run_async()


async def example_with_custom_model():
    """
    Example 4: Override model programmatically.
    
    Useful for testing different models without changing .env
    """
    print("=" * 60)
    print("EXAMPLE 4: Custom Model Override")
    print("=" * 60)
    
    # Direct model override (bypasses .env)
    from google.adk.agents import LlmAgent
    from google.adk.models.lite_llm import LiteLlm
    
    custom_model = LiteLlm(model="ollama_chat/llama3.1")
    print(f"\n✅ Custom Model: ollama_chat/llama3.1")
    
    # Create agent with custom model
    agent = LlmAgent(
        name="TestAgent",
        model=custom_model,
        instruction="You are a helpful assistant."
    )
    
    print("\n🚀 Agent created with custom Ollama model")
    print("   Useful for testing different models")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("SAA Multi-Provider Examples")
    print("=" * 60)
    
    # Show current configuration
    settings = get_settings()
    print(f"\nCurrent Configuration:")
    print(f"  LLM Provider: {settings.llm_provider}")
    print(f"  Gemini Model: {settings.gemini_text_model}")
    print(f"  Ollama Model: {settings.ollama_model}")
    print(f"  OpenRouter Model: {settings.openrouter_model}")
    
    # Run examples
    await example_with_gemini()
    print("\n")
    
    await example_with_ollama()
    print("\n")
    
    await example_with_openrouter()
    print("\n")
    
    await example_with_custom_model()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
    print("\nTo actually run the pipeline, uncomment the `result = await orchestrator.run_async()` lines")


if __name__ == "__main__":
    asyncio.run(main())
