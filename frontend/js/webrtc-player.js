/**
 * WebRTC Player for MediaMTX streams
 * Handles WebRTC video playback from MediaMTX server
 */

class WebRTCPlayer {
    constructor(videoElement, streamName) {
        this.videoElement = videoElement;
        this.streamName = streamName;
        this.pc = null;
        this.restartTimeout = null;
        this.ws = null;
    }
    
    async start() {
        console.log(`Starting WebRTC player for ${this.streamName}`);
        
        try {
            // Create RTCPeerConnection
            this.pc = new RTCPeerConnection({
                iceServers: [{
                    urls: 'stun:stun.l.google.com:19302'
                }]
            });
            
            // Handle incoming tracks
            this.pc.ontrack = (event) => {
                console.log('Received video track');
                this.videoElement.srcObject = event.streams[0];
            };
            
            // Handle connection state changes
            this.pc.onconnectionstatechange = () => {
                console.log('Connection state:', this.pc.connectionState);
                
                if (this.pc.connectionState === 'failed' || 
                    this.pc.connectionState === 'disconnected') {
                    this.scheduleRestart();
                }
            };
            
            // Add transceiver for receiving video
            this.pc.addTransceiver('video', { direction: 'recvonly' });
            this.pc.addTransceiver('audio', { direction: 'recvonly' });
            
            // Create offer
            const offer = await this.pc.createOffer();
            await this.pc.setLocalDescription(offer);
            
            // Wait for ICE gathering to complete
            await this.waitForIceGathering();
            
            // Send offer to MediaMTX WHEP endpoint
            const response = await fetch(`http://localhost:8889/${this.streamName}/whep`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/sdp'
                },
                body: this.pc.localDescription.sdp
            });
            
            if (!response.ok) {
                throw new Error(`WHEP request failed: ${response.status}`);
            }
            
            // Set remote description from answer
            const answer = await response.text();
            await this.pc.setRemoteDescription(new RTCSessionDescription({
                type: 'answer',
                sdp: answer
            }));
            
            console.log('WebRTC connection established');
            
        } catch (error) {
            console.error('WebRTC error:', error);
            this.scheduleRestart();
        }
    }
    
    waitForIceGathering() {
        return new Promise((resolve) => {
            if (this.pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (this.pc.iceGatheringState === 'complete') {
                        this.pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                this.pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }
    
    scheduleRestart() {
        if (this.restartTimeout !== null) {
            return;
        }
        
        this.restartTimeout = setTimeout(() => {
            this.restartTimeout = null;
            this.stop();
            this.start();
        }, 2000);
    }
    
    stop() {
        if (this.pc) {
            this.pc.close();
            this.pc = null;
        }
        
        if (this.restartTimeout !== null) {
            clearTimeout(this.restartTimeout);
            this.restartTimeout = null;
        }
    }
}

// Export for use in main app
window.WebRTCPlayer = WebRTCPlayer;


