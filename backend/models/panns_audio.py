"""
PANNs Audio Model Plugin
Pretrained Audio Neural Networks for audio event detection
Superior to YAMNet for specific event detection (gunshots, glass breaking, alarms)
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import numpy as np

from .audio_base import AudioBaseModel, SoundClassification


logger = logging.getLogger('overwatch.models.panns')


class PANNsModel(AudioBaseModel):
    """
    PANNs (Pretrained Audio Neural Networks) for audio event detection
    
    Better than YAMNet for:
    - Gunshot detection
    - Glass breaking
    - Alarm sounds
    - Screaming/distress
    - Vehicle sounds
    """
    
    EXPECTED_SAMPLE_RATE = 32000  # PANNs expects 32kHz
    
    # AudioSet class indices for security events
    SECURITY_EVENTS = {
        'gunshot': [427, 428],  # Gunshot, machine gun
        'glass_breaking': [410],  # Glass breaking
        'alarm': [388, 389, 390, 391],  # Smoke detector, alarm, siren
        'scream': [137],  # Screaming
        'explosion': [424],  # Explosion
        'crash': [411, 412],  # Crash, vehicle
        'dog_bark': [74, 75],  # Barking, aggressive
    }
    
    async def initialize(self):
        """Initialize PANNs model"""
        logger.info("Loading PANNs model...")
        
        try:
            import torch
            import torchaudio
            self.torch = torch
            self.torchaudio = torchaudio
            
            # Load PANNs model from torchaudio
            loop = asyncio.get_event_loop()
            self.model, self.class_names = await loop.run_in_executor(
                None,
                self._load_model
            )
            
            logger.info(f"Loaded PANNs with {len(self.class_names)} audio classes")
            
        except ImportError as e:
            logger.error(f"Missing dependency: {e}. Install with: pip install torch torchaudio")
            raise
    
    def _load_model(self):
        """Load PANNs model (blocking operation)"""
        import torch
        
        # Load pretrained PANNs CNN14 model
        bundle = self.torchaudio.pipelines.CONVTASNET_BASE_LIBRI2MIX
        # For audio classification, we'd use a different bundle
        # For now, using a placeholder - in production you'd load actual PANNs
        
        # Placeholder: Load AudioSet class names
        class_names = self._get_audioset_classes()
        
        # In production, load actual PANNs model:
        # model = torch.hub.load('qiuqiangkong/audioset_tagging_cnn', 'Cnn14')
        # For now, we'll create a stub
        model = None
        
        return model, class_names
    
    def _get_audioset_classes(self) -> List[str]:
        """Get AudioSet class names"""
        # Simplified - in production load full AudioSet ontology
        return [
            'Speech', 'Music', 'Gunshot', 'Glass breaking', 'Alarm', 
            'Scream', 'Explosion', 'Dog bark', 'Siren', 'Vehicle',
            'Door slam', 'Footsteps', 'Crying', 'Cough', 'Laughter'
        ]
    
    async def process_audio(self, audio_data: np.ndarray, sample_rate: int) -> List[SoundClassification]:
        """
        Classify audio events using PANNs
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            
        Returns:
            List of SoundClassification results with focus on security events
        """
        if self.model is None:
            logger.warning("PANNs model not fully initialized - using fallback detection")
            return self._fallback_detection(audio_data, sample_rate)
        
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
        """Run PANNs classification (blocking operation)"""
        try:
            import librosa
            
            # Resample to 32kHz if needed
            if sample_rate != self.EXPECTED_SAMPLE_RATE:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=self.EXPECTED_SAMPLE_RATE
                )
            
            # Normalize audio
            audio_data = audio_data.astype(np.float32)
            if audio_data.max() > 1.0:
                audio_data = audio_data / 32768.0
            
            # Ensure mono
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # In production, run actual PANNs inference here
            # For now, use fallback
            return self._fallback_detection(audio_data, sample_rate)
            
        except Exception as e:
            logger.error(f"PANNs classification error: {e}")
            return []
    
    def _fallback_detection(self, audio_data: np.ndarray, sample_rate: int) -> List[SoundClassification]:
        """
        Fallback detection using signal processing
        Detects loud events that might be security-relevant
        """
        try:
            import librosa
            
            classifications = []
            
            # Calculate RMS energy
            rms = librosa.feature.rms(y=audio_data)[0]
            mean_rms = np.mean(rms)
            
            # Detect loud transient events (potential gunshots, glass breaking)
            loud_threshold = self.config.get('loud_threshold', 0.3)
            if mean_rms > loud_threshold:
                # Calculate spectral characteristics
                spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
                mean_centroid = np.mean(spectral_centroid)
                
                # Rough heuristics for event classification
                if mean_centroid > 3000:  # High frequency = glass/metal
                    event_type = 'glass_breaking'
                    confidence = min(0.9, mean_rms * 2)
                elif mean_rms > 0.5:  # Very loud = potential gunshot/explosion
                    event_type = 'loud_bang'
                    confidence = min(0.9, mean_rms * 1.5)
                else:
                    event_type = 'loud_sound'
                    confidence = min(0.8, mean_rms * 1.2)
                
                classifications.append(SoundClassification(
                    sound_class=event_type,
                    confidence=float(confidence),
                    timestamp=datetime.now(),
                    metadata={
                        'rms_energy': float(mean_rms),
                        'spectral_centroid': float(mean_centroid),
                        'detection_method': 'signal_processing'
                    }
                ))
            
            return classifications
            
        except Exception as e:
            logger.error(f"Fallback detection error: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup model resources"""
        if hasattr(self, 'model') and self.model:
            del self.model
            self.model = None


