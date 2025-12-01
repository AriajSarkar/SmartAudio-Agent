"""
Smart resume tool for voice synthesis
Handles ALL resume logic internally - LLM just calls one function
"""
from pathlib import Path
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


def synthesize_remaining_chunks(
    job_state_path: str,
    chunks_json_path: str = "output/.temp/staged/chunks.json"
) -> Dict[str, Any]:
    """
    Synthesize ONLY the remaining chunks that haven't been completed yet.
    
    This tool handles ALL the resume logic:
    1. Reads state.json to see which chunks are already done
    2. Reads chunks.json to get all chunks
    3. Synthesizes ONLY the chunks that are NOT in completed_segments
    4. Updates state.json after each successful chunk
    
    The LLM doesn't need to filter or decide - this tool does everything!
    
    Args:
        job_state_path: Path to JobState JSON (state.json)
        chunks_json_path: Path to chunks.json file
    
    Returns:
        Dictionary with synthesis results
    """
    try:
        from saa.models import JobState
        from saa.tools.tts_tools import synthesize_audio, cleanup_tts_resources
        
        # Load state to see what's done
        state_path = Path(job_state_path)
        if state_path.exists():
            state = JobState.load(state_path)
            completed_ids = set(state.completed_segments)
            total_expected = state.total_segments
            logger.info(f"[Resume] Loaded state: {len(completed_ids)}/{total_expected} chunks complete")
            logger.info(f"[Resume] Completed chunks: {sorted(completed_ids)}")
        else:
            completed_ids = set()
            total_expected = 0
            logger.info(f"[Resume] No state file, will synthesize all chunks")
        
        # Load all chunks
        chunks_path = Path(chunks_json_path)
        if not chunks_path.exists():
            return {
                "status": "error",
                "error": f"Chunks file not found: {chunks_json_path}",
                "chunks_synthesized": 0,
                "chunks_skipped": 0
            }
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
            all_chunks = chunks_data.get("chunks", [])
        
        # Filter to ONLY pending chunks
        pending_chunks = [c for c in all_chunks if c["id"] not in completed_ids]
        
        logger.info(f"[Resume] Total chunks: {len(all_chunks)}")
        logger.info(f"[Resume] Already complete: {len(completed_ids)}")
        logger.info(f"[Resume] Pending synthesis: {len(pending_chunks)}")
        logger.info(f"[Resume] Pending chunk IDs: {[c['id'] for c in pending_chunks]}")
        
        if not pending_chunks:
            logger.info(f"[Resume] All chunks already synthesized!")
            return {
                "status": "success",
                "message": "All chunks already complete",
                "chunks_synthesized": 0,
                "chunks_skipped": len(completed_ids),
                "total_chunks": len(all_chunks)
            }
        
        # Synthesize each pending chunk
        synthesized_count = 0
        failed_chunks = []
        
        for chunk in pending_chunks:
            chunk_id = chunk["id"]
            logger.info(f"[Resume] Synthesizing chunk {chunk_id}/{len(all_chunks)-1}...")
            
            # Map voice to reference audio
            ref_audio = "reference_audio/male.wav"
            if chunk.get("voice") == "female":
                ref_audio = "reference_audio/female.wav"
            
            # Synthesize this chunk
            result = synthesize_audio(
                text=chunk["text"],
                output_path=f"chunk_{chunk_id:04d}.wav",
                reference_audio=ref_audio,
                voice=chunk.get("voice", "neutral"),
                speed=chunk.get("speed", 1.0),
                use_temp_dir=True,
                chunk_id=chunk_id,
                job_state_path=job_state_path
            )
            
            if result.get("status") == "success":
                synthesized_count += 1
                logger.info(f"[Resume] ✓ Chunk {chunk_id} complete ({synthesized_count}/{len(pending_chunks)})")
            else:
                failed_chunks.append(chunk_id)
                logger.error(f"[Resume] ✗ Chunk {chunk_id} failed: {result.get('error')}")
        
        # Cleanup
        cleanup_tts_resources()
        
        return {
            "status": "success",
            "chunks_synthesized": synthesized_count,
            "chunks_skipped": len(completed_ids),
            "total_chunks": len(all_chunks),
            "failed_chunks": failed_chunks,
            "message": f"Synthesized {synthesized_count} chunks (skipped {len(completed_ids)} already complete)"
        }
    
    except Exception as e:
        logger.error(f"[Resume] Fatal error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "chunks_synthesized": 0,
            "chunks_skipped": 0
        }


__all__ = ["synthesize_remaining_chunks"]
