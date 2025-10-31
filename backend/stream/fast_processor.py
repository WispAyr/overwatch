"""
Fast Frame Processor - Python Integration Layer

This module provides a Python wrapper around the C++ frame processor,
with automatic fallback to Python implementations if C++ module is unavailable.
"""

import logging
import numpy as np
from typing import List, Optional, Union
import cv2

logger = logging.getLogger('overwatch.stream.fast_processor')

# Try to import C++ accelerated module
try:
    import sys
    sys.path.insert(0, '/Users/ewanrichardson/Development/overwatch/backend/cpp_preproc')
    from frame_processor import FrameProcessor as CppFrameProcessor
    CPP_AVAILABLE = True
    logger.info("✓ C++ frame processor loaded - using accelerated path")
except ImportError as e:
    CPP_AVAILABLE = False
    logger.warning(f"C++ frame processor not available, falling back to Python: {e}")
    logger.warning("For 5-10x better performance, build C++ module with: cd backend/cpp_preproc && ./build.sh")


class FastFrameProcessor:
    """
    High-performance frame processor with automatic C++/Python fallback
    
    Usage:
        processor = FastFrameProcessor()
        
        # Single frame JPEG encoding (2-6x faster than cv2.imencode)
        jpeg_bytes = processor.encode_jpeg(frame, quality=85)
        
        # Batch JPEG encoding (parallel processing)
        jpeg_list = processor.batch_encode_jpeg([frame1, frame2, frame3], quality=85)
        
        # Frame preprocessing for AI inference
        preprocessed = processor.preprocess_for_inference(
            frame, 
            target_width=640,
            target_height=640,
            normalize=True,
            rgb_conversion=True
        )
    """
    
    def __init__(self, num_threads: int = 0):
        """
        Initialize processor
        
        Args:
            num_threads: Number of threads for parallel processing (0 = auto)
        """
        self.num_threads = num_threads
        self.using_cpp = CPP_AVAILABLE
        
        if CPP_AVAILABLE:
            self._processor = CppFrameProcessor(num_threads)
            logger.info(f"Initialized C++ processor with {num_threads or 'auto'} threads")
        else:
            self._processor = None
            
    def encode_jpeg(self, frame: np.ndarray, quality: int = 85) -> bytes:
        """
        Encode frame to JPEG
        
        Args:
            frame: Input frame (HxWxC numpy array)
            quality: JPEG quality 0-100 (higher = better quality, larger size)
            
        Returns:
            JPEG encoded bytes
        """
        if self.using_cpp:
            return self._processor.encode_jpeg(frame, quality)
        else:
            # Fallback to OpenCV
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if not ret:
                raise RuntimeError("Failed to encode JPEG")
            return buffer.tobytes()
    
    def batch_encode_jpeg(self, frames: List[np.ndarray], quality: int = 85) -> List[bytes]:
        """
        Batch encode multiple frames to JPEG in parallel
        
        Args:
            frames: List of input frames
            quality: JPEG quality 0-100
            
        Returns:
            List of JPEG encoded bytes
        """
        if self.using_cpp:
            return self._processor.batch_encode_jpeg(frames, quality)
        else:
            # Fallback to sequential encoding
            results = []
            for frame in frames:
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                if ret:
                    results.append(buffer.tobytes())
                else:
                    results.append(b'')
            return results
    
    def resize_frame(self, frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Resize frame to target dimensions
        
        Args:
            frame: Input frame
            width: Target width
            height: Target height
            
        Returns:
            Resized frame
        """
        if self.using_cpp:
            return self._processor.resize_frame(frame, width, height)
        else:
            return cv2.resize(frame, (width, height))
    
    def preprocess_for_inference(
        self,
        frame: np.ndarray,
        target_width: int = 640,
        target_height: int = 640,
        normalize: bool = True,
        rgb_conversion: bool = True
    ) -> dict:
        """
        Preprocess frame for AI model inference
        
        Operations performed:
        1. Resize to target dimensions
        2. Color conversion (BGR -> RGB)
        3. Normalization to [0, 1] range
        
        Args:
            frame: Input frame (BGR format)
            target_width: Target width for inference
            target_height: Target height for inference
            normalize: Normalize to [0, 1] range
            rgb_conversion: Convert BGR to RGB
            
        Returns:
            dict with 'data' (preprocessed array), 'width', 'height', 'channels'
        """
        if self.using_cpp:
            return self._processor.preprocess_for_inference(
                frame, target_width, target_height, normalize, rgb_conversion
            )
        else:
            # Fallback implementation
            processed = cv2.resize(frame, (target_width, target_height))
            
            if rgb_conversion:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            
            if normalize:
                processed = processed.astype(np.float32) / 255.0
            
            return {
                'data': processed,
                'width': target_width,
                'height': target_height,
                'channels': processed.shape[2] if len(processed.shape) > 2 else 1
            }
    
    def bgr_to_rgb(self, frame: np.ndarray) -> np.ndarray:
        """Convert BGR to RGB"""
        if self.using_cpp:
            return self._processor.bgr_to_rgb(frame)
        else:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def rgb_to_bgr(self, frame: np.ndarray) -> np.ndarray:
        """Convert RGB to BGR"""
        if self.using_cpp:
            return self._processor.rgb_to_bgr(frame)
        else:
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    def get_stats(self) -> dict:
        """Get processor statistics"""
        if self.using_cpp:
            return {
                'using_cpp': True,
                'frames_processed': self._processor.get_frames_processed(),
                'bytes_encoded': self._processor.get_bytes_encoded(),
                'num_threads': self.num_threads
            }
        else:
            return {
                'using_cpp': False,
                'frames_processed': 0,
                'bytes_encoded': 0,
                'num_threads': 0
            }
    
    def reset_stats(self):
        """Reset statistics counters"""
        if self.using_cpp:
            self._processor.reset_stats()


# Global singleton instance
_global_processor: Optional[FastFrameProcessor] = None


def get_processor(num_threads: int = 0) -> FastFrameProcessor:
    """
    Get global frame processor instance (singleton pattern)
    
    Args:
        num_threads: Number of threads (only used on first call)
        
    Returns:
        FastFrameProcessor instance
    """
    global _global_processor
    
    if _global_processor is None:
        _global_processor = FastFrameProcessor(num_threads)
    
    return _global_processor


# Convenience functions using global processor
def encode_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encode frame to JPEG using global processor"""
    return get_processor().encode_jpeg(frame, quality)


def batch_encode_jpeg(frames: List[np.ndarray], quality: int = 85) -> List[bytes]:
    """Batch encode frames to JPEG using global processor"""
    return get_processor().batch_encode_jpeg(frames, quality)


def preprocess_for_inference(
    frame: np.ndarray,
    target_width: int = 640,
    target_height: int = 640,
    normalize: bool = True,
    rgb_conversion: bool = True
) -> dict:
    """Preprocess frame for inference using global processor"""
    return get_processor().preprocess_for_inference(
        frame, target_width, target_height, normalize, rgb_conversion
    )

