"""
File manipulation tools for ADK agents.
"""
import json
from pathlib import Path
from typing import Dict, Any

def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to JSON file to read
        
    Returns:
        Dictionary with status and parsed JSON data
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_path}"
            }
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "data": data,
            "file_path": str(path.absolute())
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def save_json_file(file_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save data to a JSON file.
    
    Args:
        file_path: Path to save the JSON file
        data: Dictionary data to save
        
    Returns:
        Dictionary with status and file path
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "file_path": str(path.absolute())
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def update_chunk_text(file_path: str, chunk_id: int, new_text: str) -> Dict[str, Any]:
    """
    Update the text of a specific chunk in the JSON file.
    
    Args:
        file_path: Path to chunks.json
        chunk_id: ID of the chunk to update
        new_text: The new refined text
        
    Returns:
        Status dictionary
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "error": "File not found"}
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        chunks = data.get("chunks", [])
        updated = False
        
        for chunk in chunks:
            if chunk.get("id") == chunk_id:
                chunk["text"] = new_text
                updated = True
                break
        
        if not updated:
            return {"status": "error", "error": f"Chunk ID {chunk_id} not found"}
            
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return {
            "status": "success",
            "message": f"Updated chunk {chunk_id}",
            "new_text_preview": new_text[:50] + "..."
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
