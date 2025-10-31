"""
Performance Profiling and Optimization Module
Measures and optimizes AI model and visualization pipeline
"""
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
import numpy as np

logger = logging.getLogger('overwatch.performance')


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation"""
    operation: str
    duration_ms: float
    timestamp: float
    metadata: Dict = field(default_factory=dict)


class PerformanceProfiler:
    """Profiles performance of AI pipeline operations"""
    
    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.metrics: Dict[str, deque] = {}
        self.frame_times: deque = deque(maxlen=max_samples)
        self.current_timers: Dict[str, float] = {}
        
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.current_timers[operation] = time.time()
        
    def end_timer(self, operation: str, metadata: Optional[Dict] = None) -> float:
        """End timing and record metrics"""
        if operation not in self.current_timers:
            logger.warning(f"Timer '{operation}' was not started")
            return 0.0
            
        start_time = self.current_timers.pop(operation)
        duration = (time.time() - start_time) * 1000  # Convert to ms
        
        # Initialize deque for this operation if needed
        if operation not in self.metrics:
            self.metrics[operation] = deque(maxlen=self.max_samples)
            
        # Record metric
        metric = PerformanceMetrics(
            operation=operation,
            duration_ms=duration,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.metrics[operation].append(metric)
        
        return duration
        
    def get_stats(self, operation: str) -> Dict:
        """Get statistics for an operation"""
        if operation not in self.metrics or len(self.metrics[operation]) == 0:
            return {
                'count': 0,
                'avg_ms': 0,
                'min_ms': 0,
                'max_ms': 0,
                'p95_ms': 0,
                'p99_ms': 0
            }
            
        durations = [m.duration_ms for m in self.metrics[operation]]
        
        return {
            'count': len(durations),
            'avg_ms': np.mean(durations),
            'min_ms': np.min(durations),
            'max_ms': np.max(durations),
            'p95_ms': np.percentile(durations, 95),
            'p99_ms': np.percentile(durations, 99),
            'std_ms': np.std(durations)
        }
        
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all operations"""
        return {op: self.get_stats(op) for op in self.metrics.keys()}
        
    def log_stats(self, operations: Optional[List[str]] = None):
        """Log performance statistics"""
        ops = operations or list(self.metrics.keys())
        
        logger.info("=" * 80)
        logger.info("PERFORMANCE STATISTICS")
        logger.info("=" * 80)
        
        for op in ops:
            stats = self.get_stats(op)
            if stats['count'] > 0:
                logger.info(
                    f"{op:30s} | "
                    f"Avg: {stats['avg_ms']:6.2f}ms | "
                    f"P95: {stats['p95_ms']:6.2f}ms | "
                    f"P99: {stats['p99_ms']:6.2f}ms | "
                    f"Min: {stats['min_ms']:6.2f}ms | "
                    f"Max: {stats['max_ms']:6.2f}ms | "
                    f"Samples: {stats['count']}"
                )
        
        logger.info("=" * 80)
        
    def calculate_fps(self, window_seconds: float = 5.0) -> float:
        """Calculate current FPS based on recent frames"""
        if len(self.frame_times) < 2:
            return 0.0
            
        current_time = time.time()
        recent_frames = [
            t for t in self.frame_times 
            if current_time - t <= window_seconds
        ]
        
        if len(recent_frames) < 2:
            return 0.0
            
        time_span = recent_frames[-1] - recent_frames[0]
        if time_span == 0:
            return 0.0
            
        return (len(recent_frames) - 1) / time_span
        
    def record_frame(self):
        """Record a frame for FPS calculation"""
        self.frame_times.append(time.time())
        
    def get_bottlenecks(self, threshold_ms: float = 50.0) -> List[tuple]:
        """Identify operations that are bottlenecks"""
        bottlenecks = []
        
        for operation, stats in self.get_all_stats().items():
            if stats['avg_ms'] > threshold_ms:
                bottlenecks.append((operation, stats['avg_ms']))
                
        # Sort by duration (worst first)
        bottlenecks.sort(key=lambda x: x[1], reverse=True)
        return bottlenecks
        
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.frame_times.clear()
        self.current_timers.clear()


class FrameCache:
    """Intelligent frame caching to skip redundant processing"""
    
    def __init__(self, similarity_threshold: float = 0.95, max_cache_size: int = 10):
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.cache: deque = deque(maxlen=max_cache_size)
        self.last_hash = None
        
    def compute_hash(self, frame: np.ndarray) -> int:
        """Compute fast perceptual hash of frame"""
        # Downsample frame for fast comparison
        small = frame[::8, ::8]
        return hash(small.tobytes())
        
    def compute_similarity(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Compute similarity between frames (0-1)"""
        # Downsample for speed
        small1 = frame1[::4, ::4].astype(np.float32)
        small2 = frame2[::4, ::4].astype(np.float32)
        
        # Normalized cross-correlation
        diff = np.abs(small1 - small2)
        max_diff = 255.0
        similarity = 1.0 - (np.mean(diff) / max_diff)
        
        return similarity
        
    def should_process(self, frame: np.ndarray) -> bool:
        """Determine if frame should be processed"""
        if len(self.cache) == 0:
            self.cache.append(frame.copy())
            return True
            
        # Check against most recent frame
        last_frame = self.cache[-1]
        similarity = self.compute_similarity(frame, last_frame)
        
        if similarity >= self.similarity_threshold:
            # Too similar, skip processing
            return False
        else:
            # Different enough, process it
            self.cache.append(frame.copy())
            return True
            
    def reset(self):
        """Clear cache"""
        self.cache.clear()
        self.last_hash = None


class BatchProcessor:
    """Batch multiple frames for GPU efficiency"""
    
    def __init__(self, batch_size: int = 1, max_wait_ms: float = 50.0):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.batch: List[np.ndarray] = []
        self.batch_start_time: Optional[float] = None
        
    def add_frame(self, frame: np.ndarray) -> Optional[List[np.ndarray]]:
        """
        Add frame to batch, returns batch if ready
        
        Returns:
            List of frames if batch is ready, None otherwise
        """
        if len(self.batch) == 0:
            self.batch_start_time = time.time()
            
        self.batch.append(frame)
        
        # Check if batch is ready
        batch_ready = (
            len(self.batch) >= self.batch_size or
            (time.time() - self.batch_start_time) * 1000 >= self.max_wait_ms
        )
        
        if batch_ready:
            ready_batch = self.batch.copy()
            self.batch.clear()
            self.batch_start_time = None
            return ready_batch
            
        return None
        
    def flush(self) -> List[np.ndarray]:
        """Force return current batch"""
        batch = self.batch.copy()
        self.batch.clear()
        self.batch_start_time = None
        return batch


# Global profiler instance
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance"""
    return _profiler

