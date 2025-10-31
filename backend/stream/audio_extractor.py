"""
Audio Extractor
Extracts audio track from video streams using PyAV
"""
import asyncio
import logging
import time
from typing import Optional
from datetime import datetime

import av
import numpy as np
import librosa

from .audio_buffer import AudioBuffer


logger = logging.getLogger('overwatch.stream.audio')


class AudioExtractor:
    """Audio extraction from RTSP/video streams"""
    
    def __init__(
        self,
        rtsp_url: str,
        sample_rate: int = 16000,
        channels: int = 1,
        buffer_duration: float = 5.0
    ):
        """
        Initialize audio extractor
        
        Args:
            rtsp_url: RTSP stream URL
            sample_rate: Target sample rate in Hz
            channels: Number of audio channels (1=mono, 2=stereo)
            buffer_duration: Duration of audio buffer in seconds
        """
        self.rtsp_url = rtsp_url
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_duration = buffer_duration
        
        self.container = None
        self.running = False
        self.task = None
        
        # Audio buffer
        self.audio_buffer = AudioBuffer(max_duration_seconds=60.0)
        
        # Stats
        self.audio_fps = 0.0
        self.chunk_count = 0
        self.error_count = 0
        self.has_audio = False
        
    async def start(self):
        """Start audio extraction"""
        if self.running:
            logger.warning("Audio extractor already running")
            return
            
        self.running = True
        self.task = asyncio.create_task(self._extraction_loop())
        logger.info(f"Audio extraction started for {self.rtsp_url}")
        
    async def stop(self):
        """Stop audio extraction"""
        if not self.running:
            return
            
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
        if self.container:
            self.container.close()
            self.container = None
            
        logger.info("Audio extraction stopped")
        
    async def _extraction_loop(self):
        """Main audio extraction loop"""
        reconnect_delay = 3
        max_reconnect_delay = 30
        consecutive_failures = 0
        
        while self.running:
            try:
                await self._connect()
                await self._process_audio()
                
                # Reset delay on successful connection
                reconnect_delay = 3
                consecutive_failures = 0
                
            except Exception as e:
                self.error_count += 1
                consecutive_failures += 1
                
                logger.error(f"Audio extraction error (attempt {consecutive_failures}): {e}")
                
                if self.container:
                    self.container.close()
                    self.container = None
                    
                if self.running:
                    # Exponential backoff
                    current_delay = min(reconnect_delay * consecutive_failures, max_reconnect_delay)
                    logger.info(f"Reconnecting audio in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    
    async def _connect(self):
        """Connect to stream and open audio"""
        logger.info("Connecting to audio stream...")
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        self.container = await loop.run_in_executor(
            None,
            self._open_container
        )
        
        # Check if stream has audio
        audio_streams = [s for s in self.container.streams if s.type == 'audio']
        
        if not audio_streams:
            logger.warning(f"No audio track found in stream: {self.rtsp_url}")
            self.has_audio = False
            raise ValueError("No audio track in stream")
        
        self.has_audio = True
        audio_stream = audio_streams[0]
        
        logger.info(
            f"Connected to audio stream: "
            f"{audio_stream.codec.name} @ {audio_stream.codec_context.sample_rate}Hz, "
            f"{audio_stream.codec_context.channels} channels"
        )
        
    def _open_container(self):
        """Open PyAV container (blocking operation)"""
        # Open container with timeout
        container = av.open(
            self.rtsp_url,
            options={
                'rtsp_transport': 'tcp',
                'timeout': '30000000',  # 30 second timeout in microseconds
            }
        )
        return container
        
    async def _process_audio(self):
        """Process audio packets from stream"""
        loop = asyncio.get_event_loop()
        consecutive_failures = 0
        max_consecutive_failures = 30
        
        # Get audio stream
        audio_stream = [s for s in self.container.streams if s.type == 'audio'][0]
        
        chunk_start_time = time.time()
        chunks_processed = 0
        
        while self.running:
            try:
                # Decode audio packets in executor
                packet = await loop.run_in_executor(
                    None,
                    self._read_next_audio_packet,
                    audio_stream
                )
                
                if packet is None:
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning("Failed to read audio packets, reconnecting...")
                        break
                        
                    await asyncio.sleep(0.1)
                    continue
                
                # Reset failure counter
                consecutive_failures = 0
                
                # Process audio data
                await self._process_audio_packet(packet, audio_stream)
                
                self.chunk_count += 1
                chunks_processed += 1
                
                # Calculate audio FPS (chunks per second)
                if chunks_processed % 30 == 0:
                    elapsed = time.time() - chunk_start_time
                    self.audio_fps = chunks_processed / elapsed
                    chunks_processed = 0
                    chunk_start_time = time.time()
                
                # Small delay to prevent tight loop
                await asyncio.sleep(0.001)
                
            except StopIteration:
                logger.info("Audio stream ended")
                break
            except Exception as e:
                logger.error(f"Error processing audio packet: {e}")
                consecutive_failures += 1
                await asyncio.sleep(0.1)
                
    def _read_next_audio_packet(self, audio_stream):
        """Read next audio packet (blocking operation)"""
        try:
            # Demux packets
            for packet in self.container.demux(audio_stream):
                return packet
        except Exception:
            return None
        return None
        
    async def _process_audio_packet(self, packet, audio_stream):
        """Process decoded audio packet"""
        loop = asyncio.get_event_loop()
        
        # Decode packet in executor
        frames = await loop.run_in_executor(
            None,
            self._decode_packet,
            packet
        )
        
        if not frames:
            return
            
        # Convert audio to target format
        for frame in frames:
            audio_data = frame.to_ndarray()
            original_rate = frame.sample_rate
            
            # Resample if needed
            if original_rate != self.sample_rate:
                audio_data = librosa.resample(
                    audio_data.astype(np.float32),
                    orig_sr=original_rate,
                    target_sr=self.sample_rate
                )
            
            # Convert to mono/stereo
            if len(audio_data.shape) > 1:
                if self.channels == 1:
                    # Convert to mono by averaging channels
                    audio_data = np.mean(audio_data, axis=0)
                elif self.channels == 2 and audio_data.shape[0] == 1:
                    # Duplicate mono to stereo
                    audio_data = np.repeat(audio_data, 2, axis=0)
            
            # Store in buffer
            self.audio_buffer.put(
                audio_data,
                self.sample_rate,
                datetime.now()
            )
    
    def _decode_packet(self, packet):
        """Decode audio packet (blocking operation)"""
        try:
            return packet.decode()
        except Exception as e:
            logger.error(f"Failed to decode audio packet: {e}")
            return []
        
    def get_audio_chunk(self, duration: float) -> Optional[tuple[np.ndarray, int, datetime]]:
        """
        Get audio chunk of specified duration
        
        Args:
            duration: Duration in seconds
            
        Returns:
            Tuple of (audio_data, sample_rate, timestamp) or None
        """
        if not self.has_audio:
            return None
            
        return self.audio_buffer.get_chunk(duration)
        
    def get_status(self) -> dict:
        """Get audio extraction status"""
        return {
            'running': self.running,
            'has_audio': self.has_audio,
            'audio_fps': round(self.audio_fps, 2),
            'chunk_count': self.chunk_count,
            'error_count': self.error_count,
            'buffer_size': self.audio_buffer.size(),
            'sample_rate': self.sample_rate,
            'channels': self.channels
        }


