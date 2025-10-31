"""
Notification Integrations
Email, SMS, PagerDuty, etc.
"""
import logging
import asyncio
from typing import Dict, Any, Optional


logger = logging.getLogger('overwatch.integrations.notifications')


class ConsoleNotifier:
    """Console notification (for testing/logging)"""
    
    async def send(self, message: str, target: Optional[str], event: Dict[str, Any]):
        """Send console notification"""
        logger.info(f"NOTIFICATION: {message}")
        logger.info(f"Target: {target}, Event: {event['id']}")
        

class EmailNotifier:
    """Email notification via SMTP"""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = 587, username: str = None, password: str = None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        
    async def send(self, message: str, target: str, event: Dict[str, Any]):
        """Send email notification"""
        if not self.smtp_host:
            logger.warning("Email notifier not configured, skipping")
            return
            
        try:
            import aiosmtplib
            from email.message import EmailMessage
            
            msg = EmailMessage()
            msg['Subject'] = 'Overwatch Alert'
            msg['From'] = self.username
            msg['To'] = target
            msg.set_content(message)
            
            # Add snapshot if available
            snapshot_url = event.get('media', {}).get('snapshot_url')
            if snapshot_url:
                msg.add_alternative(f"""
                <html>
                  <body>
                    <p>{message}</p>
                    <img src="{snapshot_url}" alt="Snapshot">
                  </body>
                </html>
                """, subtype='html')
            
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True
            )
            
            logger.info(f"Email sent to {target}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            

class SMSNotifier:
    """SMS notification via Twilio"""
    
    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        
    async def send(self, message: str, target: str, event: Dict[str, Any]):
        """Send SMS notification"""
        if not self.account_sid:
            logger.warning("SMS notifier not configured, skipping")
            return
            
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            await asyncio.to_thread(
                client.messages.create,
                body=message[:160],  # SMS limit
                from_=self.from_number,
                to=target
            )
            
            logger.info(f"SMS sent to {target}")
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            

class PagerDutyNotifier:
    """PagerDuty incident creation"""
    
    def __init__(self, integration_key: str = None):
        self.integration_key = integration_key
        
    async def send(self, message: str, target: Optional[str], event: Dict[str, Any]):
        """Create PagerDuty incident"""
        if not self.integration_key:
            logger.warning("PagerDuty notifier not configured, skipping")
            return
            
        try:
            import httpx
            
            payload = {
                "routing_key": self.integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": message,
                    "severity": event.get('severity', 'warning'),
                    "source": event.get('source', {}).get('device_id', 'overwatch'),
                    "custom_details": {
                        "event_id": event['id'],
                        "site": event.get('site'),
                        "location": event.get('location', {}).get('area_id')
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload
                )
                response.raise_for_status()
                
            logger.info(f"PagerDuty incident created")
            
        except Exception as e:
            logger.error(f"Failed to create PagerDuty incident: {e}")


