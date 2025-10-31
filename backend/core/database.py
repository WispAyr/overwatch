"""
Database connection and models
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from .config import settings


# SQLAlchemy setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Organization(Base):
    """Organization model"""
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # renamed from metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class Site(Base):
    """Site model"""
    __tablename__ = "sites"
    
    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    site_type = Column(String, default="fixed")  # fixed or mobile
    location = Column(JSON, nullable=True)  # {address, lat, lng, etc}
    extra_data = Column(JSON, nullable=True)  # renamed from metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class Sublocation(Base):
    """Sublocation model (zones within a site)"""
    __tablename__ = "sublocations"
    
    id = Column(String, primary_key=True, index=True)
    site_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    sublocation_type = Column(String, nullable=True)  # entrance, parking, bay, etc
    extra_data = Column(JSON, nullable=True)  # renamed from metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class Event(Base):
    """Event database model"""
    __tablename__ = "events"
    
    id = Column(String, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    workflow_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    severity = Column(String, index=True)
    detections = Column(JSON)
    snapshot_path = Column(String, nullable=True)
    recording_path = Column(String, nullable=True)
    extra_data = Column(JSON, nullable=True)  # renamed from metadata
    

class Camera(Base):
    """Camera/Sensor database model"""
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, index=True)
    sublocation_id = Column(String, index=True, nullable=False)
    name = Column(String)
    type = Column(String)  # rtsp, unifi, onvif, etc
    sensor_type = Column(String, default="camera")  # camera, sensor, etc
    rtsp_url = Column(String, nullable=True)  # Legacy single URL
    streams = Column(JSON, nullable=True)  # Multi-resolution streams
    active_stream = Column(String, default="medium")  # Active stream quality
    enabled = Column(Integer, default=1)
    workflows = Column(JSON)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class Workflow(Base):
    """Workflow database model"""
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    model = Column(String)
    enabled = Column(Integer, default=1)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

class UniFiCredential(Base):
    """UniFi credential storage (encrypted)"""
    __tablename__ = "unifi_credentials"
    
    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, index=True, nullable=True)  # Optional org association
    site_id = Column(String, index=True, nullable=True)  # Optional site association
    name = Column(String, nullable=False)  # User-friendly name
    credential_type = Column(String, nullable=False)  # 'local' or 'cloud'
    
    # Connection details
    host = Column(String, nullable=True)  # For local controllers
    port = Column(Integer, default=443)
    
    # Encrypted credentials
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)  # Should be encrypted in production
    api_key = Column(String, nullable=True)  # For cloud API
    
    # UniFi site information
    unifi_site = Column(String, default="default")  # UniFi site name
    
    # SSL verification
    verify_ssl = Column(Integer, default=1)
    
    # Additional settings
    extra_data = Column(JSON, nullable=True)
    
    # Status tracking
    enabled = Column(Integer, default=1)
    last_test = Column(DateTime, nullable=True)
    last_test_status = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

