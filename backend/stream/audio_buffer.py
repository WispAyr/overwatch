"""
Audio Buffer
Circular buffer for audio samples to enable chunked processing
"""
import threading
import numpy as np
from collections import deque
from typing import Optional
from datetime import datetime


class AudioChunk:
    """Audio chunk with metadata"""
    def __init__(self, data: np.ndarray, sample_rate: int, timestamp: datetime):
        self.data = data
        self.sample_rate = sample_rate
        self.timestamp = timestamp
        self.duration = len(data) / sample_rate  # Duration in seconds


class AudioBuffer:
    """Thread-safe circular audio buffer"""
    
    def __init__(self, max_duration_seconds: float = 60.0):
        """
        Initialize audio buffer
        
        Args:
            max_duration_seconds: Maximum buffer duration in seconds
        """
        self.buffer = deque()
        self.lock = threading.Lock()
        self.max_duration = max_duration_seconds
        self.total_duration = 0.0
        
    def put(self, audio_chunk: np.ndarray, sample_rate: int, timestamp: datetime = None):
        """
        Add audio chunk to buffer
        
        Args:
            audio_chunk: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            timestamp: Optional timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        chunk = AudioChunk(audio_chunk.copy(), sample_rate, timestamp)
        
        with self.lock:
            self.buffer.append(chunk)
            self.total_duration += chunk.duration
            
            # Trim old audio if buffer exceeds max duration
            while self.total_duration > self.max_duration and len(self.buffer) > 1:
                removed_chunk = self.buffer.popleft()
                self.total_duration -= removed_chunk.duration
                
    def get_chunk(self, duration_seconds: float) -> Optional[tuple[np.ndarray, int, datetime]]:
        """
        Retrieve audio chunk of specified duration
        
        Args:
            duration_seconds: Desired duration in seconds
            
        Returns:
            Tuple of (audio_data, sample_rate, timestamp) or None if not enough data
        """
        with self.lock:
            if not self.buffer:
                return None
                
            # Collect chunks until we have enough duration
            collected_chunks = []
            collected_duration = 0.0
            sample_rate = None
            first_timestamp = None
            
            for chunk in reversed(self.buffer):  # Start from most recent
                if sample_rate is None:
                    sample_rate = chunk.sample_rate
                    first_timestamp = chunk.timestamp
                    
                # Only combine chunks with same sample rate
                if chunk.sample_rate != sample_rate:
                    break
                    
                collected_chunks.insert(0, chunk.data)
                collected_duration += chunk.duration
                first_timestamp = chunk.timestamp  # Update to earliest timestamp
                
                if collected_duration >= duration_seconds:
                    break
            
            if not collected_chunks or collected_duration < duration_seconds * 0.5:
                # Not enough data (need at least 50% of requested duration)
                return None
                
            # Concatenate chunks
            audio_data = np.concatenate(collected_chunks)
            
            # Trim to exact duration
            target_samples = int(duration_seconds * sample_rate)
            if len(audio_data) > target_samples:
                audio_data = audio_data[-target_samples:]  # Take most recent samples
                
            return audio_data, sample_rate, first_timestamp
            
    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.buffer.clear()
            self.total_duration = 0.0
            
    def size(self) -> float:
        """Get current buffer size in seconds"""
        with self.lock:
            return self.total_duration


