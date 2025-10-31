"""
API Routes for Drone Detection Components
Provides endpoints for workflow builder to query receivers, geofences, and active drones
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

router = APIRouter()

# Global references (set by main.py during startup)
meshtastic_manager = None
drone_event_manager = None


# Pydantic models for request/response validation
class GeofenceCreate(BaseModel):
    """Request model for creating geofences"""
    id: str = Field(..., description="Unique geofence identifier")
    name: str = Field(..., description="Human-readable name")
    polygon: List[List[float]] = Field(..., description="Array of [lat, lon] coordinates")
    altitude_min: float = Field(0, ge=0, le=10000, description="Minimum altitude in meters")
    altitude_max: float = Field(10000, ge=0, le=10000, description="Maximum altitude in meters")
    restriction_type: str = Field(..., description="Type: no-fly, restricted, warning, monitoring")
    enforcement_level: str = Field(..., description="Level: log_only, warning, critical_alarm")
    active_hours: Optional[List[str]] = Field(None, description="Active hours like ['8-17']")
    temporary_start: Optional[str] = Field(None, description="ISO timestamp for temporary start")
    temporary_end: Optional[str] = Field(None, description="ISO timestamp for temporary end")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "airport_approach_1",
                "name": "Airport Approach Path - Runway 27",
                "polygon": [
                    [37.621311, -122.378955],
                    [37.615966, -122.357693],
                    [37.605966, -122.357693],
                    [37.611311, -122.378955]
                ],
                "altitude_min": 0,
                "altitude_max": 500,
                "restriction_type": "no-fly",
                "enforcement_level": "critical_alarm"
            }
        }


class ReceiverStatus(BaseModel):
    """Meshtastic receiver status"""
    id: str
    name: str
    port: str
    connected: bool
    enabled: bool
    location: Optional[Dict]
    stats: Dict


class ActiveDrone(BaseModel):
    """Currently tracked drone"""
    remote_id: str
    first_seen: str
    last_seen: str
    total_detections: int
    geofence_violations: List[str]
    current_position: Optional[Dict]
    flight_path_length: int


# Dependency to get managers
def get_meshtastic_manager():
    if meshtastic_manager is None:
        raise HTTPException(status_code=503, detail="Meshtastic manager not initialized")
    return meshtastic_manager


def get_drone_event_manager():
    if drone_event_manager is None:
        raise HTTPException(status_code=503, detail="Drone event manager not initialized")
    return drone_event_manager


@router.get("/receivers", response_model=List[ReceiverStatus])
async def get_receivers(manager=Depends(get_meshtastic_manager)):
    """
    List all configured Meshtastic receivers with connection status
    Used by DroneInputNode to populate receiver selection dropdown
    """
    try:
        receivers = manager.get_device_status()
        return receivers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching receivers: {str(e)}")


@router.get("/geofences")
async def get_geofences(manager=Depends(get_drone_event_manager)):
    """
    Retrieve all defined geofence zones
    Used by DroneFilterNode and DroneMapNode
    """
    try:
        geofences = manager.get_geofences()
        return {
            "geofences": geofences,
            "total": len(geofences)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching geofences: {str(e)}")


@router.post("/geofences")
async def create_geofence(
    geofence: GeofenceCreate,
    manager=Depends(get_drone_event_manager)
):
    """
    Create or update a geofence polygon
    Validates coordinates and altitude ranges
    """
    try:
        # Validate polygon coordinates
        if len(geofence.polygon) < 3:
            raise HTTPException(
                status_code=400,
                detail="Polygon must have at least 3 coordinates"
            )
        
        for coord in geofence.polygon:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]"
                )
            lat, lon = coord
            if not (-90 <= lat <= 90):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid latitude: {lat}"
                )
            if not (-180 <= lon <= 180):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid longitude: {lon}"
                )
        
        # Validate altitude range
        if geofence.altitude_min >= geofence.altitude_max:
            raise HTTPException(
                status_code=400,
                detail="altitude_min must be less than altitude_max"
            )
        
        # Validate restriction type
        valid_types = ['no-fly', 'restricted', 'warning', 'monitoring']
        if geofence.restriction_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"restriction_type must be one of: {valid_types}"
            )
        
        # Validate enforcement level
        valid_levels = ['log_only', 'warning', 'critical_alarm']
        if geofence.enforcement_level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"enforcement_level must be one of: {valid_levels}"
            )
        
        # Create geofence
        created = manager.add_geofence(geofence.dict())
        
        return {
            "status": "created",
            "geofence": {
                "id": created.id,
                "name": created.name
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating geofence: {str(e)}")


@router.get("/active-drones", response_model=List[ActiveDrone])
async def get_active_drones(
    geofence_id: Optional[str] = None,
    manager=Depends(get_drone_event_manager)
):
    """
    List all currently detected drones with real-time telemetry
    Optional filtering by geofence ID to show only violating drones
    """
    try:
        drones = manager.get_active_drones()
        
        # Filter by geofence if requested
        if geofence_id:
            drones = [
                d for d in drones
                if geofence_id in d.get('geofence_violations', [])
            ]
        
        return drones
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active drones: {str(e)}")


@router.get("/drone-history/{drone_id}")
async def get_drone_history(
    drone_id: str,
    manager=Depends(get_drone_event_manager)
):
    """
    Retrieve complete flight history for a specific drone
    Returns flight path with timestamps and telemetry
    """
    try:
        history = await manager.get_drone_history(drone_id)
        
        if history is None:
            raise HTTPException(
                status_code=404,
                detail=f"No history found for drone: {drone_id}"
            )
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching drone history: {str(e)}")


@router.get("/stats")
async def get_drone_stats(
    meshtastic_mgr=Depends(get_meshtastic_manager),
    drone_mgr=Depends(get_drone_event_manager)
):
    """
    Get overall drone detection statistics
    Used by DroneAnalyticsNode and dashboard
    """
    try:
        receivers = meshtastic_mgr.get_device_status()
        active_drones = drone_mgr.get_active_drones()
        geofences = drone_mgr.get_geofences()
        
        # Calculate stats
        total_detections = sum(r['stats']['detection_count'] for r in receivers)
        connected_receivers = sum(1 for r in receivers if r['connected'])
        drones_with_violations = sum(
            1 for d in active_drones
            if d.get('geofence_violations')
        )
        
        return {
            "receivers": {
                "total": len(receivers),
                "connected": connected_receivers,
                "total_detections": total_detections
            },
            "drones": {
                "active": len(active_drones),
                "with_violations": drones_with_violations
            },
            "geofences": {
                "total": len(geofences),
                "active": sum(1 for g in geofences if g['is_active'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


# Function to set manager references (called from main.py)
def set_managers(meshtastic_mgr, drone_mgr):
    """Set global manager references"""
    global meshtastic_manager, drone_event_manager
    meshtastic_manager = meshtastic_mgr
    drone_event_manager = drone_mgr

