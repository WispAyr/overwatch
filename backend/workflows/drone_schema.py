"""
Drone Workflow Node Schemas
JSON schema definitions for drone detection workflow node configurations
"""

DRONE_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "receiver_id": {
            "type": "string",
            "description": "Meshtastic receiver device ID (empty for all receivers)"
        },
        "update_rate": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 10,
            "default": 1.0,
            "description": "Detection update rate in Hz"
        },
        "min_rssi": {
            "type": "integer",
            "minimum": -120,
            "maximum": -20,
            "default": -100,
            "description": "Minimum signal strength threshold in dBm"
        },
        "enable_preview": {
            "type": "boolean",
            "default": False,
            "description": "Show mini-map preview in node"
        }
    },
    "required": []
}

DRONE_FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "altitude_min": {
            "type": "number",
            "minimum": 0,
            "maximum": 10000,
            "default": 0,
            "description": "Minimum altitude in meters"
        },
        "altitude_max": {
            "type": "number",
            "minimum": 0,
            "maximum": 10000,
            "default": 10000,
            "description": "Maximum altitude in meters"
        },
        "speed_min": {
            "type": "number",
            "minimum": 0,
            "maximum": 300,
            "default": 0,
            "description": "Minimum speed in m/s"
        },
        "speed_max": {
            "type": "number",
            "minimum": 0,
            "maximum": 300,
            "default": 300,
            "description": "Maximum speed in m/s"
        },
        "geofence_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Filter to specific geofence violations"
        },
        "operator_distance_max": {
            "type": "number",
            "minimum": 0,
            "maximum": 100000,
            "description": "Maximum distance between drone and operator in meters"
        },
        "rssi_min": {
            "type": "integer",
            "minimum": -120,
            "maximum": -20,
            "description": "Minimum RSSI for reliable detections"
        },
        "filter_mode": {
            "type": "string",
            "enum": ["pass_matching", "pass_violations"],
            "default": "pass_matching",
            "description": "Pass detections matching criteria or only violations"
        }
    }
}

DRONE_MAP_SCHEMA = {
    "type": "object",
    "properties": {
        "map_provider": {
            "type": "string",
            "enum": ["leaflet", "mapbox"],
            "default": "leaflet",
            "description": "Map rendering library"
        },
        "center_lat": {
            "type": "number",
            "minimum": -90,
            "maximum": 90,
            "description": "Initial map center latitude"
        },
        "center_lon": {
            "type": "number",
            "minimum": -180,
            "maximum": 180,
            "description": "Initial map center longitude"
        },
        "initial_zoom": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20,
            "default": 13,
            "description": "Initial map zoom level"
        },
        "track_history_duration": {
            "type": "integer",
            "minimum": 60,
            "maximum": 86400,
            "default": 3600,
            "description": "Flight track history duration in seconds"
        },
        "auto_center": {
            "type": "boolean",
            "default": True,
            "description": "Auto-center map on new detections"
        },
        "show_geofences": {
            "type": "boolean",
            "default": True,
            "description": "Display geofence boundaries on map"
        },
        "show_operators": {
            "type": "boolean",
            "default": True,
            "description": "Show operator positions if available"
        },
        "marker_style": {
            "type": "string",
            "enum": ["simple", "detailed"],
            "default": "simple",
            "description": "Drone marker visual style"
        }
    }
}

DRONE_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {
            "type": "string",
            "enum": [
                "alarm",
                "notify_authorities",
                "camera_slew",
                "log_flight",
                "geofence_alert",
                "operator_notification"
            ],
            "description": "Type of action to trigger"
        },
        "alarm_severity": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "default": "high",
            "description": "Alarm severity level (for alarm action)"
        },
        "alarm_title": {
            "type": "string",
            "description": "Alarm title template"
        },
        "authority_contact": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "phone": {"type": "string"},
                "agency": {"type": "string"}
            },
            "description": "Authority contact information"
        },
        "camera_id": {
            "type": "string",
            "description": "PTZ camera ID for slewing (for camera_slew action)"
        },
        "notification_template": {
            "type": "string",
            "description": "Notification message template"
        },
        "include_flight_path": {
            "type": "boolean",
            "default": True,
            "description": "Include flight path data in notifications"
        },
        "enforcement_level": {
            "type": "string",
            "enum": ["log_only", "warning", "critical"],
            "default": "warning",
            "description": "Enforcement level for geofence alerts"
        }
    },
    "required": ["action_type"]
}

DRONE_ANALYTICS_SCHEMA = {
    "type": "object",
    "properties": {
        "time_window": {
            "type": "integer",
            "minimum": 60,
            "maximum": 604800,
            "default": 3600,
            "description": "Analysis time window in seconds"
        },
        "aggregation_interval": {
            "type": "integer",
            "minimum": 60,
            "maximum": 86400,
            "default": 300,
            "description": "Data aggregation interval in seconds"
        },
        "enable_hotspot_detection": {
            "type": "boolean",
            "default": True,
            "description": "Detect geographic hotspots"
        },
        "enable_pattern_analysis": {
            "type": "boolean",
            "default": True,
            "description": "Detect recurring flight patterns"
        },
        "enable_compliance_scoring": {
            "type": "boolean",
            "default": True,
            "description": "Calculate compliance percentage"
        },
        "enable_temporal_analysis": {
            "type": "boolean",
            "default": True,
            "description": "Track activity by time of day"
        },
        "violation_threshold": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "default": 0.1,
            "description": "Violation rate threshold for alerts (0-1)"
        },
        "hotspot_radius": {
            "type": "number",
            "minimum": 10,
            "maximum": 10000,
            "default": 100,
            "description": "Radius for hotspot clustering in meters"
        },
        "min_detections_for_pattern": {
            "type": "integer",
            "minimum": 3,
            "maximum": 100,
            "default": 5,
            "description": "Minimum detections to identify a pattern"
        }
    }
}


def validate_drone_node_config(node_type: str, config: dict) -> tuple[bool, str]:
    """
    Validate drone node configuration against schema
    Returns (is_valid, error_message)
    """
    schemas = {
        "droneInput": DRONE_INPUT_SCHEMA,
        "droneFilter": DRONE_FILTER_SCHEMA,
        "droneMap": DRONE_MAP_SCHEMA,
        "droneAction": DRONE_ACTION_SCHEMA,
        "droneAnalytics": DRONE_ANALYTICS_SCHEMA
    }
    
    schema = schemas.get(node_type)
    if not schema:
        return False, f"Unknown drone node type: {node_type}"
    
    # Manual validation for required fields
    required = schema.get("required", [])
    for field in required:
        if field not in config:
            return False, f"Missing required field: {field}"
    
    # Validate field types and constraints
    properties = schema.get("properties", {})
    for key, value in config.items():
        if key not in properties:
            continue
        
        prop_schema = properties[key]
        prop_type = prop_schema.get("type")
        
        # Type validation
        if prop_type == "number" and not isinstance(value, (int, float)):
            return False, f"Field {key} must be a number"
        if prop_type == "integer" and not isinstance(value, int):
            return False, f"Field {key} must be an integer"
        if prop_type == "string" and not isinstance(value, str):
            return False, f"Field {key} must be a string"
        if prop_type == "boolean" and not isinstance(value, bool):
            return False, f"Field {key} must be a boolean"
        if prop_type == "array" and not isinstance(value, list):
            return False, f"Field {key} must be an array"
        
        # Range validation for numbers
        if prop_type in ("number", "integer"):
            if "minimum" in prop_schema and value < prop_schema["minimum"]:
                return False, f"Field {key} must be >= {prop_schema['minimum']}"
            if "maximum" in prop_schema and value > prop_schema["maximum"]:
                return False, f"Field {key} must be <= {prop_schema['maximum']}"
        
        # Enum validation
        if "enum" in prop_schema and value not in prop_schema["enum"]:
            return False, f"Field {key} must be one of: {prop_schema['enum']}"
    
    # Custom validation logic
    if node_type == "droneFilter":
        if config.get("altitude_min", 0) >= config.get("altitude_max", 10000):
            return False, "altitude_min must be less than altitude_max"
        if config.get("speed_min", 0) >= config.get("speed_max", 300):
            return False, "speed_min must be less than speed_max"
    
    if node_type == "droneMap":
        if "center_lat" in config and not (-90 <= config["center_lat"] <= 90):
            return False, "center_lat must be between -90 and 90"
        if "center_lon" in config and not (-180 <= config["center_lon"] <= 180):
            return False, "center_lon must be between -180 and 180"
    
    return True, ""

