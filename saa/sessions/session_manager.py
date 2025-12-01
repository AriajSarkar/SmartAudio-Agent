"""
Session Management for SAA Pipeline
Implements Google ADK session services for multi-turn conversations
"""
import logging
from pathlib import Path
from typing import Optional

from google.adk.sessions import InMemorySessionService, DatabaseSessionService

from saa.utils import setup_logger
from saa.config import get_settings

logger = setup_logger(
    name="sessions",
    level=logging.INFO,
    log_file="logs/sessions.log"
)

settings = get_settings()


def create_session_service(
    persistent: bool = False,
    db_path: Optional[str] = None
) -> InMemorySessionService | DatabaseSessionService:
    """
    Create session service for conversation history.
    
    Sessions enable:
    - Multi-turn conversations with context retention
    - State management across multiple queries
    - Conversation history tracking
    
    Args:
        persistent: If True, uses DatabaseSessionService (survives restarts)
                   If False, uses InMemorySessionService (temporary)
        db_path: Path to SQLite database (only for persistent=True)
    
    Returns:
        Session service ready to use with ADK runner
    
    Usage:
        # Temporary sessions (development)
        session_service = create_session_service()
        
        # Persistent sessions (production)
        session_service = create_session_service(
            persistent=True,
            db_path="./sessions.db"
        )
        
        runner = Runner(
            agent=agent,
            app_name="saa",
            session_service=session_service
        )
    """
    if persistent:
        db_url = db_path or settings.session_db_path or "sqlite:///./sessions.db"
        if not db_url.startswith("sqlite://"):
            db_url = f"sqlite:///{db_url}"
        
        logger.info(f"Creating persistent session service: {db_url}")
        
        # Ensure directory exists for SQLite
        if db_url.startswith("sqlite:///"):
            path_str = db_url.replace("sqlite:///", "")
            if path_str != ":memory:":
                db_path_obj = Path(path_str)
                db_path_obj.parent.mkdir(parents=True, exist_ok=True)
                
        return DatabaseSessionService(db_url=db_url)
    else:
        logger.info("Creating in-memory session service (temporary)")
        return InMemorySessionService()


__all__ = ["create_session_service"]
