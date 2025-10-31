"""
Base network provider interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict


class NetworkProvider(ABC):
    """Abstract interface for overlay network providers"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the network provider
        Returns True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def ensure_network(self) -> bool:
        """
        Ensure network exists (create if needed for central nodes)
        Returns True if network is ready, False otherwise
        """
        pass
    
    @abstractmethod
    async def join_network(self) -> bool:
        """
        Join the overlay network
        Returns True if joined successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def authorize_member(self, member_id: str, member_name: str = "") -> bool:
        """
        Authorize a member to join the network
        Returns True if authorized, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_members(self) -> List[Dict]:
        """
        List all network members
        Returns list of member dictionaries
        """
        pass
    
    @abstractmethod
    async def get_member_ip(self, member_id: str) -> Optional[str]:
        """
        Get assigned IP address for a member
        Returns IP address or None if not found
        """
        pass
    
    @abstractmethod
    async def status(self) -> Dict:
        """
        Get current provider status
        Returns dictionary with status information including:
        - online: bool
        - node_id: str
        - network_id: str
        - assigned_addresses: list
        - peer_count: int
        - member_count: int (central only)
        - local_api_available: bool
        - last_error: str (if any)
        """
        pass
    
    @abstractmethod
    def prefer_overlay_url(self, original_url: str) -> str:
        """
        Convert a URL to prefer overlay network if available
        Args:
            original_url: Original HTTP URL (e.g., http://public-ip:8000)
        Returns:
            Overlay URL if available (e.g., http://10.147.0.1:8000),
            otherwise returns original URL
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup provider resources"""
        pass


class NoOpProvider(NetworkProvider):
    """No-op provider when overlay networking is disabled"""
    
    async def initialize(self) -> bool:
        return True
    
    async def ensure_network(self) -> bool:
        return True
    
    async def join_network(self) -> bool:
        return True
    
    async def authorize_member(self, member_id: str, member_name: str = "") -> bool:
        return True
    
    async def list_members(self) -> List[Dict]:
        return []
    
    async def get_member_ip(self, member_id: str) -> Optional[str]:
        return None
    
    async def status(self) -> Dict:
        return {
            "online": False,
            "enabled": False,
            "provider": "none"
        }
    
    def prefer_overlay_url(self, original_url: str) -> str:
        return original_url
    
    async def cleanup(self):
        pass


