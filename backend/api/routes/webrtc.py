"""
WebRTC API Routes
Handles WebRTC signaling for X-RAY View streaming
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

from stream.webrtc_streamer import get_webrtc_streamer


logger = logging.getLogger('overwatch.api.webrtc')
router = APIRouter()


class WebRTCOffer(BaseModel):
    """WebRTC offer from client"""
    node_id: str
    sdp: str
    type: str


class WebRTCAnswer(BaseModel):
    """WebRTC answer to client"""
    sdp: str
    type: str


@router.post("/offer")
async def handle_webrtc_offer(offer: WebRTCOffer) -> WebRTCAnswer:
    """
    Handle WebRTC offer from X-RAY View client
    Returns SDP answer to establish connection
    """
    logger.info(f"📡 Received WebRTC offer from node {offer.node_id}")
    
    try:
        streamer = get_webrtc_streamer()
        
        # Create answer
        answer_sdp = await streamer.create_offer(
            node_id=offer.node_id,
            offer_sdp={"sdp": offer.sdp, "type": offer.type}
        )
        
        logger.info(f"✅ Created WebRTC answer for {offer.node_id}")
        
        return WebRTCAnswer(
            sdp=answer_sdp["sdp"],
            type=answer_sdp["type"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error handling WebRTC offer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close/{node_id}")
async def close_webrtc_connection(node_id: str):
    """Close WebRTC connection for a specific node"""
    logger.info(f"Closing WebRTC connection for {node_id}")
    
    try:
        streamer = get_webrtc_streamer()
        await streamer.close_connection(node_id)
        
        return {"message": f"WebRTC connection closed for {node_id}"}
        
    except Exception as e:
        logger.error(f"Error closing WebRTC connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_webrtc_stats():
    """Get WebRTC streaming statistics"""
    streamer = get_webrtc_streamer()
    return streamer.get_stats()


@router.post("/cleanup")
async def cleanup_webrtc():
    """Close all WebRTC connections"""
    logger.info("Cleaning up all WebRTC connections")
    
    try:
        streamer = get_webrtc_streamer()
        await streamer.close_all()
        
        return {"message": "All WebRTC connections closed"}
        
    except Exception as e:
        logger.error(f"Error cleaning up WebRTC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

