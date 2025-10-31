# Audio Processing Guide - Whisper & Sound Detection

## 🎤 Overview

Overwatch now supports **audio processing** alongside video detection! Extract audio from RTSP streams and process with AI for:
- 🎙️ **Speech Transcription** (Whisper)
- 🔊 **Sound Classification** (Gunshots, alarms, glass breaking, etc.)
- 🚨 **Security Alerts** (Keyword detection in speech)
- 📝 **Meeting Transcription**
- 🏭 **Industrial Monitoring** (Machine sounds, anomalies)

---

## 🎵 Audio Nodes

### 1. **Audio Extractor Node**
Extracts audio stream from video sources (RTSP, cameras, YouTube).

**Configuration:**
- **Sample Rate**: 8kHz - 48kHz (16kHz recommended for speech)
- **Channels**: Mono (1) or Stereo (2)
- **Format**: WAV, MP3, FLAC, PCM
- **Buffer Duration**: 1-60 seconds (how often to process)

**Use Cases:**
- Extract audio for Whisper transcription
- Feed to sound classifiers
- Audio-only monitoring
- Acoustic analysis

### 2. **Audio AI Node**
Process audio with AI models for transcription or sound classification.

**Two Modes:**

#### A. **Transcription (Whisper)**
Convert speech to text in 99 languages.

**Models:**
- **Whisper Tiny** - Fastest (39M params, real-time capable)
- **Whisper Base** - Balanced (74M params, general use)
- **Whisper Small** - High quality (244M params, professional)
- **Whisper Medium** - Very high quality (769M params)
- **Whisper Large** - Best quality (1550M params, forensics)

**Features:**
- Auto language detection
- 99+ language support
- Keyword trigger alerts
- Timestamp generation
- Speaker diarization (future)

#### B. **Sound Classification**
Detect and classify environmental sounds.

**Models:**
- **YAMNet** - Fast (521 sound classes)
- **AST** - Transformer-based (527 classes)
- **PANNs CNN14** - Neural network (527 classes)

**Detectable Sounds:**
- 🔫 Gunshots
- 💥 Explosions
- 🚨 Alarms (fire, burglar)
- 🔨 Glass breaking
- 😱 Screaming
- 🐕 Dog barking
- 🚗 Vehicle engines
- 🔊 Loud noises
- 📢 Speech/conversation
- 🎵 Music
- And 500+ more!

---

## 🔧 Workflow Examples

### Example 1: Speech Transcription with Keywords

**Scenario**: Transcribe audio and alert on security keywords

```
Camera (RTSP) → Audio Extractor → Whisper (Base) → Action (Alert)
                                        ↓
                                   Debug Console

Settings:
- Sample Rate: 16000 Hz (optimal for speech)
- Language: Auto Detect
- Keywords: ["help", "emergency", "gun", "fire"]
- Buffer: 5 seconds
```

**Output:**
```json
{
  "text": "Help! Someone call security!",
  "language": "en",
  "confidence": 0.95,
  "keywords_detected": ["help", "security"],
  "timestamp": "2025-10-30T23:15:42Z"
}
```

### Example 2: Gunshot Detection

**Scenario**: Detect gunshots and glass breaking for security

```
Camera (Parking) → Audio Extractor → YAMNet Classifier → Action (Emergency Alert)
                                           ↓
                                      Debug Console

Settings:
- Sample Rate: 44100 Hz (high quality)
- Confidence: 0.85 (reduce false positives)
- Target Sounds: Gunshots, Glass breaking, Explosions
- Buffer: 2 seconds
```

**Output:**
```json
{
  "sound": "gunshot",
  "confidence": 0.92,
  "timestamp": "2025-10-30T23:15:42Z",
  "location": "Parking Lot Camera 1"
}
```

### Example 3: Multi-Modal Detection

**Scenario**: Detect person AND listen for keywords

```
              ┌→ YOLOv8 (Person Detection) ─┐
Camera → Split                               ├→ Combine → Alert
              └→ Audio Extractor → Whisper ──┘

Alert Triggers:
- Person detected AND
- Keywords: ["help", "emergency"] spoken
```

### Example 4: 24/7 Transcription Archive

**Scenario**: Transcribe all audio for searchable archive

```
Camera → Audio Extractor → Whisper (Tiny) → Database Storage
                                          ↓
                                    Text Search Index

Settings:
- Buffer: 30 seconds
- Language: Auto
- Continuous: Yes
- Store: PostgreSQL with full-text search
```

---

## 🎯 Use Cases

### Security Applications

**1. Gunshot Detection**
```
Model: YAMNet
Sounds: Gunshot, Explosion
Confidence: 0.85
Action: Immediate alert + recording
```

**2. Glass Breaking Alert**
```
Model: PANNs CNN14
Sounds: Glass breaking, Smashing
Confidence: 0.80
Action: Security notification
```

**3. Distress Call Detection**
```
Model: Whisper Base
Keywords: ["help", "emergency", "stop", "police"]
Action: Emergency alert with audio clip
```

### Business Applications

**4. Meeting Transcription**
```
Model: Whisper Small
Language: Auto
Output: Full transcript with timestamps
Storage: Document database
```

**5. Customer Service Monitoring**
```
Model: Whisper Base
Keywords: ["complaint", "manager", "refund"]
Action: Flag for review
```

**6. Drive-Through Audio**
```
Model: Whisper Tiny (real-time)
Use: Order taking + verification
Output: Order text + confidence
```

### Industrial Applications

**7. Machine Anomaly Detection**
```
Model: YAMNet
Baseline: Normal machine sounds
Alert: Unusual sounds (bearing failure, etc.)
```

**8. Safety Compliance**
```
Model: YAMNet
Detect: Alarm sounds, sirens
Action: Verify evacuation compliance
```

---

## ⚙️ Configuration Guide

### Choosing Sample Rate

| Sample Rate | Best For | Quality |
|-------------|----------|---------|
| 8kHz | Voice-only, low bandwidth | Phone quality |
| 16kHz | Speech recognition (Whisper) | Good speech |
| 22kHz | General audio | CD-like |
| 44.1kHz | High quality sounds | CD quality |
| 48kHz | Professional audio | Studio quality |

**Recommendation**: 
- Speech (Whisper): 16kHz
- Sound Detection: 44.1kHz
- Real-time: 16kHz or lower

### Choosing Buffer Duration

| Duration | Best For | Latency |
|----------|----------|---------|
| 1-2s | Real-time alerts | Very low |
| 5s | Balanced detection | Low |
| 10-15s | Speech segments | Medium |
| 30s+ | Transcription archive | High |

**Recommendation**:
- Gunshot detection: 2s
- Keyword alerts: 5s
- Meeting transcription: 30s

### Choosing Whisper Model

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| Tiny | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Real-time, edge devices |
| Base | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | General transcription |
| Small | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Professional use |
| Medium | ⚡⚡ | ⭐⭐⭐⭐⭐ | Legal/medical |
| Large | ⚡ | ⭐⭐⭐⭐⭐ | Forensics/research |

---

## 🛠️ Backend Implementation

### Audio Processing Pipeline

```python
1. Extract audio from RTSP stream (FFmpeg)
2. Convert to target sample rate
3. Buffer audio chunks (5s segments)
4. Send to AI model:
   - Whisper → Text transcription
   - YAMNet → Sound classification
5. Post-process results
6. Trigger actions if keywords/sounds detected
```

### Example Backend Code

```python
# Audio extraction
import ffmpeg
import whisper
import numpy as np

def extract_audio_chunk(rtsp_url, duration=5, sample_rate=16000):
    """Extract audio chunk from RTSP stream"""
    process = (
        ffmpeg
        .input(rtsp_url, rtsp_transport='tcp')
        .audio
        .output('pipe:', format='f32le', acodec='pcm_f32le', 
                ac=1, ar=sample_rate, t=duration)
        .run_async(pipe_stdout=True, pipe_stderr=True)
    )
    
    audio_data = process.stdout.read(sample_rate * duration * 4)
    audio_array = np.frombuffer(audio_data, dtype=np.float32)
    
    return audio_array

# Whisper transcription
model = whisper.load_model("base")
audio = extract_audio_chunk(rtsp_url)
result = model.transcribe(audio, language='en')

print(result['text'])
# Output: "Hello, this is a test recording"

# Keyword detection
keywords = ['help', 'emergency', 'fire']
detected = [kw for kw in keywords if kw.lower() in result['text'].lower()]

if detected:
    trigger_alert(keywords=detected, transcript=result['text'])
```

---

## 📊 Sound Classification Classes

### Security-Critical Sounds (YAMNet)

| Class ID | Sound | Typical dB | Detection Confidence |
|----------|-------|------------|---------------------|
| 427 | Gunshot/Gunfire | 140-190 dB | 0.85+ |
| 401 | Explosion | 120-180 dB | 0.90+ |
| 376 | Glass Breaking | 100-120 dB | 0.80+ |
| 389 | Scream | 110-130 dB | 0.75+ |
| 423 | Alarm (Fire/Burglar) | 85-120 dB | 0.85+ |
| 312 | Siren (Police/Ambulance) | 110-130 dB | 0.90+ |
| 298 | Dog Barking (aggressive) | 85-110 dB | 0.70+ |

### Common Environmental Sounds

| Class ID | Sound | Use Case |
|----------|-------|----------|
| 0 | Speech/Conversation | Meeting detection |
| 137 | Music | Noise filtering |
| 188 | Door slam | Entry/exit monitoring |
| 245 | Footsteps | Presence detection |
| 367 | Car horn | Traffic monitoring |
| 412 | Baby crying | Daycare monitoring |

**Full list**: 521 AudioSet classes

---

## 🚀 Quick Start

### 1. **Simple Speech Transcription**

Drag nodes to canvas:
```
Camera → Audio Extractor → Whisper (Base) → Debug Console
```

Configure:
- Audio Extractor: 16kHz, Mono, 5s buffer
- Whisper: Language = Auto Detect
- Click Execute

Watch Debug Console for transcriptions!

### 2. **Gunshot Detection System**

```
Security Camera → Audio Extractor → YAMNet → Action (Emergency Alert)
```

Configure:
- Audio Extractor: 44.1kHz, Mono, 2s buffer
- YAMNet: Confidence = 0.85
- Action: Send immediate notification

### 3. **Keyword Alert System**

```
Reception Camera → Audio Extractor → Whisper (Tiny) → Action (Conditional)
```

Configure:
- Whisper: Keywords = ["help", "emergency", "fire"]
- Action: If keywords detected → Alert security team

---

## 💡 Best Practices

### Performance Optimization

**1. Choose Right Model for Speed:**
```
Real-time alerts     → Whisper Tiny + YAMNet
Transcription archive → Whisper Small
Forensic analysis    → Whisper Large
```

**2. Buffer Duration:**
```
Gunshot detection → 2s (quick response)
Speech keywords   → 5s (catch full phrases)
Meeting archive   → 30s (reduce API calls)
```

**3. Sample Rate:**
```
Speech only      → 16kHz (sufficient for Whisper)
Sound detection  → 44.1kHz (capture full spectrum)
Bandwidth limited → 8kHz (minimum for voice)
```

### Reducing False Positives

**For Sound Detection:**
- Increase confidence threshold (0.85+)
- Use multiple models for verification
- Add zone filtering (ignore audio from certain areas)
- Combine with video detection

**For Keywords:**
- Use longer buffer (catch full context)
- Lowercase matching
- Fuzzy matching for similar words
- Blacklist common false positives

---

## 🔗 Integration with Video Detection

### Combined Video + Audio Workflows

**Example: Comprehensive Security**
```
                    ┌→ YOLOv8 (Person) ─────┐
                    │                        │
Camera (RTSP) ─────┼→ Audio Extractor       ├→ Combine → Alert
                    │      ↓                 │
                    └→ Whisper + YAMNet ────┘

Trigger when:
- Person detected (video) AND
- Keyword spoken (audio) OR Gunshot sound (audio)
```

**Example: Abandoned Object Detection**
```
Video: Detect stationary object (bag, box)
Audio: Listen for ticking, beeping sounds
Combined: Alert on suspicious abandoned object
```

---

## 📋 Supported Languages (Whisper)

Whisper supports 99 languages including:
- English, Spanish, French, German, Italian
- Portuguese, Russian, Japanese, Korean
- Chinese (Mandarin), Arabic, Hindi
- Dutch, Polish, Turkish, Vietnamese
- And 80+ more!

**Auto Detection** identifies language automatically.

---

## 🎯 Common Sound Classes (YAMNet)

### Security
- Gunshot, Explosion, Glass breaking
- Scream, Crying, Shouting
- Alarm (fire, burglar), Siren
- Door slam, Window breaking

### Industrial
- Machine sounds, Motor, Engine
- Drill, Saw, Hammer
- Beep, Buzzer, Click
- Hum, Rattle, Squeak

### Environmental
- Dog bark, Cat meow
- Thunder, Wind, Rain
- Car horn, Traffic
- Footsteps, Door

### Voice
- Speech, Conversation
- Laughter, Cough, Sneeze
- Singing, Whistling

---

## 🔧 Installation (Backend)

### Install Dependencies

All required dependencies are included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Audio Processing Dependencies:**
- `openai-whisper>=20231117` - Speech-to-text transcription
- `tensorflow>=2.13.0` - YAMNet sound classification
- `tensorflow-hub>=0.14.0` - Pre-trained audio models
- `librosa>=0.10.0` - Audio feature extraction
- `soundfile>=0.12.0` - Audio file I/O

### Download Models

```bash
# Whisper models auto-download on first use
# Or pre-download:
python -c "import whisper; whisper.load_model('base')"

# YAMNet model
python -c "import tensorflow_hub as hub; hub.load('https://tfhub.dev/google/yamnet/1')"
```

**Note:** Models are automatically downloaded on first use. Ensure sufficient disk space:
- Whisper Tiny: ~75 MB
- Whisper Base: ~140 MB
- Whisper Small: ~460 MB
- Whisper Medium: ~1.5 GB
- Whisper Large: ~2.9 GB
- YAMNet: ~50 MB

**GPU Support:**
Audio models will automatically use CUDA GPU if available for faster processing. CPU processing is fully supported for all models.

---

## 📊 Performance Benchmarks

### Whisper Models (on CUDA GPU)

| Model | Speed (Real-time Factor) | VRAM | Use Case |
|-------|-------------------------|------|----------|
| Tiny | 32x (32s audio in 1s) | ~1GB | Real-time |
| Base | 16x | ~1GB | Live transcription |
| Small | 6x | ~2GB | Professional |
| Medium | 2x | ~5GB | High accuracy |
| Large | 1x | ~10GB | Best quality |

### Sound Classification (YAMNet)

- **Speed**: ~100x real-time (0.96s audio in 10ms)
- **Memory**: ~50MB
- **CPU**: Low (can run without GPU)

---

## 🚨 Security Use Cases

### 1. Active Shooter Detection
```
Workflow: Parking Lot + Building Cameras
Audio: YAMNet (gunshot detection, 0.90 threshold)
Video: Person detection + motion tracking
Action: Immediate lockdown + 911 call
```

### 2. Distress Call Detection
```
Workflow: All cameras with audio
Audio: Whisper Tiny (real-time)
Keywords: ["help", "emergency", "police", "fire"]
Action: Alert security desk with location
```

### 3. Perimeter Breach
```
Workflow: Fence-line cameras
Audio: YAMNet (glass breaking, metal sounds)
Video: Zone intrusion detection
Action: Security patrol dispatch
```

### 4. Vandalism Detection
```
Workflow: Building exterior
Audio: Glass breaking, spray paint hissing
Video: Person + suspicious objects
Action: Record + alert
```

---

## 🏢 Business Use Cases

### 5. Meeting Transcription
```
Conference Room Camera
→ Audio Extractor (16kHz, 30s buffer)
→ Whisper Small
→ Store in database with searchable index
```

### 6. Customer Service QA
```
Service Desk Camera
→ Audio: Whisper Base
→ Keywords: ["complaint", "manager", "angry"]
→ Flag conversations for review
```

### 7. Retail Analytics
```
Store Camera
→ Audio: Count conversations
→ Video: Count people
→ Combined: Customer engagement metrics
```

---

## 📝 API Endpoints

```
GET /api/workflow-components/audio-models
→ Returns list of available audio AI models

POST /api/audio/transcribe
→ Transcribe audio chunk with Whisper

POST /api/audio/classify
→ Classify sounds with YAMNet/AST

GET /api/audio/sound-classes
→ Get full list of detectable sounds
```

---

## 🎊 Example Workflows

### Security Monitoring (Full Spectrum)
```
Camera (High-security Zone)
  ├→ Video: YOLOv8 (person, weapon detection)
  └→ Audio Extractor
      ├→ Whisper (keyword detection)
      └→ YAMNet (gunshot, alarm)
         ↓
     Combined Analysis
         ↓
     Smart Alerting (reduce false positives)
```

### Meeting Room Intelligence
```
Conference Camera
  └→ Audio Extractor
      └→ Whisper Small
          ├→ Full Transcription → Archive
          ├→ Keyword Search → Action Items
          └→ Speaker Count → Attendance Tracking
```

### Industrial Safety Monitor
```
Factory Camera
  ├→ Video: PPE detection (hard hats, vests)
  └→ Audio: YAMNet
      ├→ Alarm sounds → Verify evacuation
      ├→ Machine sounds → Anomaly detection
      └→ Human speech → Presence in restricted areas
```

---

## ✅ Implementation Status

### ✅ Frontend Complete
- Audio Extractor Node
- Audio AI Node
- Audio models endpoint
- Schema definitions
- Sidebar integration

### ✅ Backend Implemented
- ✅ Audio extraction from RTSP streams (using PyAV)
- ✅ Whisper model integration (all variants: tiny, base, small, medium, large)
- ✅ YAMNet sound classification integration
- ✅ Keyword matching logic for transcriptions
- ✅ Audio action handlers (events, alerts, webhooks)
- ✅ Audio buffer management for chunked processing
- ✅ Real-time audio processing in workflow executor

### Backend Architecture

**Audio Processing Pipeline:**
```
RTSPStream → AudioExtractor → AudioBuffer → AudioAI (Whisper/YAMNet) → EventBus → Actions
```

**Key Components:**
1. **AudioExtractor** (`backend/stream/audio_extractor.py`) - Extracts audio from RTSP streams using PyAV
2. **AudioBuffer** (`backend/stream/audio_buffer.py`) - Thread-safe circular buffer for audio chunks
3. **WhisperModel** (`backend/models/whisper_model.py`) - Speech-to-text transcription
4. **YAMNetModel** (`backend/models/yamnet_model.py`) - Sound classification (521 classes)
5. **RealtimeWorkflowExecutor** - Orchestrates audio processing alongside video

**Model Registry:**
- Whisper variants: `whisper-tiny`, `whisper-base`, `whisper-small`, `whisper-medium`, `whisper-large`
- Sound classifiers: `yamnet`, `audio-spectrogram-transformer`, `panns-cnn14`

**Event System:**
- Audio events: `AUDIO_EXTRACTED`, `AUDIO_TRANSCRIBED`, `SOUND_DETECTED`, `KEYWORD_DETECTED`
- Integration with existing workflow event bus
- WebSocket broadcasting to frontend

---

## 🎯 Quick Reference

### Node Connections
```
Video Stream → Audio Extractor → Audio AI → Action/Debug
```

### Audio AI Settings

**Whisper (Transcription):**
- Model: tiny/base/small/medium/large
- Language: auto or specific
- Keywords: Optional trigger words
- Buffer: 5-30s recommended

**YAMNet (Sound Classification):**
- Confidence: 0.70-0.90
- Target sounds: Select from 521 classes
- Buffer: 2-5s recommended

---

*Last updated: October 30, 2025*  
*Version: 1.0.0*  
*Status: ✅ Fully Implemented (Frontend + Backend)*

