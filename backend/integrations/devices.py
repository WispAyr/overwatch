"""
Device Automation Integrations
PTZ cameras, signage, radios, etc.
"""
import logging
import asyncio
import httpx
from typing import Dict, Any


logger = logging.getLogger('overwatch.integrations.devices')


class PTZController:
    """PTZ camera preset control"""
    
    async def move_to_preset(self, params: Dict[str, Any], event: Dict[str, Any]):
        """Move PTZ camera to preset"""
        camera_id = params.get('camera')
        preset = params.get('preset')
        
        if not camera_id or not preset:
            logger.warning("PTZ preset action missing camera or preset")
            return
            
        logger.info(f"Moving camera {camera_id} to preset {preset}")
        
        # TODO: Implement ONVIF PTZ control
        # This would integrate with the camera control system
        # For now, just log the action
        

class SignageController:
    """Digital signage control"""
    
    def __init__(self, allow_list: list = None):
        """Initialize with allowed signage endpoints"""
        self.allow_list = allow_list or []
        
    async def push_message(self, params: Dict[str, Any], event: Dict[str, Any]):
        """Push message to digital signage"""
        message = params.get('message') if isinstance(params, dict) else str(params)
        endpoint = params.get('endpoint') if isinstance(params, dict) else None
        
        if endpoint and endpoint not in self.allow_list:
            logger.warning(f"Signage endpoint {endpoint} not in allow list")
            return
            
        logger.info(f"Pushing message to signage: {message}")
        
        # Example: POST to PiSignage or similar
        # This is a stub implementation
        

class RadioTTSController:
    """Radio PTT/TTS integration"""
    
    async def send_tts(self, params: Dict[str, Any], event: Dict[str, Any]):
        """Send TTS to radio channel"""
        message = params.get('message') if isinstance(params, dict) else str(params)
        channel = params.get('channel')
        
        logger.info(f"Sending TTS to radio channel {channel}: {message}")
        
        # TODO: Integrate with radio gateway (e.g., Zello API, TAK, etc.)
        

class WebhookSender:
    """Generic webhook sender with retries"""
    
    def __init__(self, allow_list: list = None):
        """Initialize with allowed webhook URLs"""
        self.allow_list = allow_list or []
        
    async def send_webhook(self, params: Dict[str, Any], event: Dict[str, Any]):
        """Send webhook with retry and exponential backoff"""
        url = params.get('url')
        method = params.get('method', 'POST').upper()
        
        if url and self.allow_list and url not in self.allow_list:
            logger.warning(f"Webhook URL {url} not in allow list")
            return
            
        payload = {
            'event': event,
            'timestamp': event.get('observed'),
            'params': params.get('data', {})
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    if method == 'POST':
                        response = await client.post(url, json=payload)
                    elif method == 'PUT':
                        response = await client.put(url, json=payload)
                    else:
                        response = await client.request(method, url, json=payload)
                        
                    response.raise_for_status()
                    
                    logger.info(f"Webhook sent to {url}: {response.status_code}")
                    
                    # Store response metadata in event
                    event.setdefault('webhook_responses', []).append({
                        'url': url,
                        'status': response.status_code,
                        'body': response.text[:500]  # Truncate
                    })
                    
                    return
                    
            except Exception as e:
                logger.warning(f"Webhook attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Webhook failed after {max_retries} attempts")
                    

class RecordingController:
    """Control video recording"""
    
    def __init__(self, stream_manager=None):
        self.stream_manager = stream_manager
        
    async def record_clip(self, params: Dict[str, Any], event: Dict[str, Any]):
        """Record a clip around the event"""
        camera_id = event.get('camera_id')
        duration = params.get('duration', 30)  # seconds
        pre_buffer = params.get('pre_buffer', 5)  # seconds before event
        
        if not self.stream_manager:
            logger.warning("Stream manager not available for recording")
            return
            
        logger.info(f"Recording {duration}s clip from {camera_id}")
        
        # TODO: Implement actual recording using StreamManager buffers
        # This would extract frames from the ring buffer and encode to video


