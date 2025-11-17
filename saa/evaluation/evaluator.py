"""
Agent Evaluation Framework for SAA Pipeline
Provides tools for testing agent quality and performance
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from saa.utils import setup_logger

logger = setup_logger(
    name="evaluator",
    level=logging.INFO,
    log_file="logs/evaluation.log"
)


class AudiobookEvaluator:
    """
    Evaluates audiobook generation quality.
    
    Metrics:
    - Text extraction accuracy
    - Chunk segmentation quality
    - Voice assignment correctness
    - Audio synthesis success rate
    - End-to-end pipeline success
    
    Usage:
        evaluator = AudiobookEvaluator()
        results = evaluator.evaluate_pipeline(
            test_cases=["input/test1.txt", "input/test2.pdf"]
        )
        evaluator.save_results(results, "eval_results.json")
    """
    
    def __init__(self):
        """Initialize evaluator."""
        self.results: List[Dict[str, Any]] = []
    
    def evaluate_extraction(
        self,
        input_file: str,
        expected_chars: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate text extraction quality.
        
        Args:
            input_file: Path to input document
            expected_chars: Expected character count (if known)
        
        Returns:
            Evaluation result with metrics
        """
        from saa.tools.document_tools import extract_text_from_pdf, extract_text_from_txt
        
        file_path = Path(input_file)
        
        try:
            if file_path.suffix.lower() == '.pdf':
                result = extract_text_from_pdf(str(file_path))
            else:
                result = extract_text_from_txt(str(file_path))
            
            success = result.get("status") == "success"
            actual_chars = result.get("total_chars", 0)
            
            metrics = {
                "test": "extraction",
                "input_file": str(input_file),
                "success": success,
                "actual_chars": actual_chars,
                "expected_chars": expected_chars
            }
            
            if expected_chars:
                accuracy = min(actual_chars / expected_chars, 1.0) if expected_chars > 0 else 0.0
                metrics["accuracy"] = accuracy
            
            logger.info(f"Extraction eval: {metrics}")
            return metrics
        
        except Exception as e:
            logger.error(f"Extraction eval failed: {e}")
            return {
                "test": "extraction",
                "input_file": str(input_file),
                "success": False,
                "error": str(e)
            }
    
    def evaluate_segmentation(
        self,
        text: str,
        expected_segments: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate text segmentation quality.
        
        Args:
            text: Input text to segment
            expected_segments: Expected number of segments
        
        Returns:
            Evaluation result with metrics
        """
        from saa.tools.text_tools import segment_text
        
        try:
            result = segment_text(text)
            success = result.get("status") == "success"
            actual_segments = result.get("total_segments", 0)
            
            metrics = {
                "test": "segmentation",
                "success": success,
                "actual_segments": actual_segments,
                "expected_segments": expected_segments
            }
            
            if expected_segments:
                accuracy = 1.0 - abs(actual_segments - expected_segments) / expected_segments
                metrics["accuracy"] = max(accuracy, 0.0)
            
            logger.info(f"Segmentation eval: {metrics}")
            return metrics
        
        except Exception as e:
            logger.error(f"Segmentation eval failed: {e}")
            return {
                "test": "segmentation",
                "success": False,
                "error": str(e)
            }
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """
        Save evaluation results to JSON file.
        
        Args:
            results: List of evaluation result dictionaries
            output_file: Path to output JSON file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved evaluation results to {output_path}")


def create_evaluator() -> AudiobookEvaluator:
    """
    Create evaluator instance.
    
    Returns:
        AudiobookEvaluator ready to use
    """
    return AudiobookEvaluator()


__all__ = ["AudiobookEvaluator", "create_evaluator"]
