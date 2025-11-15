"""Test configuration and shared fixtures for SAA tests"""
import pytest
import os
from pathlib import Path
from typing import Generator
import tempfile
import shutil

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files.
    
    Yields:
        Path to temporary directory (cleaned up after test)
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_text() -> str:
    """
    Sample text for testing text processing.
    
    Returns:
        Multi-paragraph sample text with dialogue
    """
    return """
    The old wizard walked into the tavern. "Good evening," said Gandalf cheerfully.
    
    "We've been expecting you," replied the innkeeper with a knowing smile.
    
    The narrator observed the scene with interest. It was a cold winter night,
    and the fire crackled warmly in the hearth.
    
    "Tell me," she asked, "what brings you to our village?"
    """


@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """
    Create a sample PDF file for testing.
    
    Args:
        temp_dir: Temporary directory fixture
    
    Returns:
        Path to created PDF file
    """
    pdf_path = temp_dir / "test_document.pdf"
    
    # Create a simple PDF using reportlab if available
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "This is a test PDF document.")
        c.drawString(100, 730, "It contains multiple lines of text.")
        c.drawString(100, 710, "Used for testing PDF extraction.")
        c.save()
        
    except ImportError:
        # If reportlab not available, create a placeholder
        pdf_path.write_text("Placeholder PDF content")
    
    return pdf_path


@pytest.fixture
def sample_txt_path(temp_dir: Path, sample_text: str) -> Path:
    """
    Create a sample TXT file for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        sample_text: Sample text fixture
    
    Returns:
        Path to created TXT file
    """
    txt_path = temp_dir / "test_document.txt"
    txt_path.write_text(sample_text, encoding="utf-8")
    return txt_path


@pytest.fixture
def mock_reference_audio(temp_dir: Path) -> Path:
    """
    Create a mock reference audio file for testing.
    
    Args:
        temp_dir: Temporary directory fixture
    
    Returns:
        Path to mock WAV file
    """
    audio_path = temp_dir / "reference.wav"
    
    # Create a minimal WAV file header (placeholder)
    # In real tests, use actual audio generation
    audio_path.write_bytes(b"RIFF" + b"\x00" * 40 + b"WAVE")
    
    return audio_path


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """
    Mock environment variables for testing.
    
    Yields:
        None (environment variables set and cleaned up)
    """
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ["GOOGLE_API_KEY"] = "test_google_api_key_12345"
    os.environ["REPLICATE_API_TOKEN"] = "test_replicate_token_67890"
    os.environ["TTS_PROVIDER"] = "local"
    os.environ["TTS_USE_GPU"] = "false"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_settings(mock_env_vars):
    """
    Create mock settings for testing.
    
    Args:
        mock_env_vars: Environment variables fixture
    
    Returns:
        Settings instance with test configuration
    """
    from saa.config import get_settings
    return get_settings()


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests requiring GPU"
    )
    config.addinivalue_line(
        "markers", "network: marks tests requiring network access"
    )
