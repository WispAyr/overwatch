"""
YAMNet Model Plugin
Sound classification using Google YAMNet
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import librosa

from .audio_base import AudioBaseModel, SoundClassification


logger = logging.getLogger('overwatch.models.yamnet')


class YAMNetModel(AudioBaseModel):
    """Google YAMNet sound classification model"""
    
    # YAMNet expects 16kHz mono audio
    EXPECTED_SAMPLE_RATE = 16000
    
    def __init__(self, model_id: str, config: dict):
        super().__init__(model_id, config)
        self.class_names = None
        
    async def initialize(self):
        """Initialize YAMNet model"""
        logger.info("Loading YAMNet model from TensorFlow Hub...")
        
        # Load model in executor to avoid blocking
        loop = asyncio.get_event_loop()
        self.model, self.class_names = await loop.run_in_executor(
            None,
            self._load_model
        )
        
        logger.info(f"Loaded YAMNet with {len(self.class_names)} sound classes")
        
    def _load_model(self):
        """Load YAMNet model (blocking operation)"""
        # Load YAMNet model from TensorFlow Hub
        model = hub.load('https://tfhub.dev/google/yamnet/1')
        
        # Load class names from model
        class_map_path = model.class_map_path().numpy()
        class_names = []
        
        # Read class names from CSV
        with open(class_map_path, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    class_names.append(parts[2])  # Display name
        
        return model, class_names
        
    async def process_audio(self, audio_data: np.ndarray, sample_rate: int) -> List[SoundClassification]:
        """
        Classify sounds in audio using YAMNet
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            
        Returns:
            List of SoundClassification results
        """
        if self.model is None:
            logger.error("Model not initialized")
            return []
            
        # Run classification in executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._run_classification,
            audio_data,
            sample_rate
        )
        
        return results
        
    def _run_classification(self, audio_data: np.ndarray, sample_rate: int) -> List[SoundClassification]:
        """Run YAMNet classification (blocking operation)"""
        try:
            # Resample to 16kHz if needed (YAMNet requirement)
            if sample_rate != self.EXPECTED_SAMPLE_RATE:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=self.EXPECTED_SAMPLE_RATE
                )
            
            # Convert to float32 and normalize
            audio_data = audio_data.astype(np.float32)
            if audio_data.max() > 1.0:
                audio_data = audio_data / 32768.0  # Normalize int16 to float32
            
            # Ensure mono audio
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Run YAMNet inference
            scores, embeddings, spectrogram = self.model(audio_data)
            
            # Get confidence threshold from config
            confidence_threshold = self.config.get('confidence', 0.7)
            
            # Convert scores to numpy
            scores_np = scores.numpy()
            
            # Get mean scores across all time frames
            mean_scores = np.mean(scores_np, axis=0)
            
            # Get top classifications above threshold
            classifications = []
            top_indices = np.argsort(mean_scores)[::-1]  # Sort descending
            
            # Limit to top 5 classes
            for idx in top_indices[:5]:
                confidence = float(mean_scores[idx])
                
                if confidence >= confidence_threshold:
                    class_name = self.class_names[idx] if idx < len(self.class_names) else f"class_{idx}"
                    
                    classification = SoundClassification(
                        sound_class=class_name,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        metadata={
                            'class_id': int(idx),
                            'num_frames': len(scores_np)
                        }
                    )
                    classifications.append(classification)
            
            return classifications
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return []
        
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None
            self.class_names = None
            
            # Clear TensorFlow session
            tf.keras.backend.clear_session()


