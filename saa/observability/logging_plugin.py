"""
Observability Plugin for SAA Pipeline
Implements Google ADK LoggingPlugin for comprehensive agent monitoring
"""
import logging
from typing import Any, Dict, Optional
from google.adk.plugins.logging_plugin import LoggingPlugin as ADKLoggingPlugin

from saa.utils import setup_logger

logger = setup_logger(
    name="observability",
    level=logging.INFO,
    log_file="logs/observability.log"
)


class SAALoggingPlugin(ADKLoggingPlugin):
    """
    Enhanced LoggingPlugin with SAA-specific metrics.
    
    Automatically captures:
    - All agent invocations
    - LLM requests and responses (with token counts)
    - Tool executions
    - Errors and exceptions
    
    Usage:
        from saa.observability.logging_plugin import SAALoggingPlugin
        
        runner = InMemoryRunner(
            agent=agent,
            plugins=[SAALoggingPlugin()]
        )
    """
    
    def __init__(self):
        """Initialize plugin with SAA configuration."""
        super().__init__()
        logger.info("SAALoggingPlugin initialized - observability enabled")


# Convenience function for quick setup
def create_observability_plugin() -> SAALoggingPlugin:
    """
    Create pre-configured observability plugin.
    
    Returns:
        SAALoggingPlugin ready to attach to runner
    """
    return SAALoggingPlugin()
