"""
Overwatch - AI-Powered Security Camera Monitoring System
Main application entry point
"""
import asyncio
import signal
import sys
from pathlib import Path

from core.config import settings
from core.logging import setup_logging
from core.hierarchy import HierarchyLoader
from api.server import create_app
from stream.manager import StreamManager
from workflows.engine import WorkflowEngine
from events.manager import EventManager
from federation.manager import FederationManager
from alarms.manager import AlarmManager
from rules.engine import RulesEngine
from integrations.notifications import ConsoleNotifier, EmailNotifier, SMSNotifier, PagerDutyNotifier
from integrations.devices import PTZController, SignageController, RadioTTSController, WebhookSender, RecordingController
from core.metrics import init_metrics


logger = setup_logging()


class Overwatch:
    """Main application class"""
    
    def __init__(self):
        self.stream_manager = None
        self.workflow_engine = None
        self.event_manager = None
        self.alarm_manager = None
        self.rules_engine = None
        self.federation_manager = None
        self.meshtastic_manager = None
        self.drone_event_manager = None
        self.drone_workflow_manager = None
        self.app = None
        self._shutdown = False
        
    async def startup(self):
        """Initialize all components"""
        logger.info("Starting Overwatch...")
        
        # Create data directories
        self._create_directories()
        
        # Free port before starting
        await self._free_port(settings.API_PORT)
        
        # Initialize database first
        from core.database import init_db
        init_db()
        logger.info("Database initialized")
        
        # Initialize metrics
        init_metrics(version='1.0.0', node_id='overwatch-main')
        logger.info("Metrics initialized")
        
        # Load organizational hierarchy
        hierarchy_loader = HierarchyLoader()
        await hierarchy_loader.load_hierarchy()
        
        # Initialize event bus for workflow execution
        from workflows.event_bus import init_event_bus
        await init_event_bus()
        logger.info("Workflow event bus initialized")
        
        # Initialize components
        self.event_manager = EventManager()
        await self.event_manager.initialize()
        
        self.alarm_manager = AlarmManager()
        await self.alarm_manager.initialize()
        
        # Initialize rules engine
        self.rules_engine = RulesEngine(alarm_manager=self.alarm_manager)
        await self.rules_engine.initialize()
        
        # Register notifiers
        self.rules_engine.register_notifier('console', ConsoleNotifier().send)
        self.rules_engine.register_notifier('email', EmailNotifier().send)
        self.rules_engine.register_notifier('sms', SMSNotifier().send)
        self.rules_engine.register_notifier('pagerduty', PagerDutyNotifier().send)
        
        # Register automation handlers
        self.rules_engine.register_automation('ptz.preset', PTZController().move_to_preset)
        self.rules_engine.register_automation('signage.push', SignageController().push_message)
        self.rules_engine.register_automation('radio.tts', RadioTTSController().send_tts)
        
        # Subscribe alarm manager to event updates
        async def on_event_created(event):
            await self.alarm_manager.process_event(event)
        self.event_manager.subscribe(on_event_created)
        
        # Subscribe rules engine to events
        async def on_event_for_rules(event):
            await self.rules_engine.evaluate_event(event)
        self.event_manager.subscribe(on_event_for_rules)
        
        # Subscribe to alarm updates for WebSocket broadcast
        async def on_alarm_updated(alarm, action):
            from api.websocket import broadcast_alarm
            await broadcast_alarm(alarm, action)
        self.alarm_manager.subscribe(on_alarm_updated)
        
        self.workflow_engine = WorkflowEngine(self.event_manager)
        await self.workflow_engine.load_workflows()
        
        self.stream_manager = StreamManager(self.workflow_engine)
        await self.stream_manager.load_cameras()
        
        # Set stream manager for realtime workflows
        from workflows.realtime_executor import set_stream_manager
        set_stream_manager(self.stream_manager)
        logger.info("Stream manager registered with realtime executor")
        
        # Initialize federation if enabled
        self.federation_manager = FederationManager()
        if settings.ENABLE_FEDERATION:
            await self.federation_manager.initialize()
        
        # Initialize drone detection system
        from integrations.meshtastic import MeshtasticManager
        from events.drone_manager import DroneEventManager
        from workflows.drone_workflow_manager import DroneWorkflowManager
        
        self.drone_event_manager = DroneEventManager()
        await self.drone_event_manager.initialize()
        
        # Start background track cleanup task
        asyncio.create_task(self.drone_event_manager.cleanup_inactive_tracks())
        
        # Initialize drone workflow manager
        self.drone_workflow_manager = DroneWorkflowManager(
            drone_event_manager=self.drone_event_manager,
            alarm_manager=self.alarm_manager
        )
        
        self.meshtastic_manager = MeshtasticManager()
        await self.meshtastic_manager.initialize()
        
        # Register drone detection callback to publish to WebSocket
        async def on_drone_detection(detection):
            enriched = await self.drone_event_manager.process_detection(detection)
            # Broadcast to WebSocket clients
            from api.websocket import broadcast_drone_detection
            await broadcast_drone_detection(enriched.to_event_dict())
        
        self.meshtastic_manager.register_callback(on_drone_detection)
        
        # Start Meshtastic receivers
        asyncio.create_task(self.meshtastic_manager.start())
        
        # Create FastAPI app
        self.app = create_app(
            stream_manager=self.stream_manager,
            workflow_engine=self.workflow_engine,
            event_manager=self.event_manager,
            federation_manager=self.federation_manager,
            alarm_manager=self.alarm_manager,
            rules_engine=self.rules_engine,
            drone_workflow_manager=self.drone_workflow_manager
        )
        
        # Set drone managers for API routes
        from api.routes.drone_components import set_managers
        set_managers(self.meshtastic_manager, self.drone_event_manager)
        
        logger.info("Overwatch started successfully")
        logger.info(f"API server: http://{settings.API_HOST}:{settings.API_PORT}")
        logger.info(f"Dashboard: http://localhost:{settings.DASHBOARD_PORT}")
        
    async def shutdown(self):
        """Gracefully shutdown all components"""
        if self._shutdown:
            return
            
        self._shutdown = True
        logger.info("Shutting down Overwatch...")
        
        if self.stream_manager:
            await self.stream_manager.stop_all()
            
        if self.workflow_engine:
            await self.workflow_engine.cleanup()
            
        if self.event_manager:
            await self.event_manager.cleanup()
            
        if self.alarm_manager:
            await self.alarm_manager.cleanup()
            
        if self.rules_engine:
            await self.rules_engine.cleanup()
            
        if self.federation_manager:
            await self.federation_manager.cleanup()
        
        if self.drone_workflow_manager:
            await self.drone_workflow_manager.cleanup()
        
        if self.meshtastic_manager:
            await self.meshtastic_manager.stop()
        
        # Shutdown event bus
        from workflows.event_bus import shutdown_event_bus
        await shutdown_event_bus()
            
        logger.info("Overwatch shutdown complete")
        
    def _create_directories(self):
        """Create required directories"""
        dirs = [
            settings.MODEL_CACHE_DIR,
            settings.SNAPSHOT_DIR,
            settings.RECORDING_DIR,
            settings.UPLOAD_DIR,
            Path(settings.LOG_FILE).parent,
        ]
        
        for directory in dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    async def _free_port(self, port: int):
        """Free the port if it's in use"""
        try:
            # Try to find and kill process using the port
            import subprocess
            result = subprocess.run(
                ['lsof', '-t', f'-i:{port}'],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                pid = result.stdout.strip()
                logger.warning(f"Port {port} is in use by PID {pid}, killing process...")
                subprocess.run(['kill', '-9', pid])
                await asyncio.sleep(1)
                logger.info(f"Port {port} freed")
        except Exception as e:
            logger.debug(f"Port check: {e}")
            

async def main():
    """Main entry point"""
    overwatch = Overwatch()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        asyncio.create_task(overwatch.shutdown())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await overwatch.startup()
        
        # Start uvicorn server
        import uvicorn
        config = uvicorn.Config(
            overwatch.app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await overwatch.shutdown()
        sys.exit(1)
        

if __name__ == "__main__":
    asyncio.run(main())

