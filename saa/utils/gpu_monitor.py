"""
GPU monitoring utilities for SAA
Tracks VRAM usage and provides warnings
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_gpu_info() -> Dict[str, Any]:
    """
    Get GPU information including VRAM usage.
    
    Returns:
        Dictionary with GPU info:
        - available: bool (GPU available)
        - device_name: str (GPU model)
        - total_memory_gb: float (total VRAM)
        - allocated_memory_gb: float (currently allocated)
        - free_memory_gb: float (free VRAM)
        - utilization_percent: float (% of VRAM used)
    
    Example:
        >>> info = get_gpu_info()
        >>> print(f"GPU: {info['device_name']}, Free: {info['free_memory_gb']:.2f} GB")
    """
    try:
        import torch
        
        if not torch.cuda.is_available():
            return {
                "available": False,
                "device_name": "N/A",
                "total_memory_gb": 0.0,
                "allocated_memory_gb": 0.0,
                "free_memory_gb": 0.0,
                "utilization_percent": 0.0,
            }
        
        device = torch.cuda.current_device()
        total_memory = torch.cuda.get_device_properties(device).total_memory
        allocated_memory = torch.cuda.memory_allocated(device)
        free_memory = total_memory - allocated_memory
        
        total_gb = total_memory / 1e9
        allocated_gb = allocated_memory / 1e9
        free_gb = free_memory / 1e9
        utilization = (allocated_memory / total_memory) * 100
        
        return {
            "available": True,
            "device_name": torch.cuda.get_device_name(device),
            "total_memory_gb": round(total_gb, 2),
            "allocated_memory_gb": round(allocated_gb, 2),
            "free_memory_gb": round(free_gb, 2),
            "utilization_percent": round(utilization, 1),
        }
    
    except ImportError:
        logger.warning("PyTorch not installed - GPU monitoring unavailable")
        return {
            "available": False,
            "device_name": "PyTorch not installed",
            "total_memory_gb": 0.0,
            "allocated_memory_gb": 0.0,
            "free_memory_gb": 0.0,
            "utilization_percent": 0.0,
        }
    except Exception as e:
        logger.error(f"Error getting GPU info: {e}")
        return {
            "available": False,
            "device_name": f"Error: {str(e)}",
            "total_memory_gb": 0.0,
            "allocated_memory_gb": 0.0,
            "free_memory_gb": 0.0,
            "utilization_percent": 0.0,
        }


def check_gpu_memory(threshold_percent: float = 90.0) -> Dict[str, Any]:
    """
    Check GPU memory usage and warn if above threshold.
    
    Args:
        threshold_percent: Warning threshold (default 90%)
    
    Returns:
        Dictionary with:
        - status: "ok", "warning", or "critical"
        - message: Status message
        - info: GPU info from get_gpu_info()
    
    Example:
        >>> result = check_gpu_memory(threshold_percent=85.0)
        >>> if result["status"] == "warning":
        ...     print(result["message"])
    """
    info = get_gpu_info()
    
    if not info["available"]:
        return {
            "status": "ok",
            "message": "GPU not available",
            "info": info
        }
    
    utilization = info["utilization_percent"]
    
    if utilization >= threshold_percent:
        status = "critical" if utilization >= 95.0 else "warning"
        message = (
            f"⚠️ GPU memory {utilization}% full "
            f"({info['allocated_memory_gb']:.2f}/{info['total_memory_gb']:.2f} GB) "
            f"- Consider cleanup or reducing batch size"
        )
        logger.warning(message)
        
        return {
            "status": status,
            "message": message,
            "info": info
        }
    
    return {
        "status": "ok",
        "message": f"GPU memory healthy ({utilization}% used)",
        "info": info
    }


def cleanup_gpu_memory() -> bool:
    """
    Force GPU memory cleanup.
    
    Returns:
        True if cleanup successful, False otherwise
    
    Example:
        >>> if cleanup_gpu_memory():
        ...     print("GPU memory freed")
    """
    try:
        import torch
        import gc
        
        if not torch.cuda.is_available():
            return False
        
        # Force garbage collection
        gc.collect()
        
        # Empty CUDA cache
        torch.cuda.empty_cache()
        
        # Synchronize
        torch.cuda.synchronize()
        
        logger.info("✓ GPU memory cleanup completed")
        return True
    
    except ImportError:
        logger.warning("PyTorch not installed - cannot cleanup GPU")
        return False
    except Exception as e:
        logger.error(f"GPU cleanup failed: {e}")
        return False
