"""
Whisper Model Plugin
Speech-to-text transcription using OpenAI Whisper
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

import numpy as np
import torch
import whisper
import librosa

from core.config import settings
from .audio_base import AudioBaseModel, AudioResult


logger = logging.getLogger('overwatch.models.whisper')


class WhisperModel(AudioBaseModel):
    """OpenAI Whisper speech-to-text model"""
    
    def __init__(self, model_id: str, config: dict):
        super().__init__(model_id, config)
        self.device = settings.DEVICE
        self.variant = self._get_variant()
        
    def _get_variant(self) -> str:
        """Extract Whisper variant from model_id"""
        # model_id is like 'whisper-tiny', 'whisper-base', etc.
        parts = self.model_id.split('-')
        if len(parts) >= 2:
            return parts[1]  # 'tiny', 'base', 'small', 'medium', 'large'
        return 'base'
        
    async def initialize(self):
        """Initialize Whisper model"""
        logger.info(f"Loading Whisper model ({self.variant})...")
        
        # Load model in executor to avoid blocking
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            self._load_model
        )
        
        logger.info(f"Loaded Whisper {self.variant} on {self.device}")
        
    def _load_model(self) -> whisper.Whisper:
        """Load Whisper model (blocking operation)"""
        # Load model
        model = whisper.load_model(self.variant)
        
        # Move to device
        if self.device == 'cuda' and torch.cuda.is_available():
            model = model.to('cuda')
        else:
            model = model.to('cpu')
            
        return model
        
    async def process_audio(self, audio_data: np.ndarray, sample_rate: int) -> Optional[AudioResult]:
        """
        Transcribe audio using Whisper
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            
        Returns:
            AudioResult with transcription
        """
        if self.model is None:
            logger.error("Model not initialized")
            return None
            
        # Run transcription in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._run_transcription,
            audio_data,
            sample_rate
        )
        
        return result
        
    def _run_transcription(self, audio_data: np.ndarray, sample_rate: int) -> Optional[AudioResult]:
        """Run Whisper transcription (blocking operation)"""
        try:
            # Resample to 16kHz if needed (Whisper requirement)
            if sample_rate != 16000:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=16000
                )
            
            # Convert to float32 and normalize
            audio_data = audio_data.astype(np.float32)
            if audio_data.max() > 1.0:
                audio_data = audio_data / 32768.0  # Normalize int16 to float32
            
            # Get language from config (default: auto-detect)
            language = self.config.get('language', None)
            if language == 'auto':
                language = None
            
            # Run transcription
            result = self.model.transcribe(
                audio_data,
                language=language,
                fp16=(self.device == 'cuda')
            )
            
            # Extract results
            text = result['text'].strip()
            detected_language = result.get('language', 'unknown')
            
            # Calculate average confidence from segments
            segments = result.get('segments', [])
            if segments:
                avg_confidence = sum(s.get('no_speech_prob', 0.0) for s in segments) / len(segments)
                confidence = 1.0 - avg_confidence  # Invert no_speech_prob to get confidence
            else:
                confidence = 0.0
            
            # Check for keyword matches
            keywords_detected = []
            detect_keywords = self.config.get('detectKeywords', [])
            if detect_keywords and text:
                text_lower = text.lower()
                for keyword in detect_keywords:
                    if keyword.lower() in text_lower:
                        keywords_detected.append(keyword)
            
            # Return AudioResult
            return AudioResult(
                text=text,
                language=detected_language,
                confidence=confidence,
                keywords_detected=keywords_detected,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
        
    async def cleanup(self):
        """Cleanup model resources"""
        if self.model:
            del self.model
            self.model = None
            
            # Clear CUDA cache if using GPU
            if self.device == 'cuda' and torch.cuda.is_available():
                torch.cuda.empty_cache()


