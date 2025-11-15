# Contributing to SAA

Thank you for considering contributing to SAA (Smart Audio Agent)! This document provides guidelines for contributing to the project.

---

## 🎯 Ways to Contribute

- **Bug Reports**: Found an issue? Open a GitHub issue with details
- **Feature Requests**: Have an idea? Discuss it in GitHub Discussions
- **Code Contributions**: Submit pull requests for bugs or features
- **Documentation**: Improve README, guides, or add examples
- **Testing**: Write tests or test on different platforms
- **Voice Samples**: Share reference audio for the community

---

## 🚀 Getting Started

### 1. Fork and Clone

```powershell
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/saa.git
cd saa
```

### 2. Set Up Development Environment

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install PyTorch with CUDA
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Install SAA in editable mode with dev dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

### 3. Create a Branch

```powershell
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## 📝 Code Style

### Python Standards

- **PEP 8**: Follow Python style guide
- **Type Hints**: Add type hints to all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions
- **Line Length**: Max 100 characters (not strict)

### Tools

```powershell
# Format code with Black
black saa/

# Lint with Ruff
ruff check saa/ --fix

# Type check with mypy
mypy saa/

# Run all checks
black saa/; ruff check saa/ --fix; mypy saa/
```

### Example Function

```python
def synthesize_audio(
    text: str,
    reference_audio: str,
    provider: str = "auto",
    temperature: float = 0.75
) -> Dict[str, Any]:
    """
    Synthesize speech from text using TTS provider.
    
    Args:
        text: Text to convert to speech
        reference_audio: Path to reference audio for voice cloning
        provider: TTS provider ("auto", "replicate", "local")
        temperature: Voice expressiveness (0.1-1.0, default 0.75)
    
    Returns:
        Dictionary with status, audio_path, and metadata
        
    Raises:
        TTSProviderError: If synthesis fails on all providers
        
    Example:
        >>> result = synthesize_audio(
        ...     text="Hello world",
        ...     reference_audio="reference_audio/narrator.wav"
        ... )
        >>> print(result["status"])
        success
    """
    # Implementation
    pass
```

---

## 🏗️ Architecture Patterns

### ADK Function Tools

Tools must be **pure functions** with comprehensive docstrings:

```python
def your_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description (shows in ADK agent context).
    
    Detailed explanation of what the tool does and when to use it.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
    
    Returns:
        Dictionary with standard keys: status, data, error
    """
    try:
        result = do_something(param1, param2)
        return {
            "status": "success",
            "data": result,
            "error": None
        }
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        return {
            "status": "error",
            "data": None,
            "error": str(e)
        }
```

**Important**: Docstrings guide ADK agents on tool usage. Be specific!

### Data Models

Use `dataclass` with serialization methods:

```python
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class YourModel:
    """Brief description of the model."""
    
    field1: str
    field2: int
    optional_field: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "YourModel":
        """Create instance from dictionary."""
        return cls(**data)
```

### Exception Handling

Use custom exceptions from `saa/exceptions.py`:

```python
from saa.exceptions import TTSProviderError

def risky_operation():
    try:
        # Your code
        pass
    except SomeError as e:
        raise TTSProviderError(
            message="Failed to synthesize audio",
            original_error=e,
            error_code="TTS_001",
            recoverable=True  # Can retry with different provider
        )
```

### Logging

Use module-level logger:

```python
import logging

logger = logging.getLogger(__name__)

def your_function():
    logger.debug("Detailed debug information")
    logger.info("Important user-facing information")
    logger.warning("Something unexpected but recoverable")
    logger.error("Operation failed", exc_info=True)
```

---

## 🧪 Testing

### Writing Tests

```python
# tests/unit/test_your_tool.py
import pytest
from unittest.mock import Mock, patch
from saa.tools.your_tool import your_function

def test_your_function_success():
    """Test successful execution."""
    result = your_function("valid_input")
    assert result["status"] == "success"
    assert "data" in result

def test_your_function_error():
    """Test error handling."""
    with pytest.raises(YourException):
        your_function("invalid_input")

@patch('saa.providers.replicate_provider.replicate')
def test_with_mocked_api(mock_replicate):
    """Test with mocked external API."""
    mock_replicate.run.return_value = "http://fake-audio.wav"
    result = your_function()
    assert result["status"] == "success"
```

### Running Tests

```powershell
# All tests
pytest

# Specific test file
pytest tests/unit/test_tools.py -v

# With coverage
pytest --cov=saa --cov-report=html

# Open coverage report
start htmlcov/index.html
```

### Test Coverage Goals

- **Target**: 85% overall coverage
- **Critical Paths**: 100% (TTS synthesis, audio merging)
- **Tools**: >90% (all function tools)
- **Models**: >80% (data validation)

---

## 📚 Documentation

### Docstring Style

Use Google-style docstrings:

```python
def function_name(param1, param2):
    """
    Brief one-line summary.
    
    Longer description explaining the function's purpose,
    behavior, and any important details.
    
    Args:
        param1 (str): Description of first parameter
        param2 (int): Description of second parameter
    
    Returns:
        dict: Description of return value with structure
    
    Raises:
        ValueError: When param1 is empty
        TTSError: When synthesis fails
    
    Example:
        >>> result = function_name("hello", 42)
        >>> print(result["data"])
        processed_output
    
    Note:
        Any important notes or warnings.
    """
    pass
```

### Adding to README

When adding features:
1. Update **Features** section with emoji bullet
2. Add to **Architecture** diagram if new agent/tool
3. Update **Quick Start** if affects usage
4. Add to **Troubleshooting** if known issues

### CHANGELOG Updates

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]

### Added
- New TTS provider: ElevenLabs integration (#42)
- Character detection: NER-based speaker identification

### Changed
- Improved GPU memory cleanup (90% → 85% threshold)

### Fixed
- PDF extraction failing on password-protected files (#38)
```

---

## 🔄 Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines (Black, Ruff)
- [ ] All tests pass (`pytest`)
- [ ] Added tests for new features
- [ ] Updated documentation (README, docstrings)
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts with main branch

### 2. PR Description Template

```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that breaks existing functionality)
- [ ] Documentation update

## How Has This Been Tested?
Describe tests you ran to verify changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### 3. Review Process

- Maintainers will review within 1-2 weeks
- Address review comments
- Squash commits before merge (if requested)
- Merge via squash or rebase (no merge commits)

---

## 🐛 Bug Reports

### Template

```markdown
**Describe the bug**
Clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Run command: `python -m saa generate input/test.pdf`
2. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment**
- OS: Windows 11
- Python version: 3.10.8
- SAA version: 2.0.0
- GPU: NVIDIA RTX 3050 4GB
- CUDA: 11.8

**Logs**
Paste relevant logs (use code blocks).

**Additional context**
Any other relevant information.
```

---

## 💡 Feature Requests

### Template

```markdown
**Is your feature related to a problem?**
Description of the problem.

**Describe the solution you'd like**
Clear description of desired functionality.

**Describe alternatives considered**
Other solutions you've considered.

**Use case**
How would this feature be used?

**Additional context**
Mockups, examples, or references.
```

---

## 🌟 Recognition

Contributors will be:
- Added to `CONTRIBUTORS.md`
- Mentioned in release notes
- Credited in README (for major contributions)

---

## 📧 Questions?

- **GitHub Discussions**: https://github.com/AriajSarkar/saa/discussions

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for making SAA better!** 🎙️
