"""
UniFi Credential Manager
Manages UniFi credentials and provides client instances
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from core.database import UniFiCredential
from .client import UniFiClient
from .protect_client import UniFiProtectClient

logger = logging.getLogger('overwatch.integrations.unifi.manager')


class UniFiCredentialManager:
    """Manages UniFi credentials and client creation"""
    
    def __init__(self, db: Session):
        """
        Initialize credential manager
        
        Args:
            db: Database session
        """
        self.db = db
        self._client_cache: Dict[str, UniFiClient] = {}
        self._protect_cache: Dict[str, UniFiProtectClient] = {}
        
    def get_credentials(
        self,
        organization_id: Optional[str] = None,
        site_id: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[UniFiCredential]:
        """
        Get UniFi credentials
        
        Args:
            organization_id: Filter by organization
            site_id: Filter by site
            enabled_only: Only return enabled credentials
            
        Returns:
            List of credentials
        """
        query = self.db.query(UniFiCredential)
        
        if organization_id:
            query = query.filter(UniFiCredential.organization_id == organization_id)
        if site_id:
            query = query.filter(UniFiCredential.site_id == site_id)
        if enabled_only:
            query = query.filter(UniFiCredential.enabled == 1)
            
        return query.all()
        
    def get_credential(self, credential_id: str) -> Optional[UniFiCredential]:
        """Get specific credential by ID"""
        return self.db.query(UniFiCredential).filter(
            UniFiCredential.id == credential_id
        ).first()
        
    def get_client(self, credential_id: str) -> Optional[UniFiClient]:
        """
        Get UniFi controller client
        
        Args:
            credential_id: Credential ID
            
        Returns:
            UniFiClient instance or None
        """
        # Check cache
        if credential_id in self._client_cache:
            return self._client_cache[credential_id]
            
        # Load credential
        cred = self.get_credential(credential_id)
        if not cred or not cred.enabled:
            return None
            
        if cred.credential_type != 'local':
            logger.warning(f"Credential {credential_id} is not a local controller")
            return None
            
        # Create client
        try:
            client = UniFiClient(
                host=cred.host,
                username=cred.username,
                password=cred.password,
                port=cred.port,
                site=cred.unifi_site,
                verify_ssl=bool(cred.verify_ssl)
            )
            
            # Cache it
            self._client_cache[credential_id] = client
            return client
            
        except Exception as e:
            logger.error(f"Failed to create UniFi client for {credential_id}: {e}")
            return None
            
    def get_protect_client(self, credential_id: str) -> Optional[UniFiProtectClient]:
        """
        Get UniFi Protect client
        
        Args:
            credential_id: Credential ID
            
        Returns:
            UniFiProtectClient instance or None
        """
        # Check cache
        if credential_id in self._protect_cache:
            return self._protect_cache[credential_id]
            
        # Load credential
        cred = self.get_credential(credential_id)
        if not cred or not cred.enabled:
            return None
            
        # Create client
        try:
            client = UniFiProtectClient(
                host=cred.host,
                username=cred.username,
                password=cred.password,
                port=cred.port,
                verify_ssl=bool(cred.verify_ssl)
            )
            
            # Cache it
            self._protect_cache[credential_id] = client
            return client
            
        except Exception as e:
            logger.error(f"Failed to create UniFi Protect client for {credential_id}: {e}")
            return None
            
    def clear_cache(self, credential_id: Optional[str] = None):
        """
        Clear client cache
        
        Args:
            credential_id: Specific credential to clear, or None for all
        """
        if credential_id:
            self._client_cache.pop(credential_id, None)
            self._protect_cache.pop(credential_id, None)
        else:
            self._client_cache.clear()
            self._protect_cache.clear()
            
    async def test_credential(self, credential_id: str) -> Dict:
        """
        Test a credential
        
        Args:
            credential_id: Credential to test
            
        Returns:
            Test result dict
        """
        cred = self.get_credential(credential_id)
        if not cred:
            return {
                "success": False,
                "error": "Credential not found"
            }
            
        try:
            # Test based on type
            if cred.credential_type == 'local':
                # Try Protect first, fall back to controller
                protect_client = self.get_protect_client(credential_id)
                if protect_client:
                    result = await protect_client.test_connection()
                    if result.get('success'):
                        result['type'] = 'protect'
                        return result
                        
                # Try regular controller
                client = self.get_client(credential_id)
                if client:
                    result = await client.test_connection()
                    result['type'] = 'controller'
                    return result
                    
            return {
                "success": False,
                "error": "Unknown credential type"
            }
            
        except Exception as e:
            logger.error(f"Error testing credential {credential_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

