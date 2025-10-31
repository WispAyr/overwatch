"""
Base Model Plugin
Abstract base class for AI models
"""
from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np


class Detection:
    """Detection result"""
    def __init__(
        self,
        class_id: int,
        class_name: str,
        confidence: float,
        bbox: List[float],
        **kwargs
    ):
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.metadata = kwargs
        
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'confidence': self.confidence,
            'bbox': self.bbox,
            **self.metadata
        }


class BaseModel(ABC):
    """Base class for AI model plugins"""
    
    def __init__(self, model_id: str, config: dict):
        self.model_id = model_id
        self.config = config
        self.model = None
        
    @abstractmethod
    async def initialize(self):
        """Initialize the model"""
        pass
        
    @abstractmethod
    async def detect(self, frame: np.ndarray) -> List[dict]:
        """
        Run detection on a frame
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            List of detection dictionaries
        """
        pass
        
    @abstractmethod
    async def cleanup(self):
        """Cleanup model resources"""
        pass

