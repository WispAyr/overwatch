# Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.10+
- FFmpeg with RTSP support
- CUDA Toolkit (optional, for GPU acceleration)
- Node.js 18+ (for frontend tooling)

### Backend Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

3. Run tests:
```bash
pytest tests/
```

4. Start development server:
```bash
python backend/main.py --dev --reload
```

### Frontend Setup

1. Install Tailwind CSS CLI:
```bash
npm install -D tailwindcss
```

2. Build CSS:
```bash
npm run build:css
```

3. Start local server:
```bash
python -m http.server 7001 --directory frontend
```

## Project Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── server.py          # FastAPI application
│   ├── routes/            # API route handlers
│   └── websocket.py       # WebSocket handler
├── core/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connections
│   └── logging.py         # Logging setup
├── stream/
│   ├── __init__.py
│   ├── manager.py         # Stream manager
│   ├── rtsp.py            # RTSP client
│   └── processor.py       # Frame processor
├── workflows/
│   ├── __init__.py
│   ├── engine.py          # Workflow engine
│   ├── loader.py          # Workflow loader
│   └── executor.py        # Workflow executor
├── models/
│   ├── __init__.py
│   ├── base.py            # Base model plugin
│   ├── ultralytics.py     # YOLO integration
│   └── custom.py          # Custom model loader
├── events/
│   ├── __init__.py
│   ├── manager.py         # Event manager
│   ├── storage.py         # Event storage
│   └── alerts.py          # Alert handlers
└── main.py                # Application entry point
```

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints
- Docstrings for all public functions
- Maximum line length: 100 characters

Example:
```python
from typing import List, Optional
import numpy as np

def process_frame(
    frame: np.ndarray,
    confidence: float = 0.7,
    classes: Optional[List[int]] = None
) -> List[Detection]:
    """
    Process a video frame through detection model.
    
    Args:
        frame: Input frame as numpy array
        confidence: Minimum confidence threshold
        classes: Optional list of class IDs to detect
        
    Returns:
        List of Detection objects
    """
    pass
```

### JavaScript
- Use ES6+ features
- Async/await for promises
- JSDoc comments for functions
- Use const/let, never var

Example:
```javascript
/**
 * Fetch camera status from API
 * @param {string} cameraId - Camera identifier
 * @returns {Promise<Object>} Camera status object
 */
async function getCameraStatus(cameraId) {
    const response = await fetch(`/api/cameras/${cameraId}`);
    return await response.json();
}
```

## Adding a New Model Plugin

1. Create model file in `backend/models/`:

```python
from typing import List
import numpy as np
from .base import ModelPlugin, Detection

class CustomModel(ModelPlugin):
    """Custom AI model integration."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.model = None
        
    def initialize(self) -> None:
        """Load and initialize the model."""
        # Load your model here
        pass
        
    def process_frame(self, frame: np.ndarray) -> List[Detection]:
        """Process a frame and return detections."""
        # Run inference
        detections = []
        return detections
        
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.model:
            del self.model
```

2. Register in `backend/models/__init__.py`:
```python
from .custom import CustomModel

MODEL_REGISTRY = {
    'custom-model': CustomModel,
}
```

3. Use in workflow:
```yaml
workflow:
  model: custom-model
  config:
    param1: value1
```

## Adding a New Action Type

1. Create action handler in `backend/events/actions/`:

```python
from typing import Dict, Any
from .base import ActionHandler

class CustomAction(ActionHandler):
    """Custom action handler."""
    
    def __init__(self, config: dict):
        self.config = config
        
    async def execute(self, event: Dict[str, Any]) -> None:
        """Execute the action."""
        # Implement your action logic
        pass
```

2. Register in `backend/events/actions/__init__.py`:
```python
ACTION_REGISTRY = {
    'custom_action': CustomAction,
}
```

3. Use in workflow:
```yaml
actions:
  - type: custom_action
    param1: value1
```

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Test Coverage
```bash
pytest --cov=backend --cov-report=html
```

### Testing Workflows
```bash
python backend/tools/test_workflow.py \
    --workflow people_detection \
    --video test_videos/sample.mp4 \
    --output results/
```

## Debugging

### Enable Debug Logging
```bash
export OVERWATCH_LOG_LEVEL=DEBUG
python backend/main.py
```

### Debug Specific Component
```python
import logging
logger = logging.getLogger('overwatch.stream')
logger.setLevel(logging.DEBUG)
```

### Profile Performance
```bash
python -m cProfile -o profile.stats backend/main.py
python -m pstats profile.stats
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Building for Production

### Backend
```bash
# Build Docker image
docker build -t overwatch-backend .

# Run container
docker run -p 8000:8000 overwatch-backend
```

### Frontend
```bash
# Build optimized CSS
npm run build:css -- --minify

# Bundle JavaScript
npm run build:js
```

## Performance Optimization

### GPU Acceleration
Ensure CUDA is available:
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
```

### Batch Processing
Enable frame batching in workflow:
```yaml
processing:
  batch_size: 4  # Process 4 frames at once
```

### Stream Optimization
Reduce resolution for processing:
```yaml
stream:
  processing_resolution: [640, 480]  # Process at lower res
  display_resolution: [1920, 1080]   # Display at full res
```

## Troubleshooting

### Common Issues

**RTSP Connection Failed**
- Check camera IP and port
- Verify credentials
- Test with VLC or FFmpeg directly

**High CPU Usage**
- Reduce processing FPS
- Use smaller model (YOLOv8n)
- Enable frame skipping

**Out of Memory**
- Reduce batch size
- Use CPU instead of GPU for some models
- Limit concurrent streams

**WebSocket Disconnects**
- Check firewall settings
- Increase timeout in config
- Verify network stability

