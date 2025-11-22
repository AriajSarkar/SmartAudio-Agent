"""Integration test for full audiobook pipeline"""
import pytest
from pathlib import Path
from saa.agents.orchestrator import AudiobookOrchestrator


@pytest.mark.integration
@pytest.mark.slow
class TestAudiobookPipeline:
    """Integration tests for complete audiobook generation"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_creation(self):
        """Test that orchestrator can be created"""
        
        orchestrator = AudiobookOrchestrator(
            input_file=Path("input/sample.txt"),
            output_dir=Path("output")
        )
        
        assert orchestrator is not None
        assert orchestrator.job_id is not None
        
        # Create pipeline
        pipeline = orchestrator.create_pipeline()
        assert pipeline is not None
        assert pipeline.name == "PipelineCoordinator"
        assert len(pipeline.tools) == 7  # 5 agents + 2 debug tools
    
    @pytest.mark.asyncio
    async def test_pipeline_with_sample_text(self, sample_txt_path, temp_dir):
        """Test pipeline with sample TXT file"""
        # This is a mock test - real test would require API keys
        # For now, just verify the orchestrator can be instantiated
        
        try:
            orchestrator = AudiobookOrchestrator(
                input_file=sample_txt_path,
                output_dir=temp_dir
            )
            
            # Try to run (will fail without API key, which is expected)
            result = await orchestrator.run_async()
            
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
        orchestrator = AudiobookOrchestrator(
            input_file=sample_txt_path,
            output_dir=temp_dir
        )
        result = await orchestrator.run_async()
        print(
            f"Generate audiobook from: {str(sample_txt_path)}"
        )
        
        assert result["status"] == "success"
        assert result["error"] is None
        
        # Verify output exists
        output_files = list(temp_dir.glob("*.mp3")) + list(temp_dir.glob("*.wav"))
        assert len(output_files) > 0
