"""
WebRTC Streamer for X-RAY View
Hardware-accelerated H.264 streaming with ultra-low latency
"""
import asyncio
import logging
import json
import cv2
import numpy as np
from typing import Optional, Dict
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from av import VideoFrame
import fractions

logger = logging.getLogger('overwatch.webrtc')


class XRayVideoTrack(VideoStreamTrack):
    """
    Custom video track that streams X-RAY annotated frames
    Uses H.264 encoding for efficient real-time streaming
    """
    
    def __init__(self, node_id: str):
        super().__init__()
        self.node_id = node_id
        self.current_frame = None
        self.frame_count = 0
        self._timestamp = 0
        self._start = None
        
    def set_frame(self, frame: np.ndarray):
        """Update the current frame to stream"""
        self.current_frame = frame
        
    async def recv(self):
        """
        Receive next video frame for WebRTC
        Called by WebRTC at ~30-60 FPS
        """
        pts, time_base = await self.next_timestamp()
        
        # If no frame available, return black frame
        if self.current_frame is None:
            # Create black frame placeholder
            frame_array = np.zeros((540, 960, 3), dtype=np.uint8)
        else:
            frame_array = self.current_frame
            
        # Convert to VideoFrame for WebRTC
        frame = VideoFrame.from_ndarray(frame_array, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base
        
        self.frame_count += 1
        return frame


class WebRTCStreamer:
    """
    Manages WebRTC connections for X-RAY streaming
    Provides hardware-accelerated H.264 streaming
    """
    
    def __init__(self):
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.video_tracks: Dict[str, XRayVideoTrack] = {}
        self.relay = MediaRelay()
        
    async def create_offer(self, node_id: str, offer_sdp: dict) -> dict:
        """
        Handle WebRTC offer from client
        
        Args:
            node_id: X-RAY View node ID
            offer_sdp: Client's SDP offer
            
        Returns:
            Answer SDP
        """
        logger.info(f"📡 Creating WebRTC connection for node {node_id}")
        
        # Create peer connection
        pc = RTCPeerConnection()
        self.peer_connections[node_id] = pc
        
        # Create video track for this node
        video_track = XRayVideoTrack(node_id)
        self.video_tracks[node_id] = video_track
        
        # Add track to peer connection
        pc.addTrack(video_track)
        
        # Handle ICE connection state changes
        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            logger.info(f"WebRTC ICE state for {node_id}: {pc.iceConnectionState}")
            if pc.iceConnectionState == "failed":
                await self.close_connection(node_id)
                
        # Handle connection state changes
        @pc.on("connectionstatechange")
        async def on_connection_state_change():
            logger.info(f"WebRTC connection state for {node_id}: {pc.connectionState}")
            
        # Set remote description (client's offer)
        offer = RTCSessionDescription(sdp=offer_sdp["sdp"], type=offer_sdp["type"])
        await pc.setRemoteDescription(offer)
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        logger.info(f"✅ WebRTC connection established for {node_id}")
        
        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }
        
    async def update_frame(self, node_id: str, frame: np.ndarray):
        """
        Update frame for a specific X-RAY View node
        
        Args:
            node_id: X-RAY View node ID
            frame: Annotated frame (BGR format)
        """
        if node_id in self.video_tracks:
            # Ensure frame is correct format
            if len(frame.shape) == 2:
                # Grayscale, convert to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                # RGBA, convert to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                
            self.video_tracks[node_id].set_frame(frame)
            logger.debug(f"Updated WebRTC frame for {node_id}: {frame.shape}")
        else:
            logger.warning(f"No WebRTC track found for node {node_id}")
            
    async def close_connection(self, node_id: str):
        """Close WebRTC connection for a node"""
        if node_id in self.peer_connections:
            pc = self.peer_connections[node_id]
            await pc.close()
            del self.peer_connections[node_id]
            logger.info(f"Closed WebRTC connection for {node_id}")
            
        if node_id in self.video_tracks:
            del self.video_tracks[node_id]
            
    async def close_all(self):
        """Close all WebRTC connections"""
        for node_id in list(self.peer_connections.keys()):
            await self.close_connection(node_id)
            
    def get_stats(self) -> dict:
        """Get WebRTC statistics"""
        return {
            "active_connections": len(self.peer_connections),
            "active_tracks": len(self.video_tracks),
            "connection_ids": list(self.peer_connections.keys())
        }


# Global WebRTC streamer instance
_webrtc_streamer = None


def get_webrtc_streamer() -> WebRTCStreamer:
    """Get global WebRTC streamer instance"""
    global _webrtc_streamer
    if _webrtc_streamer is None:
        _webrtc_streamer = WebRTCStreamer()
    return _webrtc_streamer

