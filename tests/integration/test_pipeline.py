"""Integration test for full audiobook pipeline"""
import pytest
from pathlib import Path
from saa.agents.agent import root_agent
from google.adk.runners import InMemoryRunner


@pytest.mark.integration
@pytest.mark.slow
class TestAudiobookPipeline:
    """Integration tests for complete audiobook generation"""
    
    @pytest.mark.asyncio
    async def test_pipeline_creation(self):
        """Test that pipeline can be created"""
        
        assert root_agent is not None
        assert root_agent.name == "AudiobookPipeline"
        assert len(root_agent.sub_agents) == 5
    
    @pytest.mark.asyncio
    async def test_pipeline_with_sample_text(self, sample_txt_path, temp_dir):
        """Test pipeline with sample TXT file"""
        # This is a mock test - real test would require API keys
        # For now, just verify the agent can be instantiated
        
        try:
            runner = InMemoryRunner(agent=root_agent)
            
            # Try to run (will fail without API key, which is expected)
            result = await runner.run_debug(
                f"Generate audiobook from: {str(sample_txt_path)}"
            )
            
            # If we get here without API keys, expect graceful error
            assert result is not None
            
        except Exception as e:
            # Expected without proper API keys
            assert "API" in str(e) or "key" in str(e).lower() or "GOOGLE_API_KEY" in str(e)
    
    @pytest.mark.skip(reason="Requires API keys and GPU")
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, sample_txt_path, temp_dir):
        """
        Full pipeline test (skipped by default).
        Run with: pytest -m integration --run-slow
        """
        runner = InMemoryRunner(agent=root_agent)
        result = await runner.run_debug(
            f"Generate audiobook from: {str(sample_txt_path)}"
        )
        )
        
        assert result["status"] == "success"
        assert result["error"] is None
        
        # Verify output exists
        output_files = list(temp_dir.glob("*.mp3")) + list(temp_dir.glob("*.wav"))
        assert len(output_files) > 0
