"""
Device Configuration Model
Stores device-specific configuration and settings
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import platform
import os


class DeviceInfo(BaseModel):
    """Device information"""
    device_id: str
    device_name: str
    device_type: str = Field(default="server")  # server, raspberry-pi, edge
    hostname: str
    platform: str
    architecture: str
    python_version: str
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    version: str = "1.0.0"
    

class DeviceSettings(BaseModel):
    """Device-specific settings"""
    # Startup
    autostart_enabled: bool = False
    autostart_delay: int = 10  # seconds
    
    # Updates
    auto_update_enabled: bool = False
    update_channel: str = "stable"  # stable, beta, main
    update_check_interval: int = 3600  # seconds
    last_update_check: Optional[datetime] = None
    
    # Performance
    max_cpu_percent: int = 80
    max_memory_percent: int = 80
    enable_gpu: bool = True
    
    # Federation
    enable_discovery: bool = True
    discovery_interval: int = 60  # seconds
    auto_sync_enabled: bool = True
    sync_workflows: bool = True
    sync_cameras: bool = True
    sync_rules: bool = True
    
    # Storage
    max_recording_days: int = 7
    max_snapshot_days: int = 30
    auto_cleanup_enabled: bool = True
    
    # Network
    webrtc_enabled: bool = True
    webrtc_port_range_start: int = 50000
    webrtc_port_range_end: int = 50100
    
    # Device-specific
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class DeviceConfig:
    """Manages device configuration"""
    
    def __init__(self, config_path: str = "./config/device.json"):
        self.config_path = Path(config_path)
        self.info: Optional[DeviceInfo] = None
        self.settings: Optional[DeviceSettings] = None
        self._load()
    
    def _load(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.info = DeviceInfo(**data.get('info', {}))
                    self.settings = DeviceSettings(**data.get('settings', {}))
            except Exception as e:
                print(f"Error loading device config: {e}")
                self._create_default()
        else:
            self._create_default()
    
    def _create_default(self):
        """Create default configuration"""
        import socket
        import sys
        
        # Detect device type from environment or platform
        device_type = os.getenv('DEVICE_TYPE', 'server')
        if 'raspberry' in platform.platform().lower() or 'arm' in platform.machine().lower():
            device_type = 'raspberry-pi'
        
        self.info = DeviceInfo(
            device_id=os.getenv('NODE_ID', f"overwatch-{socket.gethostname()}"),
            device_name=socket.gethostname(),
            device_type=device_type,
            hostname=socket.gethostname(),
            platform=platform.platform(),
            architecture=platform.machine(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        
        self.settings = DeviceSettings()
        self.save()
    
    def save(self):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'info': self.info.dict() if self.info else {},
            'settings': self.settings.dict() if self.settings else {},
            'updated_at': datetime.utcnow().isoformat()
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def update_settings(self, settings_update: Dict[str, Any]):
        """Update settings"""
        if not self.settings:
            self.settings = DeviceSettings()
        
        for key, value in settings_update.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        
        self.save()
    
    def get_branch_for_device(self) -> str:
        """Get the appropriate git branch for this device type"""
        if not self.info:
            return "main"
        
        branch_mapping = {
            "raspberry-pi": "ras-pi",
            "server": "main",
            "edge": "main"
        }
        
        return branch_mapping.get(self.info.device_type, "main")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'info': self.info.dict() if self.info else {},
            'settings': self.settings.dict() if self.settings else {}
        }

