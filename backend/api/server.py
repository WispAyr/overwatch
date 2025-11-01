"""
FastAPI Server
Main API server with routes
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from core.config import settings
from .routes import cameras, streams, workflows, events, system, organizations, sites, sublocations, hierarchy, federation, zerotier, snapshots, video, camera_control, workflow_builder, workflow_components, component_status, system_installer, config, alarms, rules, drone_components, unifi, uploads, device, webrtc
from .websocket import websocket_router
# from . import huggingface


logger = logging.getLogger('overwatch.api')


def create_app(stream_manager, workflow_engine, event_manager, federation_manager, alarm_manager, rules_engine, drone_workflow_manager=None, device_manager=None, discovery_service=None, sync_service=None) -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Overwatch API",
        description="AI-Powered Security Camera Monitoring System",
        version="1.0.0",
    )
    
    # CORS middleware - configure allowed origins for workflow builder
    allowed_origins = [
        "http://localhost:7003",  # Workflow builder dev
        "http://localhost:7002",  # Dashboard (main)
        "http://localhost:7001",  # Dashboard (alt)
        "http://localhost:3000",  # Frontend dev
    ]
    
    # Add configured origins from settings
    if hasattr(settings, 'CORS_ORIGINS') and settings.CORS_ORIGINS:
        if isinstance(settings.CORS_ORIGINS, str):
            allowed_origins.extend(settings.CORS_ORIGINS.split(','))
        else:
            allowed_origins.extend(settings.CORS_ORIGINS)
    
    # Allow all origins for Raspberry Pi network access
    allowed_origins = ["*"]  # Override for development
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store managers in app state
    app.state.stream_manager = stream_manager
    app.state.workflow_engine = workflow_engine
    app.state.event_manager = event_manager
    app.state.federation_manager = federation_manager
    app.state.alarm_manager = alarm_manager
    app.state.rules_engine = rules_engine
    app.state.drone_workflow_manager = drone_workflow_manager
    app.state.device_manager = device_manager
    app.state.discovery_service = discovery_service
    app.state.sync_service = sync_service
    
    # Include routers
    app.include_router(device.router, prefix="/api/device", tags=["device"])
    app.include_router(federation.router, prefix="/api/federation", tags=["federation"])
    app.include_router(zerotier.router, prefix="/api/zerotier", tags=["zerotier"])
    app.include_router(hierarchy.router, prefix="/api/hierarchy", tags=["hierarchy"])
    app.include_router(organizations.router, prefix="/api/organizations", tags=["organizations"])
    app.include_router(sites.router, prefix="/api/sites", tags=["sites"])
    app.include_router(sublocations.router, prefix="/api/sublocations", tags=["sublocations"])
    app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
    app.include_router(camera_control.router, prefix="/api/camera-control", tags=["camera-control"])
    app.include_router(streams.router, prefix="/api/streams", tags=["streams"])
    app.include_router(video.router, prefix="/api/video", tags=["video"])
    app.include_router(webrtc.router, prefix="/api/webrtc", tags=["webrtc"])
    app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(workflow_builder.router, prefix="/api/workflow-builder", tags=["workflow-builder"])
    app.include_router(workflow_components.router, prefix="/api/workflow-components", tags=["workflow-components"])
    app.include_router(component_status.router, prefix="/api/component-status", tags=["component-status"])
    app.include_router(system_installer.router, prefix="/api/system", tags=["system-installer"])
    app.include_router(config.router, prefix="/api/config", tags=["config"])
    app.include_router(events.router, prefix="/api/events", tags=["events"])
    app.include_router(alarms.router)
    app.include_router(rules.router)
    app.include_router(snapshots.router, prefix="/api/snapshots", tags=["snapshots"])
    app.include_router(drone_components.router, prefix="/api/drone-components", tags=["drone"])
    app.include_router(system.router, prefix="/api/system", tags=["system"])
    app.include_router(unifi.router, prefix="/api/unifi", tags=["unifi"])
    app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
    #     app.include_router(huggingface.router, tags=["huggingface"])  # HuggingFace AI Model Manager
    app.include_router(websocket_router, prefix="/api/ws", tags=["websocket"])
    
    # Serve uploaded files as static files
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")
    
    # Serve frontend static files
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    
    @app.on_event("startup")
    async def startup_event():
        """Startup tasks"""
        logger.info("API server starting...")
        from core.database import init_db
        init_db()
        
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown tasks"""
        logger.info("API server shutting down...")
        
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}
        
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
        
    return app

