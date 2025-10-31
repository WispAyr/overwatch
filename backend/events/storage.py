"""
Event Storage
SQLite storage for events
"""
import aiosqlite
import json
import logging
from typing import List, Optional
from pathlib import Path

from core.config import settings


logger = logging.getLogger('overwatch.events.storage')


class EventStorage:
    """SQLite event storage"""
    
    def __init__(self):
        self.db_path = settings.EVENT_DB_PATH
        self.db = None
        
    async def initialize(self):
        """Initialize database"""
        # Create data directory
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self.db = await aiosqlite.connect(self.db_path)
        
        # Create tables
        await self._create_tables()
        
        logger.info(f"Event storage initialized: {self.db_path}")
        
    async def _create_tables(self):
        """Create database tables with unified schema"""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                tenant TEXT,
                site TEXT,
                source_type TEXT,
                source_subtype TEXT,
                source_device_id TEXT,
                source_vendor TEXT,
                source_model TEXT,
                observed TEXT NOT NULL,
                ingested TEXT NOT NULL,
                location_lat REAL,
                location_lon REAL,
                location_floor INTEGER,
                location_area_id TEXT,
                geometry TEXT,
                attributes TEXT NOT NULL,
                media_snapshot_url TEXT,
                media_clip_url TEXT,
                raw TEXT,
                tags TEXT,
                camera_id TEXT,
                workflow_id TEXT,
                severity TEXT
            )
        """)
        
        # Indices for canonical schema
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_tenant ON events(tenant)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_site ON events(site)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON events(source_type)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_observed ON events(observed)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_ingested ON events(ingested)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_area ON events(location_area_id)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_severity ON events(severity)")
        # Legacy indices
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_camera_id ON events(camera_id)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_workflow_id ON events(workflow_id)")
        
        await self.db.commit()
        
    async def store_event(self, event: dict):
        """Store an event with canonical schema"""
        # Extract nested fields
        source = event.get('source', {})
        location = event.get('location', {})
        media = event.get('media', {})
        
        # Handle both new canonical and legacy formats
        observed = event.get('observed', event.get('timestamp', datetime.utcnow()).isoformat() if isinstance(event.get('timestamp'), datetime) else event.get('timestamp'))
        ingested = event.get('ingested', datetime.utcnow().isoformat())
        
        await self.db.execute("""
            INSERT INTO events (
                id, tenant, site,
                source_type, source_subtype, source_device_id, source_vendor, source_model,
                observed, ingested,
                location_lat, location_lon, location_floor, location_area_id,
                geometry, attributes, media_snapshot_url, media_clip_url,
                raw, tags,
                camera_id, workflow_id, severity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['id'],
            event.get('tenant'),
            event.get('site'),
            source.get('type'),
            source.get('subtype'),
            source.get('device_id', event.get('camera_id')),  # Fallback to legacy
            source.get('vendor'),
            source.get('model'),
            observed,
            ingested,
            location.get('lat'),
            location.get('lon'),
            location.get('floor'),
            location.get('area_id'),
            json.dumps(event.get('geometry')) if event.get('geometry') else None,
            json.dumps(event.get('attributes', event.get('detections', []))),  # Support both
            media.get('snapshot_url', event.get('snapshot_path')),  # Fallback to legacy
            media.get('clip_url', event.get('recording_path')),  # Fallback to legacy
            json.dumps(event.get('raw', {})),
            json.dumps(event.get('tags', [])),
            event.get('camera_id'),  # Keep for backward compatibility
            event.get('workflow_id'),  # Keep for backward compatibility
            event.get('severity', 'info')
        ))
        
        await self.db.commit()
        
    async def get_event(self, event_id: str) -> Optional[dict]:
        """Get event by ID"""
        async with self.db.execute(
            "SELECT * FROM events WHERE id = ?",
            (event_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
            if not row:
                return None
                
            return self._row_to_event(row)
            
    async def query_events(
        self,
        camera_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        severity: Optional[str] = None,
        tenant: Optional[str] = None,
        site: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        since_ts: Optional[str] = None,
        before_ts: Optional[str] = None
    ) -> List[dict]:
        """Query events with canonical and legacy filters"""
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        # Canonical filters
        if tenant:
            query += " AND tenant = ?"
            params.append(tenant)
        if site:
            query += " AND site = ?"
            params.append(site)
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
            
        # Legacy filters
        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
            
        # Timestamp filters for pagination
        if since_ts:
            query += " AND observed > ?"
            params.append(since_ts)
        if before_ts:
            query += " AND observed < ?"
            params.append(before_ts)
            
        query += " ORDER BY observed DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_event(row) for row in rows]
            
    async def count_events(
        self,
        camera_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        severity: Optional[str] = None,
        tenant: Optional[str] = None,
        site: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> int:
        """Count events with canonical and legacy filters"""
        query = "SELECT COUNT(*) FROM events WHERE 1=1"
        params = []
        
        # Canonical filters
        if tenant:
            query += " AND tenant = ?"
            params.append(tenant)
        if site:
            query += " AND site = ?"
            params.append(site)
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
            
        # Legacy filters
        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
            
        async with self.db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
            
    def _row_to_event(self, row) -> dict:
        """Convert database row to canonical event dict"""
        return {
            'id': row[0],
            'tenant': row[1],
            'site': row[2],
            'source': {
                'type': row[3],
                'subtype': row[4],
                'device_id': row[5],
                'vendor': row[6],
                'model': row[7]
            },
            'observed': row[8],
            'ingested': row[9],
            'location': {
                'lat': row[10],
                'lon': row[11],
                'floor': row[12],
                'area_id': row[13]
            },
            'geometry': json.loads(row[14]) if row[14] else None,
            'attributes': json.loads(row[15]) if row[15] else {},
            'media': {
                'snapshot_url': row[16],
                'clip_url': row[17]
            },
            'raw': json.loads(row[18]) if row[18] else {},
            'tags': json.loads(row[19]) if row[19] else [],
            # Legacy fields for backward compatibility
            'camera_id': row[20],
            'workflow_id': row[21],
            'severity': row[22]
        }
        
    async def cleanup(self):
        """Cleanup database connection"""
        if self.db:
            await self.db.close()

