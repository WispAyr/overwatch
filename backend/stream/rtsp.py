"""
RTSP Stream Handler
Handles individual RTSP camera stream
"""
import asyncio
import logging
import time
from typing import List, Optional
from datetime import datetime

import cv2
import numpy as np

from .frame_buffer import FrameBuffer


logger = logging.getLogger('overwatch.stream.rtsp')


class RTSPStream:
    """RTSP stream handler"""
    
    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        workflow_engine,
        workflows: List[str]
    ):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.workflow_engine = workflow_engine
        self.workflows = workflows
        
        self.capture = None
        self.running = False
        self.task = None
        
        # Frame buffer for smooth playback
        self.frame_buffer = FrameBuffer(max_size=5)
        
        # Stats
        self.fps = 0.0
        self.frame_count = 0
        self.last_frame_time = None
        self.start_time = None
        self.error_count = 0
        
    async def start(self):
        """Start the stream"""
        if self.running:
            logger.warning(f"Stream {self.camera_id} already running")
            return
            
        self.running = True
        self.start_time = time.time()
        self.task = asyncio.create_task(self._stream_loop())
        logger.info(f"Stream {self.camera_id} started")
        
    async def stop(self):
        """Stop the stream"""
        if not self.running:
            return
            
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
        if self.capture:
            self.capture.release()
            self.capture = None
            
        logger.info(f"Stream {self.camera_id} stopped")
        
    async def _stream_loop(self):
        """Main stream processing loop"""
        reconnect_delay = 3  # Faster reconnection
        max_reconnect_delay = 30
        consecutive_failures = 0
        
        while self.running:
            try:
                await self._connect()
                await self._process_frames()
                
                # Reset delay on successful connection
                reconnect_delay = 3
                consecutive_failures = 0
                
            except Exception as e:
                self.error_count += 1
                consecutive_failures += 1
                
                logger.error(
                    f"Stream {self.camera_id} error (attempt {consecutive_failures}): {e}"
                )
                
                if self.capture:
                    self.capture.release()
                    self.capture = None
                    
                if self.running:
                    # Exponential backoff for reconnection
                    current_delay = min(reconnect_delay * consecutive_failures, max_reconnect_delay)
                    logger.info(
                        f"Reconnecting {self.camera_id} in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    
    async def _connect(self):
        """Connect to RTSP stream"""
        logger.info(f"Connecting to {self.camera_id}...")
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Create capture with better settings for reliability
        def create_capture():
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            
            # Configure for better stability
            # Higher buffer for high-res streams, lower for low-res
            buffer_size = 3 if '1920' in self.rtsp_url or 'high' in self.rtsp_url.lower() else 1
            cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            
            # Set RTSP transport to TCP for reliability with secure streams
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 30000)  # 30 second timeout
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 30000)
            
            return cap
        
        self.capture = await loop.run_in_executor(None, create_capture)
        
        if not self.capture.isOpened():
            raise ConnectionError(f"Failed to open stream: {self.rtsp_url}")
            
        # Get stream properties
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(
            f"Connected to {self.camera_id}: "
            f"{width}x{height} @ {fps}fps"
        )
        
    async def _process_frames(self):
        """Process frames from stream"""
        loop = asyncio.get_event_loop()
        frame_time_start = time.time()
        frames_processed = 0
        consecutive_failures = 0
        max_consecutive_failures = 30  # Allow 30 failed reads before reconnecting
        
        while self.running and self.capture and self.capture.isOpened():
            # Read frame in executor
            ret, frame = await loop.run_in_executor(
                None,
                self.capture.read
            )
            
            if not ret or frame is None:
                consecutive_failures += 1
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.warning(
                        f"Failed to read {consecutive_failures} frames from {self.camera_id}, reconnecting..."
                    )
                    break
                    
                # Small delay before retry
                await asyncio.sleep(0.1)
                continue
                
            # Reset failure counter on successful read
            consecutive_failures = 0
                
            self.frame_count += 1
            frames_processed += 1
            self.last_frame_time = datetime.now()
            
            # Store frame in buffer
            self.frame_buffer.put(frame)
            
            # Calculate FPS
            if frames_processed % 30 == 0:
                elapsed = time.time() - frame_time_start
                self.fps = frames_processed / elapsed
                frames_processed = 0
                frame_time_start = time.time()
                
            # Process frame through workflows
            if self.workflows:
                await self._process_frame(frame)
                
            # Small delay to prevent tight loop
            await asyncio.sleep(0.001)
            
    async def _process_frame(self, frame: np.ndarray):
        """Process frame through workflows"""
        try:
            for workflow_id in self.workflows:
                await self.workflow_engine.process_frame(
                    camera_id=self.camera_id,
                    workflow_id=workflow_id,
                    frame=frame,
                    timestamp=self.last_frame_time
                )
        except Exception as e:
            logger.error(
                f"Error processing frame for {self.camera_id}: {e}",
                exc_info=True
            )
            
    def get_status(self) -> dict:
        """Get stream status"""
        uptime = 0
        if self.start_time:
            uptime = int(time.time() - self.start_time)
            
        return {
            'running': self.running,
            'fps': round(self.fps, 2),
            'frame_count': self.frame_count,
            'uptime': uptime,
            'last_frame': self.last_frame_time.isoformat() if self.last_frame_time else None,
            'error_count': self.error_count,
            'workflows': self.workflows,
            'buffer_size': self.frame_buffer.size()
        }
        
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame from buffer"""
        return self.frame_buffer.get_latest()

