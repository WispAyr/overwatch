"""
Audio Analyzer - Real-time audio level and frequency spectrum analysis
"""
import numpy as np
import time
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Analyze audio for VU meter and frequency spectrum visualization"""
    
    def __init__(self, sample_rate: int = 48000):
        """
        Initialize audio analyzer
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
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
        try:
            # Convert to mono if stereo
            if len(audio_chunk.shape) > 1:
                audio_mono = np.mean(audio_chunk, axis=1)
            else:
                audio_mono = audio_chunk
                
            # Handle empty audio
            if len(audio_mono) == 0:
                return self._empty_result()
            
            # Calculate RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_mono ** 2))
            
            # Calculate peak
            peak = np.max(np.abs(audio_mono))
            
            # Convert RMS to dB (relative to peak = 0 dB)
            # Prevent log(0) with small epsilon
            if rms > 0:
                level_db = 20 * np.log10(rms + 1e-10)
                # Normalize to 0-100 range (assuming -60dB to 0dB range)
                level_db_normalized = max(0, min(100, (level_db + 60) * (100/60)))
            else:
                level_db_normalized = 0.0
            
            # Calculate frequency spectrum using FFT
            spectrum = self.calculate_spectrum(audio_mono, num_bands=32)
            
            return {
                'level_db': float(level_db_normalized),
                'rms': float(rms),
                'peak': float(peak),
                'spectrum': spectrum,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Error calculating audio levels: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict:
        """Return empty/zero result"""
        return {
            'level_db': 0.0,
            'rms': 0.0,
            'peak': 0.0,
            'spectrum': [0.0] * 32,
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
        try:
            # Handle short audio
            if len(audio) < self.fft_size:
                # Pad with zeros
                audio = np.pad(audio, (0, self.fft_size - len(audio)))
            
            # Perform FFT on first fft_size samples
            fft = np.fft.rfft(audio[:self.fft_size])
            magnitude = np.abs(fft)
            
            # Convert to dB
            magnitude_db = 20 * np.log10(magnitude + 1e-10)
            
            # Group into frequency bands
            band_size = max(1, len(magnitude_db) // num_bands)
            bands = []
            
            for i in range(num_bands):
                start_idx = i * band_size
                end_idx = min(start_idx + band_size, len(magnitude_db))
                
                if start_idx < len(magnitude_db):
                    # Average magnitude for this band
                    band_avg = np.mean(magnitude_db[start_idx:end_idx])
                    
                    # Normalize to 0-100 range (assuming -60dB to 0dB)
                    band_normalized = max(0, min(100, (band_avg + 60) * (100/60)))
                    bands.append(float(band_normalized))
                else:
                    bands.append(0.0)
            
            return bands
        except Exception as e:
            logger.error(f"Error calculating spectrum: {e}")
            return [0.0] * num_bands
    
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
            # Subtract hysteresis to prevent rapid toggling
            return level_db >= (threshold - hysteresis)
        else:
            # Not triggered, check if we should turn on
            return level_db >= threshold
    
    def get_frequency_band_labels(self, num_bands: int = 32) -> List[str]:
        """
        Get frequency labels for spectrum bands
        
        Args:
            num_bands: Number of frequency bands
            
        Returns:
            List of frequency range labels (e.g., "20-100 Hz")
        """
        nyquist = self.sample_rate // 2
        band_width = nyquist / num_bands
        
        labels = []
        for i in range(num_bands):
            low_freq = int(i * band_width)
            high_freq = int((i + 1) * band_width)
            
            # Format nicely
            if low_freq < 1000:
                low = f"{low_freq}"
            else:
                low = f"{low_freq/1000:.1f}k"
                
            if high_freq < 1000:
                high = f"{high_freq}"
            else:
                high = f"{high_freq/1000:.1f}k"
            
            labels.append(f"{low}-{high} Hz")
        
        return labels


