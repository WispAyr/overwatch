"""
Alarm Storage
Persistent storage for alarms and alarm-event correlations
"""
import aiosqlite
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from core.config import settings


logger = logging.getLogger('overwatch.alarms.storage')


class AlarmStorage:
    """SQLite alarm storage"""
    
    def __init__(self):
        self.db_path = settings.EVENT_DB_PATH
        self.db = None
        
    async def initialize(self):
        """Initialize database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info(f"Alarm storage initialized: {self.db_path}")
        
    async def _create_tables(self):
        """Create alarm tables"""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id TEXT PRIMARY KEY,
                group_key TEXT NOT NULL,
                tenant TEXT,
                site TEXT,
                severity TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_sla_deadline TEXT,
                confidence REAL,
                assignee TEXT,
                runbook_id TEXT,
                escalation_policy TEXT,
                watchers TEXT,
                links TEXT,
                attributes TEXT
            )
        """)
        
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS alarm_events (
                alarm_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                correlated_at TEXT NOT NULL,
                PRIMARY KEY (alarm_id, event_id)
            )
        """)
        
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS alarm_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alarm_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT,
                action TEXT NOT NULL,
                user TEXT,
                note TEXT
            )
        """)
        
        # Indices
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_group_key ON alarms(group_key)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_state ON alarms(state)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_severity ON alarms(severity)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_tenant ON alarms(tenant)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_site ON alarms(site)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_assignee ON alarms(assignee)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_created_at ON alarms(created_at)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_alarm_events_event ON alarm_events(event_id)")
        
        await self.db.commit()
        
    async def create_alarm(self, alarm: Dict[str, Any]) -> str:
        """Create a new alarm"""
        await self.db.execute("""
            INSERT INTO alarms (
                id, group_key, tenant, site, severity, state,
                created_at, updated_at, current_sla_deadline, confidence,
                assignee, runbook_id, escalation_policy, watchers, links, attributes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alarm['id'],
            alarm['group_key'],
            alarm.get('tenant'),
            alarm.get('site'),
            alarm['severity'],
            alarm['state'],
            alarm['created_at'],
            alarm['updated_at'],
            alarm.get('current_sla_deadline'),
            alarm.get('confidence'),
            alarm.get('assignee'),
            alarm.get('runbook_id'),
            alarm.get('escalation_policy'),
            json.dumps(alarm.get('watchers', [])),
            json.dumps(alarm.get('links', {})),
            json.dumps(alarm.get('attributes', {}))
        ))
        
        await self.db.commit()
        return alarm['id']
        
    async def update_alarm(self, alarm_id: str, updates: Dict[str, Any]):
        """Update an existing alarm"""
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [alarm_id]
        
        await self.db.execute(
            f"UPDATE alarms SET {set_clause} WHERE id = ?",
            values
        )
        await self.db.commit()
        
    async def get_alarm(self, alarm_id: str) -> Optional[Dict[str, Any]]:
        """Get alarm by ID"""
        async with self.db.execute(
            "SELECT * FROM alarms WHERE id = ?",
            (alarm_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_alarm(row)
            
    async def get_alarm_by_group_key(self, group_key: str, state_filter: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get open alarm by group_key"""
        if state_filter is None:
            state_filter = ['NEW', 'TRIAGE', 'ACTIVE', 'CONTAINED']
            
        placeholders = ','.join(['?' for _ in state_filter])
        query = f"SELECT * FROM alarms WHERE group_key = ? AND state IN ({placeholders}) ORDER BY created_at DESC LIMIT 1"
        
        async with self.db.execute(query, [group_key] + state_filter) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_alarm(row)
            
    async def query_alarms(
        self,
        tenant: Optional[str] = None,
        site: Optional[str] = None,
        state: Optional[str] = None,
        severity: Optional[str] = None,
        assignee: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query alarms with filters"""
        query = "SELECT * FROM alarms WHERE 1=1"
        params = []
        
        if tenant:
            query += " AND tenant = ?"
            params.append(tenant)
        if site:
            query += " AND site = ?"
            params.append(site)
        if state:
            query += " AND state = ?"
            params.append(state)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if assignee:
            query += " AND assignee = ?"
            params.append(assignee)
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_alarm(row) for row in rows]
            
    async def count_alarms(
        self,
        tenant: Optional[str] = None,
        site: Optional[str] = None,
        state: Optional[str] = None,
        severity: Optional[str] = None
    ) -> int:
        """Count alarms"""
        query = "SELECT COUNT(*) FROM alarms WHERE 1=1"
        params = []
        
        if tenant:
            query += " AND tenant = ?"
            params.append(tenant)
        if site:
            query += " AND site = ?"
            params.append(site)
        if state:
            query += " AND state = ?"
            params.append(state)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
            
        async with self.db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
            
    async def add_event_to_alarm(self, alarm_id: str, event_id: str):
        """Correlate an event to an alarm"""
        await self.db.execute("""
            INSERT OR IGNORE INTO alarm_events (alarm_id, event_id, correlated_at)
            VALUES (?, ?, ?)
        """, (alarm_id, event_id, datetime.utcnow().isoformat()))
        await self.db.commit()
        
    async def get_alarm_events(self, alarm_id: str) -> List[str]:
        """Get all event IDs correlated to an alarm"""
        async with self.db.execute(
            "SELECT event_id FROM alarm_events WHERE alarm_id = ? ORDER BY correlated_at",
            (alarm_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
            
    async def add_history_entry(
        self,
        alarm_id: str,
        action: str,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        user: Optional[str] = None,
        note: Optional[str] = None
    ):
        """Add history entry for an alarm"""
        await self.db.execute("""
            INSERT INTO alarm_history (alarm_id, timestamp, from_state, to_state, action, user, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            alarm_id,
            datetime.utcnow().isoformat(),
            from_state,
            to_state,
            action,
            user,
            note
        ))
        await self.db.commit()
        
    async def get_alarm_history(self, alarm_id: str) -> List[Dict[str, Any]]:
        """Get history for an alarm"""
        async with self.db.execute(
            "SELECT * FROM alarm_history WHERE alarm_id = ? ORDER BY timestamp",
            (alarm_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{
                'id': row[0],
                'alarm_id': row[1],
                'timestamp': row[2],
                'from_state': row[3],
                'to_state': row[4],
                'action': row[5],
                'user': row[6],
                'note': row[7]
            } for row in rows]
            
    def _row_to_alarm(self, row) -> Dict[str, Any]:
        """Convert database row to alarm dict"""
        return {
            'id': row[0],
            'group_key': row[1],
            'tenant': row[2],
            'site': row[3],
            'severity': row[4],
            'state': row[5],
            'created_at': row[6],
            'updated_at': row[7],
            'current_sla_deadline': row[8],
            'confidence': row[9],
            'assignee': row[10],
            'runbook_id': row[11],
            'escalation_policy': row[12],
            'watchers': json.loads(row[13]) if row[13] else [],
            'links': json.loads(row[14]) if row[14] else {},
            'attributes': json.loads(row[15]) if row[15] else {}
        }
        
    async def cleanup(self):
        """Cleanup database connection"""
        if self.db:
            await self.db.close()


