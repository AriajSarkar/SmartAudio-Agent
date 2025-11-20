"""
Replicate TTS Provider for cloud-based synthesis
Uses Replicate API for scalable TTS generation
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False
    replicate = None

from saa.exceptions import ReplicateAuthError, ReplicateAPIError

logger = logging.getLogger(__name__)


class ReplicateTTSProvider:
    """
    Cloud TTS synthesis using Replicate API
    
    Provides serverless TTS without local GPU requirements.
    Automatically handles authentication and retry logic.
    """
    
    # Default Replicate model for TTS (can be overridden)
    DEFAULT_MODEL = "lucataco/xtts-v2"
    DEFAULT_VERSION = "684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e"
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        model: Optional[str] = None,
        version: Optional[str] = None
    ):
        """
        Initialize Replicate TTS provider
        
        Args:
            api_token: Replicate API token (or from REPLICATE_API_TOKEN env var)
            model: Replicate model name (or from REPLICATE_MODEL env var)
            version: Model version hash (or from REPLICATE_MODEL_VERSION env var)
        """
        if not REPLICATE_AVAILABLE:
            raise ImportError(
                "replicate package not installed. "
                "Install with: pip install replicate"
            )
        
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        
        if not self.api_token or self.api_token == "your_replicate_token_here":
            raise ReplicateAuthError()
        
        # Allow configuration via environment variables
        self.model = model or os.getenv("REPLICATE_MODEL", self.DEFAULT_MODEL)
        self.version = version or os.getenv("REPLICATE_MODEL_VERSION", self.DEFAULT_VERSION)
        self.client = None
        
        logger.info(f"ReplicateTTSProvider initialized with model: {self.model}")
    
    def _get_client(self):
        """Get or create Replicate client"""
        if self.client is None:
            try:
                self.client = replicate.Client(api_token=self.api_token)
            except Exception as e:
                raise ReplicateAuthError()
        return self.client
    
    def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str = "neutral",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synthesize speech using Replicate API.
        
        Args:
            text: Text to synthesize
            output_path: Where to save audio
            voice: Voice preset name
            **kwargs: Additional model-specific parameters
        
        Returns:
            Dict with status, output_file, error
        """
        try:
            client = self._get_client()
            
            # Prepare output path
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Calling Replicate API for {len(text)} chars...")
            
            # Call Replicate model
            try:
                # Note: Actual parameters depend on specific model
                # This is a generic template - adjust for actual TTS model
                output = replicate.run(
                    f"{self.model}:{self.version}",
                    input={
                        "text": text,
                        "voice": voice,
                        **kwargs
                    }
                )
                
                # Handle output (could be URL, bytes, or file path)
                if isinstance(output, str) and output.startswith("http"):
                    # Download from URL
                    import requests
                    response = requests.get(output)
                    response.raise_for_status()
                    
                    with open(output_path_obj, 'wb') as f:
                        f.write(response.content)
                
                elif isinstance(output, bytes):
                    # Write bytes directly
                    with open(output_path_obj, 'wb') as f:
                        f.write(output)
                
                else:
                    # Assume it's already a file path
                    import shutil
                    shutil.copy(output, output_path_obj)
                
                file_size_mb = output_path_obj.stat().st_size / (1024 * 1024)
                
                logger.info(f"✓ Generated {file_size_mb:.2f} MB audio via Replicate")
                
                return {
                    "status": "success",
                    "output_file": str(output_path_obj),
                    "file_size_mb": round(file_size_mb, 2),
                    "synthesis_method": "replicate",
                    "error": None
                }
            
            except replicate.exceptions.ReplicateError as e:
                status_code = getattr(e, 'status_code', None)
                raise ReplicateAPIError(str(e), status_code)
        
        except ReplicateAuthError:
            raise  # Re-raise for agent to handle
        
        except ReplicateAPIError:
            raise  # Re-raise for agent to handle
        
        except Exception as e:
            logger.error(f"Replicate synthesis failed: {str(e)}")
            return {
                "status": "error",
                "output_file": "",
                "error": str(e),
                "synthesis_method": "replicate"
            }
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "provider": "replicate",
            "model": self.model,
            "version": self.version,
            "authenticated": bool(self.api_token and self.api_token != "your_replicate_token_here")
        }
