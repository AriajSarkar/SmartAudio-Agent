# SAA Tests

Test suite for Smart Audio Agent v2.0

## Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_document_tools.py
│   ├── test_text_tools.py
│   └── test_voice_tools.py
├── integration/             # Integration tests
│   └── test_pipeline.py
└── test_data/               # Test fixtures
```

## Running Tests

```powershell
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/ -m integration

# With coverage
pytest --cov=saa --cov-report=html

# Verbose output
pytest -v

# Skip slow tests
pytest -m "not slow"
```

## Test Markers

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.gpu` - Requires GPU
- `@pytest.mark.network` - Requires network

## Fixtures

Key fixtures in `conftest.py`:
- `temp_dir` - Temporary directory for test files
- `sample_text` - Multi-paragraph text with dialogue
- `sample_pdf_path` - Generated PDF file
- `sample_txt_path` - TXT file with sample text
- `mock_reference_audio` - Mock WAV file
- `mock_env_vars` - Test environment variables
- `mock_settings` - Test configuration

## Writing Tests

```python
def test_my_tool(sample_text, temp_dir):
    """Test description"""
    result = my_tool(sample_text)
    
    assert result["status"] == "success"
    assert "expected" in result["data"]
```

## Coverage Goals

- Overall: 85%
- Tools: 90%
- Models: 80%
- Critical paths: 100%
