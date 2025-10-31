"""
Workflow Schema Definitions
JSON Schemas for visual workflow nodes, edges, and graphs
"""

# Schema version for migration tracking
SCHEMA_VERSION = "1.0.0"

# Camera/Input Node Schema
CAMERA_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["camera", "videoInput", "youtube"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "properties": {
                "cameraId": {"type": "string"},
                "cameraName": {"type": "string"},
                "videoPath": {"type": "string"},
                "youtubeUrl": {"type": "string"},
                "fps": {"type": "number", "minimum": 1, "maximum": 30, "default": 10},
                "skipSimilar": {"type": "boolean", "default": False}
            }
        }
    }
}

# Model Node Schema
MODEL_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["model"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["modelId"],
            "properties": {
                "modelId": {"type": "string"},
                "modelName": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.7},
                "classes": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Array of class IDs to detect"
                },
                "fps": {"type": "number", "minimum": 1, "maximum": 30, "default": 10},
                "batchSize": {"type": "integer", "minimum": 1, "maximum": 32, "default": 1}
            }
        }
    }
}

# Zone/Filter Node Schema
ZONE_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["zone"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["zoneType"],
            "properties": {
                "zoneType": {"type": "string", "enum": ["polygon", "line", "rectangle"]},
                "label": {"type": "string"},
                "polygon": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "minItems": 3,
                    "description": "Array of [x, y] coordinates, minimum 3 points"
                },
                "filterType": {"type": "string", "enum": ["include", "exclude"]},
                "cooldown": {"type": "integer", "minimum": 0, "description": "Cooldown in seconds"}
            }
        }
    }
}

# Action Node Schemas
EMAIL_ACTION_SCHEMA = {
    "type": "object",
    "required": ["to"],
    "properties": {
        "to": {"type": "string", "format": "email"},
        "cc": {"type": "array", "items": {"type": "string", "format": "email"}},
        "subject": {"type": "string"},
        "includeSnapshot": {"type": "boolean", "default": True},
        "includeDetections": {"type": "boolean", "default": True}
    }
}

WEBHOOK_ACTION_SCHEMA = {
    "type": "object",
    "required": ["url"],
    "properties": {
        "url": {"type": "string", "format": "uri"},
        "method": {"type": "string", "enum": ["POST", "PUT"], "default": "POST"},
        "headers": {"type": "object"},
        "timeout": {"type": "integer", "minimum": 1, "maximum": 60, "default": 10},
        "retries": {"type": "integer", "minimum": 0, "maximum": 5, "default": 3},
        "secretKey": {"type": "string", "description": "Reference to secret store key"}
    }
}

RECORD_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "duration": {"type": "integer", "minimum": 1, "maximum": 300, "default": 30},
        "preBuffer": {"type": "integer", "minimum": 0, "maximum": 60, "default": 5},
        "postBuffer": {"type": "integer", "minimum": 0, "maximum": 60, "default": 5},
        "format": {"type": "string", "enum": ["mp4", "mkv"], "default": "mp4"},
        "quality": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
    }
}

ALERT_ACTION_SCHEMA = {
    "type": "object",
    "required": ["severity"],
    "properties": {
        "severity": {"type": "string", "enum": ["info", "warning", "critical"], "default": "warning"},
        "notify": {"type": "array", "items": {"type": "string"}},
        "message": {"type": "string"}
    }
}

SNAPSHOT_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "drawBoxes": {"type": "boolean", "default": True},
        "drawZones": {"type": "boolean", "default": False},
        "format": {"type": "string", "enum": ["jpg", "png"], "default": "jpg"},
        "quality": {"type": "integer", "minimum": 1, "maximum": 100, "default": 90}
    }
}

ACTION_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["action"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["actionType", "config"],
            "properties": {
                "actionType": {"type": "string", "enum": ["email", "webhook", "record", "alert", "snapshot"]},
                "label": {"type": "string"},
                "config": {
                    "oneOf": [
                        EMAIL_ACTION_SCHEMA,
                        WEBHOOK_ACTION_SCHEMA,
                        RECORD_ACTION_SCHEMA,
                        ALERT_ACTION_SCHEMA,
                        SNAPSHOT_ACTION_SCHEMA
                    ]
                }
            }
        }
    }
}

# Link Nodes for multi-tab routing
LINK_IN_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["linkIn"]},
        "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
        "data": {
            "type": "object",
            "required": ["linkName"],
            "properties": {
                "linkName": {"type": "string"},
                "description": {"type": "string"}
            }
        }
    }
}

LINK_OUT_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["linkOut"]},
        "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
        "data": {
            "type": "object",
            "required": ["linkName"],
            "properties": {
                "linkName": {"type": "string"}
            }
        }
    }
}

LINK_CALL_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["linkCall"]},
        "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
        "data": {
            "type": "object",
            "required": ["linkName"],
            "properties": {
                "linkName": {"type": "string"},
                "parameters": {"type": "object"}
            }
        }
    }
}

# Catch Node for error handling
CATCH_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["catch"]},
        "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
        "data": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["all", "specific"]},
                "nodeIds": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}

# Config Node for reusable configurations
CONFIG_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["config"]},
        "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
        "data": {
            "type": "object",
            "required": ["config"],
            "properties": {
                "configType": {"type": "string", "enum": ["generic", "model", "webhook", "record", "email"]},
                "configName": {"type": "string"},
                "description": {"type": "string"},
                "config": {"type": "object", "description": "Configuration JSON object"}
            }
        }
    }
}

# Audio Extractor Node Schema
AUDIO_EXTRACTOR_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["audioExtractor"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "properties": {
                "sampleRate": {"type": "integer", "minimum": 8000, "maximum": 48000, "default": 16000},
                "channels": {"type": "integer", "enum": [1, 2], "default": 1},
                "format": {"type": "string", "enum": ["wav", "mp3", "flac", "pcm"], "default": "wav"},
                "bufferDuration": {"type": "number", "minimum": 1, "maximum": 60, "default": 5}
            }
        }
    }
}

# Audio AI Node Schema
AUDIO_AI_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["audioAI"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["modelId"],
            "properties": {
                "modelId": {"type": "string"},
                "modelName": {"type": "string"},
                "modelType": {"type": "string", "enum": ["transcription", "sound_classification"]},
                "language": {"type": "string", "default": "auto"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.7},
                "detectKeywords": {"type": "array", "items": {"type": "string"}},
                "bufferDuration": {"type": "number", "minimum": 1, "maximum": 60}
            }
        }
    }
}

# UniFi Node Schemas
UNIFI_CAMERA_DISCOVERY_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["unifiCameraDiscovery"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["credentialId"],
            "properties": {
                "credentialId": {"type": "string"},
                "credentialName": {"type": "string"},
                "filterState": {"type": "string", "enum": ["all", "connected", "disconnected"]},
                "filterRecording": {"type": "boolean"}
            }
        }
    }
}

UNIFI_PROTECT_EVENT_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["unifiProtectEvent"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["credentialId"],
            "properties": {
                "credentialId": {"type": "string"},
                "credentialName": {"type": "string"},
                "eventTypes": {"type": "array", "items": {"type": "string", "enum": ["motion", "smart", "ring"]}},
                "cameraFilter": {"type": "array", "items": {"type": "string"}},
                "detectionTypes": {"type": "array", "items": {"type": "string", "enum": ["person", "vehicle", "animal"]}},
                "pollInterval": {"type": "number", "minimum": 5, "maximum": 300, "default": 10}
            }
        }
    }
}

UNIFI_DEVICE_STATUS_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["unifiDeviceStatus"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["credentialId"],
            "properties": {
                "credentialId": {"type": "string"},
                "credentialName": {"type": "string"},
                "deviceTypes": {"type": "array", "items": {"type": "string"}},
                "checkOffline": {"type": "boolean", "default": False}
            }
        }
    }
}

UNIFI_CLIENT_DETECTION_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["unifiClientDetection"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["credentialId"],
            "properties": {
                "credentialId": {"type": "string"},
                "credentialName": {"type": "string"},
                "macFilter": {"type": "array", "items": {"type": "string"}},
                "hostnameFilter": {"type": "array", "items": {"type": "string"}},
                "activeOnly": {"type": "boolean", "default": True}
            }
        }
    }
}

UNIFI_ADD_CAMERA_NODE_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "position", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string", "enum": ["unifiAddCamera"]},
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        "data": {
            "type": "object",
            "required": ["sublocationId"],
            "properties": {
                "sublocationId": {"type": "string"},
                "sublocationName": {"type": "string"},
                "streamQuality": {"type": "string", "enum": ["high", "medium", "low"], "default": "medium"},
                "autoEnable": {"type": "boolean", "default": True}
            }
        }
    }
}

# Edge Schema
EDGE_SCHEMA = {
    "type": "object",
    "required": ["id", "source", "target"],
    "properties": {
        "id": {"type": "string"},
        "source": {"type": "string"},
        "target": {"type": "string"},
        "sourceHandle": {"type": "string"},
        "targetHandle": {"type": "string"},
        "type": {"type": "string", "enum": ["animated", "data", "error"]},
        "data": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["video", "detections", "zones", "raw_data", "error", "debug"]},
                "label": {"type": "string"}
            }
        }
    }
}

# Top-level Workflow Graph Schema
WORKFLOW_GRAPH_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "schemaVersion", "nodes", "edges"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "schemaVersion": {"type": "string"},
        "siteId": {"type": "string"},
        "nodes": {
            "type": "array",
            "items": {
                "oneOf": [
                    CAMERA_NODE_SCHEMA,
                    MODEL_NODE_SCHEMA,
                    ZONE_NODE_SCHEMA,
                    ACTION_NODE_SCHEMA,
                    LINK_IN_NODE_SCHEMA,
                    LINK_OUT_NODE_SCHEMA,
                    LINK_CALL_NODE_SCHEMA,
                    CATCH_NODE_SCHEMA,
                    CONFIG_NODE_SCHEMA,
                    AUDIO_EXTRACTOR_NODE_SCHEMA,
                    AUDIO_AI_NODE_SCHEMA,
                    UNIFI_CAMERA_DISCOVERY_NODE_SCHEMA,
                    UNIFI_PROTECT_EVENT_NODE_SCHEMA,
                    UNIFI_DEVICE_STATUS_NODE_SCHEMA,
                    UNIFI_CLIENT_DETECTION_NODE_SCHEMA,
                    UNIFI_ADD_CAMERA_NODE_SCHEMA
                ]
            }
        },
        "edges": {
            "type": "array",
            "items": EDGE_SCHEMA
        },
        "metadata": {
            "type": "object",
            "properties": {
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}

# Subflow/Template Schema
SUBFLOW_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "nodes", "edges", "parameters"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "category": {"type": "string"},
        "parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["string", "number", "boolean", "array", "object"]},
                    "default": {},
                    "required": {"type": "boolean"},
                    "description": {"type": "string"}
                }
            }
        },
        "nodes": {"type": "array"},
        "edges": {"type": "array"},
        "inputs": {"type": "array", "items": {"type": "string"}, "description": "Node IDs that act as inputs"},
        "outputs": {"type": "array", "items": {"type": "string"}, "description": "Node IDs that act as outputs"}
    }
}

# Port Type Registry - defines allowed connections
PORT_COMPATIBILITY = {
    "camera": {
        "outputs": {
            "video-output": ["video"]
        }
    },
    "videoInput": {
        "outputs": {
            "video-output": ["video"]
        }
    },
    "youtube": {
        "outputs": {
            "video-output": ["video"]
        }
    },
    "model": {
        "inputs": {
            "video-input": ["video"]
        },
        "outputs": {
            "detections-output": ["detections"],
            "data-output": ["raw_data"]
        }
    },
    "zone": {
        "inputs": {
            "detections-input": ["detections"]
        },
        "outputs": {
            "filtered-output": ["detections"]
        }
    },
    "audioExtractor": {
        "inputs": {
            "video-input": ["video"]
        },
        "outputs": {
            "audio-output": ["audio"]
        }
    },
    "audioAI": {
        "inputs": {
            "audio-input": ["audio"]
        },
        "outputs": {
            "transcript-output": ["audio_data", "detections"]
        }
    },
    "action": {
        "inputs": {
            "trigger-input": ["detections", "zones", "audio_data"]
        }
    },
    "dataPreview": {
        "inputs": {
            "data-input": ["raw_data", "detections", "debug", "audio", "audio_data"]
        }
    },
    "debug": {
        "inputs": {
            "data-input": ["raw_data", "detections", "video", "zones", "debug", "audio", "audio_data"]
        }
    },
    "linkIn": {
        "outputs": {
            "link-output": ["video", "detections", "zones", "raw_data"]
        }
    },
    "linkOut": {
        "inputs": {
            "link-input": ["video", "detections", "zones", "raw_data"]
        }
    },
    "linkCall": {
        "inputs": {
            "call-input": ["video", "detections", "zones", "raw_data"]
        },
        "outputs": {
            "call-output": ["video", "detections", "zones", "raw_data"]
        }
    },
    "catch": {
        "inputs": {
            "error-input": ["error"]
        },
        "outputs": {
            "handled-output": ["detections"]
        }
    },
    "config": {
        "outputs": {
            "config-output": ["config"]
        }
    },
    "unifiCameraDiscovery": {
        "outputs": {
            "cameras-output": ["unifi_data", "raw_data"]
        }
    },
    "unifiProtectEvent": {
        "outputs": {
            "events-output": ["unifi_data", "raw_data", "detections"]
        }
    },
    "unifiDeviceStatus": {
        "outputs": {
            "devices-output": ["unifi_data", "raw_data"]
        }
    },
    "unifiClientDetection": {
        "outputs": {
            "clients-output": ["unifi_data", "raw_data"]
        }
    },
    "unifiAddCamera": {
        "inputs": {
            "cameras-input": ["unifi_data"]
        },
        "outputs": {
            "result-output": ["raw_data"]
        }
    }
}

# Config nodes can connect to these node types
CONFIG_COMPATIBLE_NODES = ["model", "action", "zone"]

# Sensitive field keys for redaction
SENSITIVE_FIELDS = {
    "url", "webhookUrl", "email", "to", "cc", "bcc",
    "Authorization", "headers", "password", "token",
    "apiKey", "secretKey", "secret"
}


def get_action_schema(action_type: str):
    """Get schema for specific action type"""
    schemas = {
        "email": EMAIL_ACTION_SCHEMA,
        "webhook": WEBHOOK_ACTION_SCHEMA,
        "record": RECORD_ACTION_SCHEMA,
        "alert": ALERT_ACTION_SCHEMA,
        "snapshot": SNAPSHOT_ACTION_SCHEMA
    }
    return schemas.get(action_type)


def validate_port_connection(source_type: str, source_handle: str, target_type: str, target_handle: str) -> tuple[bool, str]:
    """
    Validate if a connection between two ports is allowed
    
    Returns:
        (is_valid, error_message)
    """
    source_config = PORT_COMPATIBILITY.get(source_type)
    target_config = PORT_COMPATIBILITY.get(target_type)
    
    if not source_config:
        return False, f"Unknown source node type: {source_type}"
    
    if not target_config:
        return False, f"Unknown target node type: {target_type}"
    
    # Check if source has outputs
    source_outputs = source_config.get("outputs", {})
    if not source_outputs:
        return False, f"{source_type} node has no outputs"
    
    # Check if target has inputs
    target_inputs = target_config.get("inputs", {})
    if not target_inputs:
        return False, f"{target_type} node has no inputs"
    
    # Check if source handle exists
    source_data_types = source_outputs.get(source_handle, [])
    if not source_data_types:
        return False, f"{source_type} has no output handle '{source_handle}'"
    
    # Check if target handle exists
    target_data_types = target_inputs.get(target_handle, [])
    if not target_data_types:
        return False, f"{target_type} has no input handle '{target_handle}'"
    
    # Check if data types are compatible
    compatible = any(st in target_data_types for st in source_data_types)
    if not compatible:
        return False, f"Incompatible data types: {source_data_types} -> {target_data_types}"
    
    return True, ""


def redact_sensitive_data(data: dict, depth: int = 0, max_depth: int = 5) -> dict:
    """
    Recursively redact sensitive fields from dict
    
    Args:
        data: Dictionary to redact
        depth: Current recursion depth
        max_depth: Maximum recursion depth
        
    Returns:
        Dictionary with sensitive fields redacted
    """
    if depth > max_depth or not isinstance(data, dict):
        return data
    
    redacted = {}
    for key, value in data.items():
        if key in SENSITIVE_FIELDS:
            # Redact but show type and partial length
            if isinstance(value, str):
                redacted[key] = f"<redacted:{len(value)} chars>"
            else:
                redacted[key] = "<redacted>"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value, depth + 1, max_depth)
        elif isinstance(value, list):
            redacted[key] = [
                redact_sensitive_data(item, depth + 1, max_depth) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted

