"""
Audio Base Model Plugin
Abstract base class for audio AI models
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class AudioResult:
    """Transcription result from audio processing"""
    text: str
    language: str
    confidence: float
    keywords_detected: List[str]
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'language': self.language,
            'confidence': self.confidence,
            'keywords_detected': self.keywords_detected,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SoundClassification:
    """Sound classification result"""
    sound_class: str
    confidence: float
    timestamp: datetime
    metadata: dict
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'sound_class': self.sound_class,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class AudioBaseModel(ABC):
    """Base class for audio AI model plugins"""
    
    def __init__(self, model_id: str, config: dict):
        self.model_id = model_id
        self.config = config
        self.model = None
        self.model_type = config.get('modelType', 'transcription')  # 'transcription' or 'sound_classification'
        
    @abstractmethod
    async def initialize(self):
        """Initialize the model"""
        pass
        
    @abstractmethod
    async def process_audio(self, audio_data: np.ndarray, sample_rate: int):
        """
        Process audio data
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            
        Returns:
            AudioResult for transcription or List[SoundClassification] for sound classification
        """
        pass
        
    @abstractmethod
    async def cleanup(self):
        """Cleanup model resources"""
        pass


