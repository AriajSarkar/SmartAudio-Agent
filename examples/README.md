# SAA Examples

This directory contains example scripts demonstrating SAA features and best practices.

## Available Examples

### 1. `advanced_features.py`
**Demonstrates**: Observability, Sessions, and Evaluation

**Features shown:**
- LoggingPlugin for comprehensive monitoring
- Session management for multi-turn conversations
- Agent evaluation for quality testing

**Run:**
```powershell
python examples/advanced_features.py
```

**What you'll see:**
- Setup examples for each feature
- Sample evaluation results
- Links to detailed documentation

**Note**: This is a demonstration script. For actual audiobook generation, use:
```powershell
python -m saa generate input/sample.txt
```

## Best Practices Demonstrated

### Observability (ADK Requirement)
```python
from saa.observability import create_observability_plugin

plugin = create_observability_plugin()
runner = Runner(agent=pipeline, plugins=[plugin])
```

**Benefits:**
- Automatic logging of all agent actions
- LLM token usage tracking
- Tool execution monitoring
- Error tracking

### Sessions (ADK Requirement)
```python
from saa.sessions import create_session_service

session_service = create_session_service(persistent=True)
runner = Runner(agent=pipeline, session_service=session_service)
```

**Benefits:**
- Multi-turn conversations with context
- State management across queries
- Persistent conversation history

### Evaluation (ADK Requirement)
```python
from saa.evaluation import create_evaluator

evaluator = create_evaluator()
results = evaluator.evaluate_extraction(input_file, expected_chars)
```

**Benefits:**
- Quality metrics tracking
- Regression testing
- Performance benchmarking

## Google ADK Capstone Compliance

These examples demonstrate **3+ required features** for the Kaggle capstone:

1. ✅ **Multi-Agent System** - 5-stage AgentTool coordinator
2. ✅ **Custom Tools** - 17 function tools across 5 domains
3. ✅ **Observability** - LoggingPlugin integration
4. ✅ **Sessions & Memory** - InMemorySessionService / DatabaseSessionService
5. ✅ **Agent Evaluation** - Quality testing framework

## Next Steps

1. **Run examples**: `python examples/advanced_features.py`
2. **Try full pipeline**: `python -m saa generate input/sample.txt`
3. **Deploy to production**: See `docs/DEPLOYMENT.md`
4. **Submit to Kaggle**: See project README for capstone details
