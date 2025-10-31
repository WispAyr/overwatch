"""
Frame Buffer
Circular buffer for video frames to smooth out stream interruptions
"""
import threading
import numpy as np
from collections import deque
from typing import Optional


class FrameBuffer:
    """Thread-safe circular frame buffer"""
    
    def __init__(self, max_size: int = 10):
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
        self.last_frame = None
        
    def put(self, frame: np.ndarray):
        """Add frame to buffer"""
        with self.lock:
            self.buffer.append(frame.copy())
            self.last_frame = frame.copy()
            
    def get_latest(self) -> Optional[np.ndarray]:
        """Get most recent frame"""
        with self.lock:
            if self.buffer:
                return self.buffer[-1].copy()
            return self.last_frame.copy() if self.last_frame is not None else None
            
    def get(self) -> Optional[np.ndarray]:
        """Get and remove oldest frame"""
        with self.lock:
            if self.buffer:
                return self.buffer.popleft()
            return None
            
    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.buffer.clear()
            
    def size(self) -> int:
        """Get buffer size"""
        with self.lock:
            return len(self.buffer)


