# Backend Implementation Guide: Audio VU & Day/Night Nodes

**Status**: Frontend complete, backend integration needed  
**Priority**: Medium  
**Complexity**: Moderate

---

## Overview

Two new workflow nodes have been created in the frontend but require backend processing to work with live data:

1. **Audio VU/Frequency Meter** - Real-time audio level analysis
2. **Day/Night/IR Detector** - Image brightness and IR mode detection

Currently both nodes show **demo data** for visualization. This guide explains what backend code is needed to make them work with live camera/audio feeds.

---

## 1. Audio VU/Frequency Meter Backend

### Required Processing

The backend needs to:
1. Extract audio from video streams (already partially implemented)
2. Calculate audio levels (dB, RMS, peak)
3. Perform FFT for frequency spectrum
4. Stream results via WebSocket to frontend

### Implementation Location

**File**: `backend/stream/audio_buffer.py` or create `backend/stream/audio_analyzer.py`

### Code Implementation

```python
import numpy as np
import librosa
from typing import Dict, List, Optional

class AudioAnalyzer:
    """Analyze audio for VU meter and frequency spectrum"""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.fft_size = 2048
        self.hop_length = 512
        
    def calculate_levels(self, audio_chunk: np.ndarray) -> Dict:
        """
        Calculate audio levels from audio chunk
        
        Args:
            audio_chunk: Audio data as numpy array (mono or stereo)
            
        Returns:
            Dict with level_db, rms, peak, spectrum
        """
        # Convert to mono if stereo
        if len(audio_chunk.shape) > 1:
            audio_mono = np.mean(audio_chunk, axis=1)
        else:
            audio_mono = audio_chunk
            
        # Calculate RMS (Root Mean Square)
        rms = np.sqrt(np.mean(audio_mono ** 2))
        
        # Calculate peak
        peak = np.max(np.abs(audio_mono))
        
        # Convert RMS to dB (relative to peak = 0 dB)
        # Prevent log(0) with small epsilon
        level_db = 20 * np.log10(rms + 1e-10)
        # Normalize to 0-100 range (assuming -60dB to 0dB range)
        level_db_normalized = max(0, min(100, (level_db + 60) * (100/60)))
        
        # Calculate frequency spectrum using FFT
        spectrum = self.calculate_spectrum(audio_mono, num_bands=32)
        
        return {
            'level_db': float(level_db_normalized),
            'rms': float(rms),
            'peak': float(peak),
            'spectrum': spectrum,
            'timestamp': time.time()
        }
    
    def calculate_spectrum(self, audio: np.ndarray, num_bands: int = 32) -> List[float]:
        """
        Calculate frequency spectrum with configurable number of bands
        
        Args:
            audio: Mono audio data
            num_bands: Number of frequency bands (4-32)
            
        Returns:
            List of dB levels for each frequency band (0-100)
        """
        # Pad audio if too short
        if len(audio) < self.fft_size:
            audio = np.pad(audio, (0, self.fft_size - len(audio)))
        
        # Perform FFT
        fft = np.fft.rfft(audio[:self.fft_size])
        magnitude = np.abs(fft)
        
        # Convert to dB
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        
        # Group into frequency bands
        band_size = len(magnitude_db) // num_bands
        bands = []
        
        for i in range(num_bands):
            start_idx = i * band_size
            end_idx = start_idx + band_size
            
            # Average magnitude for this band
            band_avg = np.mean(magnitude_db[start_idx:end_idx])
            
            # Normalize to 0-100 range
            band_normalized = max(0, min(100, (band_avg + 60) * (100/60)))
            bands.append(float(band_normalized))
        
        return bands
    
    def check_threshold(
        self, 
        level_db: float, 
        threshold: float,
        hysteresis: float = 5.0,
        current_state: bool = False
    ) -> bool:
        """
        Check if level exceeds threshold with hysteresis
        
        Args:
            level_db: Current audio level in dB (0-100)
            threshold: Threshold level (0-100)
            hysteresis: Hysteresis amount to prevent rapid toggling
            current_state: Current trigger state
            
        Returns:
            New trigger state (True if triggered)
        """
        if current_state:
            # Currently triggered, check if we should turn off
            return level_db >= (threshold - hysteresis)
        else:
            # Not triggered, check if we should turn on
            return level_db >= threshold
```

### Integration with Visual Executor

**File**: `backend/workflows/visual_executor.py`

```python
from stream.audio_analyzer import AudioAnalyzer

class VisualWorkflowExecutor:
    def __init__(self):
        # ... existing code ...
        self.audio_analyzer = AudioAnalyzer()
        self.audio_vu_states = {}  # Track threshold states per node
        
    async def execute_node(self, node: dict, input_data: dict) -> dict:
        """Execute a single workflow node"""
        
        if node['type'] == 'audioVU':
            return await self._execute_audio_vu(node, input_data)
        
        # ... existing node handlers ...
    
    async def _execute_audio_vu(self, node: dict, input_data: dict) -> dict:
        """
        Execute Audio VU/Frequency Meter node
        
        Input: Audio chunk from audio extractor or video with audio
        Output: Audio levels, spectrum, and threshold trigger status
        """
        node_id = node['id']
        config = node.get('data', {})
        
        # Get audio chunk from input
        if 'audio' in input_data:
            audio_chunk = input_data['audio']
        elif 'video' in input_data and 'audio_stream' in input_data:
            # Extract audio from video (if not already extracted)
            audio_chunk = await self._extract_audio_chunk(input_data)
        else:
            return {'error': 'No audio input'}
        
        # Calculate audio levels
        levels = self.audio_analyzer.calculate_levels(audio_chunk)
        
        # Check threshold if enabled
        threshold_triggered = False
        if config.get('enableThreshold', False):
            threshold = config.get('thresholdLevel', 75)
            hysteresis = config.get('hysteresis', 5)
            current_state = self.audio_vu_states.get(node_id, False)
            
            threshold_triggered = self.audio_analyzer.check_threshold(
                levels['level_db'],
                threshold,
                hysteresis,
                current_state
            )
            
            self.audio_vu_states[node_id] = threshold_triggered
        
        # Prepare output data
        output = {
            'audio': audio_chunk,  # Pass through audio
            'vu_data': levels,
            'threshold_triggered': threshold_triggered,
            'display_mode': config.get('displayMode', 'vu_meter'),
            'frequency_bands': config.get('frequencyBands', 8),
        }
        
        # Send to WebSocket for live display
        await self._send_node_update(node_id, {
            'type': 'audioVU',
            'data': {
                'level_db': levels['level_db'],
                'spectrum': levels['spectrum'][:config.get('frequencyBands', 8)],
                'triggered': threshold_triggered
            }
        })
        
        return output
```

### WebSocket Updates

**File**: `backend/api/websocket.py`

Add handler to stream audio VU data to frontend:

```python
async def send_audio_vu_update(node_id: str, data: dict):
    """Send audio VU data to subscribed clients"""
    message = {
        'type': 'node_update',
        'node_id': node_id,
        'node_type': 'audioVU',
        'data': data,
        'timestamp': time.time()
    }
    
    # Broadcast to all workflow builder clients
    await broadcast_to_workflow_builder(message)
```

### Frontend WebSocket Handler

The frontend node needs to listen for WebSocket updates:

```javascript
// In AudioVUNode.jsx, add WebSocket connection
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws')
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    if (message.type === 'node_update' && message.node_id === id) {
      // Update with live data
      setCurrentLevel(message.data.level_db)
      setCurrentSpectrum(message.data.spectrum)
      setIsTriggered(message.data.triggered)
      setIsLiveConnected(true)
      setConnectionStatus('live')
    }
  }
  
  return () => ws.close()
}, [id])
```

---

## 2. Day/Night/IR Detector Backend

### Required Processing

The backend needs to:
1. Analyze video frames for brightness
2. Detect IR mode via color saturation analysis
3. Determine day/dusk/night state
4. Stream results via WebSocket

### Implementation Location

**File**: Create `backend/stream/lighting_analyzer.py`

### Code Implementation

```python
import cv2
import numpy as np
from typing import Dict, Literal
from enum import Enum

class LightingState(str, Enum):
    DAY = 'day'
    DUSK = 'dusk'
    NIGHT = 'night'

class LightingAnalyzer:
    """Analyze video frames for lighting conditions and IR mode"""
    
    def __init__(self):
        self.history_size = 5
        self.brightness_history = []
        self.saturation_history = []
    
    def analyze_frame(
        self,
        frame: np.ndarray,
        brightness_threshold: float = 0.3,
        ir_threshold: float = 0.7,
        sensitivity: float = 0.5
    ) -> Dict:
        """
        Analyze frame for lighting conditions
        
        Args:
            frame: BGR image from camera
            brightness_threshold: Threshold for day/night (0.0-1.0)
            ir_threshold: Threshold for IR detection (0.0-1.0)
            sensitivity: Overall sensitivity adjustment
            
        Returns:
            Dict with state, brightness, is_ir, confidence
        """
        # Convert to HSV for better analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Calculate average brightness (V channel)
        brightness = np.mean(hsv[:, :, 2]) / 255.0
        
        # Calculate color saturation (S channel)
        saturation = np.mean(hsv[:, :, 1]) / 255.0
        
        # Add to history for smoothing
        self.brightness_history.append(brightness)
        self.saturation_history.append(saturation)
        
        if len(self.brightness_history) > self.history_size:
            self.brightness_history.pop(0)
            self.saturation_history.pop(0)
        
        # Use smoothed values
        avg_brightness = np.mean(self.brightness_history)
        avg_saturation = np.mean(self.saturation_history)
        
        # Detect IR mode (low saturation = monochrome image)
        # Adjust threshold with sensitivity
        adjusted_ir_threshold = ir_threshold - (sensitivity - 0.5) * 0.2
        is_ir = avg_saturation < (1.0 - adjusted_ir_threshold)
        
        # Determine lighting state
        adjusted_brightness_threshold = brightness_threshold + (sensitivity - 0.5) * 0.2
        
        if avg_brightness >= (adjusted_brightness_threshold + 0.2):
            state = LightingState.DAY
            confidence = min(1.0, (avg_brightness - adjusted_brightness_threshold) / 0.5)
        elif avg_brightness >= adjusted_brightness_threshold:
            state = LightingState.DUSK
            confidence = 0.7
        else:
            state = LightingState.NIGHT
            confidence = min(1.0, (adjusted_brightness_threshold - avg_brightness) / 0.3)
        
        return {
            'state': state.value,
            'brightness': float(avg_brightness),
            'saturation': float(avg_saturation),
            'is_ir': bool(is_ir),
            'confidence': float(confidence),
            'raw_brightness': float(brightness),
            'raw_saturation': float(saturation)
        }
    
    def should_trigger_action(
        self,
        current_state: LightingState,
        previous_state: LightingState,
        enable_actions: bool
    ) -> bool:
        """Check if state change should trigger actions"""
        return enable_actions and current_state != previous_state
```

### Integration with Visual Executor

```python
from stream.lighting_analyzer import LightingAnalyzer, LightingState

class VisualWorkflowExecutor:
    def __init__(self):
        # ... existing code ...
        self.lighting_analyzer = LightingAnalyzer()
        self.lighting_states = {}  # Track previous states per node
        
    async def _execute_day_night_detector(self, node: dict, input_data: dict) -> dict:
        """
        Execute Day/Night/IR Detector node
        
        Input: Video frame
        Output: Frame with lighting metadata, separate outputs for IR/night
        """
        node_id = node['id']
        config = node.get('data', {})
        
        if 'frame' not in input_data:
            return {'error': 'No video frame input'}
        
        frame = input_data['frame']
        
        # Analyze frame
        analysis = self.lighting_analyzer.analyze_frame(
            frame,
            brightness_threshold=config.get('brightnessThreshold', 0.3),
            ir_threshold=config.get('irThreshold', 0.7),
            sensitivity=config.get('sensitivity', 0.5)
        )
        
        # Check if we should trigger actions
        previous_state = self.lighting_states.get(node_id)
        current_state = LightingState(analysis['state'])
        
        trigger_action = self.lighting_analyzer.should_trigger_action(
            current_state,
            previous_state,
            config.get('enableActions', True)
        )
        
        self.lighting_states[node_id] = current_state
        
        # Prepare outputs
        output = {
            'frame': frame,
            'lighting': analysis,
            'state_changed': trigger_action,
        }
        
        # Separate outputs
        output_ir = None
        output_night = None
        
        if analysis['is_ir']:
            output_ir = output.copy()
        
        if analysis['state'] in ['night', 'dusk']:
            output_night = output.copy()
        
        # Send to WebSocket for live display
        await self._send_node_update(node_id, {
            'type': 'dayNightDetector',
            'data': analysis
        })
        
        return {
            'main': output,
            'ir': output_ir,
            'night': output_night
        }
```

---

## 3. Testing & Validation

### Test Audio VU Node

```python
# tests/test_audio_vu.py
import pytest
import numpy as np
from stream.audio_analyzer import AudioAnalyzer

def test_audio_level_calculation():
    analyzer = AudioAnalyzer()
    
    # Generate test audio (440 Hz sine wave)
    duration = 1.0
    sample_rate = 48000
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t) * 0.5
    
    levels = analyzer.calculate_levels(audio)
    
    assert 'level_db' in levels
    assert 'spectrum' in levels
    assert 0 <= levels['level_db'] <= 100
    assert len(levels['spectrum']) == 32

def test_threshold_hysteresis():
    analyzer = AudioAnalyzer()
    
    # Test threshold crossing
    assert analyzer.check_threshold(80, 75, 5, False) == True
    # Test hysteresis (should stay on)
    assert analyzer.check_threshold(72, 75, 5, True) == True
    # Test turn off
    assert analyzer.check_threshold(65, 75, 5, True) == False
```

### Test Day/Night Detector

```python
# tests/test_lighting_analyzer.py
import pytest
import numpy as np
from stream.lighting_analyzer import LightingAnalyzer, LightingState

def test_brightness_detection():
    analyzer = LightingAnalyzer()
    
    # Create bright frame (day)
    bright_frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
    result = analyzer.analyze_frame(bright_frame)
    assert result['state'] == 'day'
    assert result['brightness'] > 0.7
    
    # Create dark frame (night)
    dark_frame = np.ones((480, 640, 3), dtype=np.uint8) * 30
    result = analyzer.analyze_frame(dark_frame)
    assert result['state'] == 'night'
    assert result['brightness'] < 0.3

def test_ir_detection():
    analyzer = LightingAnalyzer()
    
    # Create grayscale frame (simulating IR)
    gray_value = 128
    ir_frame = np.ones((480, 640, 3), dtype=np.uint8) * gray_value
    result = analyzer.analyze_frame(ir_frame)
    assert result['is_ir'] == True
    assert result['saturation'] < 0.3
```

---

## 4. Performance Considerations

### Audio VU Processing
- **Target Latency**: < 100ms
- **Update Rate**: 10-30 FPS
- **CPU Impact**: ~2-5% per stream
- **Optimization**: Use ring buffers, process in chunks

### Day/Night Detection  
- **Target Latency**: < 50ms per frame
- **Update Rate**: 1-5 FPS (configurable)
- **CPU Impact**: ~1-2% per stream
- **Optimization**: Downsample frames, cache results

---

## 5. Configuration

### Add to Config Schema

```python
# backend/workflows/schema.py

class AudioVUNodeConfig(BaseModel):
    displayMode: str = 'vu_meter'
    sensitivity: float = 0.5
    frequencyBands: int = 8
    enableThreshold: bool = False
    thresholdLevel: float = 75
    thresholdMode: str = 'continuous'
    hysteresis: float = 5

class DayNightDetectorConfig(BaseModel):
    detectionMode: str = 'all'
    brightnessThreshold: float = 0.3
    irThreshold: float = 0.7
    checkInterval: int = 5
    sensitivity: float = 0.5
    enableActions: bool = True
```

---

## 6. Next Steps

**Priority Order:**

1. ✅ Frontend nodes created (DONE)
2. ⏳ Create `AudioAnalyzer` class
3. ⏳ Create `LightingAnalyzer` class
4. ⏳ Integrate with `VisualWorkflowExecutor`
5. ⏳ Add WebSocket streaming
6. ⏳ Connect frontend to WebSocket
7. ⏳ Write tests
8. ⏳ Performance optimization

**Estimated Effort**: 4-6 hours of development

---

## 7. Dependencies

Already installed (from requirements.txt):
- ✅ `numpy`
- ✅ `opencv-python`
- ✅ `librosa`

No additional packages needed!

---

For questions or implementation help, see:
- [Audio Processing Guide](docs/AUDIO_PROCESSING_GUIDE.md)
- [Workflow Builder](docs/WORKFLOW_BUILDER.md)
- [Architecture](docs/ARCHITECTURE.md)


