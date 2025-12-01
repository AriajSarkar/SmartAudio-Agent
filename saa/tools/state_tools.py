"""
Tool for VoiceGenerationAgent to get chunks that need synthesis
Returns pre-filtered chunks ready to synthesize
"""
from pathlib import Path
from typing import Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)


def get_chunks_to_synthesize(job_state_path: str, chunks_json_path: str = "output/.temp/staged/chunks.json") -> Dict[str, Any]:
    """
    Get the EXACT list of chunks that need to be synthesized (pre-filtered).
    
    This tool does ALL the filtering work for you:
    1. Reads the JobState to see which chunks are complete
    2. Reads chunks.json to get all chunks
    3. FILTERS to only return pending chunks
    4. Returns ready-to-use chunk list
    
    Args:
        job_state_path: Path to JobState JSON file
        chunks_json_path: Path to chunks.json file
    
    Returns:
        Dictionary with:
            - status: "success" or "error"
            - chunks_to_synthesize: List of chunk objects that NEED synthesis
            - total_chunks: Total number of chunks
            - completed_count: Number already complete
            - pending_count: Number that need synthesis
            - skipped_chunks: List of chunk IDs being skipped
    """
    try:
        from saa.models import JobState
        
        # Load state
        state_path = Path(job_state_path)
        if not state_path.exists():
            logger.warning(f"[Resume] State file not found, will synthesize ALL chunks")
            # No state file - read all chunks
            chunks_path = Path(chunks_json_path)
            if not chunks_path.exists():
                return {
                    "status": "error",
                    "error": f"Chunks file not found: {chunks_json_path}",
                    "chunks_to_synthesize": [],
                    "total_chunks": 0,
                    "completed_count": 0,
                    "pending_count": 0
                }
            
            with open(chunks_path, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
                all_chunks = chunks_data.get("chunks", [])
                
            return {
                "status": "success",
                "chunks_to_synthesize": all_chunks,
                "total_chunks": len(all_chunks),
                "completed_count": 0,
                "pending_count": len(all_chunks),
                "skipped_chunks": []
            }
        
        # Load state
        state = JobState.load(state_path)
        completed_ids = set(state.completed_segments)
        
        # Load chunks
        chunks_path = Path(chunks_json_path)
        if not chunks_path.exists():
            return {
                "status": "error",
                "error": f"Chunks file not found: {chunks_json_path}",
                "chunks_to_synthesize": [],
                "total_chunks": 0,
                "completed_count": 0,
                "pending_count": 0
            }
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
            all_chunks = chunks_data.get("chunks", [])
        
        # FILTER to only pending chunks
        pending_chunks = [chunk for chunk in all_chunks if chunk["id"] not in completed_ids]
        
        result = {
            "status": "success",
            "chunks_to_synthesize": pending_chunks,
            "total_chunks": len(all_chunks),
            "completed_count": len(completed_ids),
            "pending_count": len(pending_chunks),
            "skipped_chunks": sorted(list(completed_ids))
        }
        
        logger.info(f"[Resume] Returning {len(pending_chunks)} chunks to synthesize (skipping {len(completed_ids)} completed)")
        logger.info(f"[Resume] Skipped chunk IDs: {sorted(list(completed_ids))}")
        logger.info(f"[Resume] Pending chunk IDs: {[c['id'] for c in pending_chunks]}")
        
        return result
    
    except Exception as e:
        logger.error(f"[Resume] Failed to get chunks: {e}")
        return {
            "status": "error",
            "error": str(e),
            "chunks_to_synthesize": [],
            "total_chunks": 0,
            "completed_count": 0,
            "pending_count": 0
        }


__all__ = ["get_chunks_to_synthesize"]
