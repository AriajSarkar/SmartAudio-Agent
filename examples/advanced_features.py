"""
Example: Using SAA with Observability and Sessions
Demonstrates ADK best practices for production agents
"""
import asyncio
import logging
from pathlib import Path

# SAA imports
from saa.agents.orchestrator import AudiobookOrchestrator
from saa.observability import create_observability_plugin
from saa.sessions import create_session_service
from saa.evaluation import create_evaluator

# ADK imports
from google.adk.runners import Runner


async def example_with_observability():
    """
    Example 1: Generate audiobook with comprehensive logging.
    
    LoggingPlugin captures:
    - All agent invocations
    - LLM requests/responses with token counts
    - Tool executions
    - Errors and exceptions
    """
    print("=" * 60)
    print("EXAMPLE 1: Observability with LoggingPlugin")
    print("=" * 60)
    
    # Create orchestrator
    orchestrator = AudiobookOrchestrator(
        input_file=Path("input/sample.txt"),
        output_dir=Path("output")
    )
    
    # Create pipeline with observability
    pipeline = orchestrator.create_pipeline()
    
    # Create observability plugin
    observability_plugin = create_observability_plugin()
    
    print("\n✅ Pipeline created with observability enabled")
    print("📊 LoggingPlugin captures:")
    print("   - All agent invocations")
    print("   - LLM requests/responses with token counts")
    print("   - Tool executions")
    print("   - Errors and exceptions")
    
    print("\n💡 In production, attach plugin to runner:")
    print("   runner = InMemoryRunner(agent=pipeline, plugins=[plugin])")
    print("   response = await runner.run_debug(prompt)")
    
    # Note: Full execution would run the pipeline
    # For demo purposes, we just show the setup
    print("\nTo run full pipeline: await orchestrator.run_async()")


async def example_with_sessions():
    """
    Example 2: Multi-turn conversation with session management.
    
    Sessions enable:
    - Conversation history retention
    - State management across queries
    - Context from previous turns
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Sessions for Multi-Turn Conversations")
    print("=" * 60)
    
    # Create session service (persistent)
    session_service = create_session_service(
        persistent=True,
        db_path="./sessions_demo.db"
    )
    
    print("\n✅ Session service created (persistent)")
    print("💾 Sessions saved to: sessions_demo.db")
    print("\nUse case: Chat-based audiobook configuration")
    print("  User: 'Generate audiobook from mybook.pdf'")
    print("  Agent: 'What voice should I use?'")
    print("  User: 'Use narrator voice'")
    print("  Agent: [Remembers previous context, proceeds with generation]")
    
    # Create session
    session = await session_service.create_session(
        app_name="saa",
        user_id="user_123",
        session_id="audiobook_config_1"
    )
    
    print(f"\n📝 Session created: {session.id}")


async def example_with_evaluation():
    """
    Example 3: Evaluate pipeline quality.
    
    Evaluator tests:
    - Text extraction accuracy
    - Chunk segmentation quality
    - End-to-end success rate
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Agent Evaluation")
    print("=" * 60)
    
    evaluator = create_evaluator()
    
    # Test extraction
    result = evaluator.evaluate_extraction(
        input_file="input/sample.txt",
        expected_chars=1000  # Approximate expected length
    )
    
    print("\n📊 Extraction Evaluation:")
    print(f"  Success: {result['success']}")
    print(f"  Actual chars: {result.get('actual_chars', 'N/A')}")
    if 'accuracy' in result:
        print(f"  Accuracy: {result['accuracy']:.2%}")
    
    # Test segmentation
    sample_text = "This is a sample text for testing. It has multiple sentences. Each should be segmented properly."
    seg_result = evaluator.evaluate_segmentation(
        text=sample_text,
        expected_segments=3
    )
    
    print("\n📊 Segmentation Evaluation:")
    print(f"  Success: {seg_result['success']}")
    print(f"  Segments: {seg_result.get('actual_segments', 'N/A')}")
    if 'accuracy' in seg_result:
        print(f"  Accuracy: {seg_result['accuracy']:.2%}")
    
    print("\n✅ Evaluation complete")
    print("💡 Use these metrics to track quality improvements over time")


async def main():
    """Run all examples."""
    print("\n" + "🎙️ SAA - Advanced Features Demo" + "\n")
    
    await example_with_observability()
    await example_with_sessions()
    await example_with_evaluation()
    
    print("\n" + "=" * 60)
    print("✨ All examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run actual pipeline: python -m saa generate input/sample.txt")
    print("2. Check observability logs: logs/observability.log")
    print("3. Inspect session database: sessions_demo.db")
    print("4. Review evaluation results for quality tracking")
    print("\nFor deployment: See docs/DEPLOYMENT.md")


if __name__ == "__main__":
    asyncio.run(main())
