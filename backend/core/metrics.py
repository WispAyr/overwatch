"""
Prometheus Metrics

Counters and histograms for observability
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import logging


logger = logging.getLogger('overwatch.metrics')


# System Info
system_info = Info('overwatch_system', 'Overwatch system information')

# Frame Processing Metrics
frames_received = Counter(
    'overwatch_frames_received_total',
    'Total frames received from cameras',
    ['camera_id', 'workflow_id']
)

frames_processed = Counter(
    'overwatch_frames_processed_total',
    'Total frames successfully processed',
    ['camera_id', 'workflow_id']
)

frames_dropped = Counter(
    'overwatch_frames_dropped_total',
    'Total frames dropped due to backpressure',
    ['camera_id', 'workflow_id', 'reason']
)

# Detection Metrics
detections_total = Counter(
    'overwatch_detections_total',
    'Total object detections',
    ['camera_id', 'workflow_id', 'class_name']
)

# Model Performance
model_inference_duration = Histogram(
    'overwatch_model_inference_duration_seconds',
    'Model inference duration in seconds',
    ['model_id', 'workflow_id'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

model_load_duration = Histogram(
    'overwatch_model_load_duration_seconds',
    'Model load duration in seconds',
    ['model_id']
)

# Event Metrics
events_created = Counter(
    'overwatch_events_created_total',
    'Total events created',
    ['workflow_id', 'severity']
)

events_storage_duration = Histogram(
    'overwatch_events_storage_duration_seconds',
    'Event storage duration',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

# Alarm Metrics
alarms_created = Counter(
    'overwatch_alarms_created_total',
    'Total alarms created',
    ['severity', 'site']
)

alarms_transitioned = Counter(
    'overwatch_alarms_transitioned_total',
    'Total alarm state transitions',
    ['from_state', 'to_state']
)

alarms_by_state = Gauge(
    'overwatch_alarms_by_state',
    'Current alarms by state',
    ['state', 'severity']
)

alarm_sla_breaches = Counter(
    'overwatch_alarm_sla_breaches_total',
    'Total SLA breaches',
    ['severity']
)

# Rules Engine Metrics
rules_evaluated = Counter(
    'overwatch_rules_evaluated_total',
    'Total rule evaluations',
    ['rule_id']
)

rules_triggered = Counter(
    'overwatch_rules_triggered_total',
    'Total rule triggers',
    ['rule_id', 'action_type']
)

rules_evaluation_duration = Histogram(
    'overwatch_rules_evaluation_duration_seconds',
    'Rule evaluation duration',
    ['rule_id']
)

# WebSocket Metrics
websocket_connections = Gauge(
    'overwatch_websocket_connections',
    'Current WebSocket connections'
)

websocket_messages_sent = Counter(
    'overwatch_websocket_messages_sent_total',
    'Total WebSocket messages sent',
    ['topic']
)

websocket_messages_dropped = Counter(
    'overwatch_websocket_messages_dropped_total',
    'Total WebSocket messages dropped',
    ['reason']
)

# Stream Health Metrics
stream_status = Gauge(
    'overwatch_stream_status',
    'Stream health status (1=healthy, 0=unhealthy)',
    ['camera_id']
)

stream_reconnects = Counter(
    'overwatch_stream_reconnects_total',
    'Total stream reconnections',
    ['camera_id']
)

stream_errors = Counter(
    'overwatch_stream_errors_total',
    'Total stream errors',
    ['camera_id', 'error_type']
)

# Queue Metrics
workflow_queue_depth = Gauge(
    'overwatch_workflow_queue_depth',
    'Current workflow queue depth',
    ['camera_id', 'workflow_id']
)

# API Metrics
http_requests = Counter(
    'overwatch_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration = Histogram(
    'overwatch_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)


def init_metrics(version: str = '1.0.0', node_id: str = 'overwatch-1'):
    """Initialize system info metrics"""
    system_info.info({
        'version': version,
        'node_id': node_id
    })
    logger.info(f"Metrics initialized for {node_id} v{version}")


