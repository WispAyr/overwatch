"""
Organizational Hierarchy Loader
Loads and manages organization/site/sublocation structure
"""
import logging
from pathlib import Path
from typing import Dict, List

import yaml
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, Organization, Site, Sublocation, Camera


logger = logging.getLogger('overwatch.hierarchy')


class HierarchyLoader:
    """Loads organizational hierarchy from configuration"""
    
    def __init__(self):
        self.config_path = Path(settings.CONFIG_DIR) / "hierarchy.yaml"
        
    async def load_hierarchy(self):
        """Load complete hierarchy from config file"""
        if not self.config_path.exists():
            logger.warning(f"Hierarchy config not found: {self.config_path}")
            logger.info("Using example config...")
            self.config_path = Path(settings.CONFIG_DIR) / "hierarchy.example.yaml"
            
        if not self.config_path.exists():
            logger.warning("No hierarchy configuration found")
            return
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        db = SessionLocal()
        try:
            await self._load_organizations(config.get('organizations', []), db)
            db.commit()
            logger.info("Hierarchy loaded successfully")
        finally:
            db.close()
            
    async def _load_organizations(self, orgs: List[dict], db: Session):
        """Load organizations and their sites"""
        for org_config in orgs:
            org_id = org_config['id']
            
            # Create or update organization
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                org = Organization(
                    id=org_id,
                    name=org_config['name'],
                    description=org_config.get('description'),
                    metadata={}
                )
                db.add(org)
                logger.info(f"Created organization: {org.name}")
            else:
                org.name = org_config['name']
                org.description = org_config.get('description')
                
            # Load sites
            if 'sites' in org_config:
                await self._load_sites(org_id, org_config['sites'], db)
                
    async def _load_sites(self, org_id: str, sites: List[dict], db: Session):
        """Load sites and their sublocations"""
        for site_config in sites:
            site_id = site_config['id']
            
            # Create or update site
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site:
                site = Site(
                    id=site_id,
                    organization_id=org_id,
                    name=site_config['name'],
                    description=site_config.get('description'),
                    site_type=site_config.get('site_type', 'fixed'),
                    location=site_config.get('location', {}),
                    metadata={}
                )
                db.add(site)
                logger.info(f"Created site: {site.name} ({site.site_type})")
            else:
                site.name = site_config['name']
                site.description = site_config.get('description')
                site.site_type = site_config.get('site_type', 'fixed')
                site.location = site_config.get('location', {})
                
            # Load sublocations
            if 'sublocations' in site_config:
                await self._load_sublocations(site_id, site_config['sublocations'], db)
                
    async def _load_sublocations(
        self,
        site_id: str,
        sublocations: List[dict],
        db: Session
    ):
        """Load sublocations and their cameras"""
        for sl_config in sublocations:
            sl_id = sl_config['id']
            
            # Create or update sublocation
            sl = db.query(Sublocation).filter(Sublocation.id == sl_id).first()
            if not sl:
                sl = Sublocation(
                    id=sl_id,
                    site_id=site_id,
                    name=sl_config['name'],
                    description=sl_config.get('description'),
                    sublocation_type=sl_config.get('sublocation_type'),
                    metadata={}
                )
                db.add(sl)
                logger.info(f"Created sublocation: {sl.name}")
            else:
                sl.name = sl_config['name']
                sl.description = sl_config.get('description')
                sl.sublocation_type = sl_config.get('sublocation_type')
                
            # Load cameras
            if 'cameras' in sl_config:
                await self._load_cameras(sl_id, sl_config['cameras'], db)
                
    async def _load_cameras(
        self,
        sublocation_id: str,
        cameras: List[dict],
        db: Session
    ):
        """Load cameras"""
        for cam_config in cameras:
            cam_id = cam_config['id']
            
            # Create or update camera
            cam = db.query(Camera).filter(Camera.id == cam_id).first()
            
            # Handle multi-resolution streams
            streams = cam_config.get('streams', {})
            active_stream = cam_config.get('active_stream', 'medium')
            rtsp_url = cam_config.get('rtsp_url')
            
            # If streams defined, get URL from active stream
            if streams and active_stream in streams:
                rtsp_url = streams[active_stream]['url']
            
            if not cam:
                cam = Camera(
                    id=cam_id,
                    sublocation_id=sublocation_id,
                    name=cam_config['name'],
                    type=cam_config.get('type', 'generic'),
                    sensor_type=cam_config.get('sensor_type', 'camera'),
                    rtsp_url=rtsp_url,
                    streams=streams,
                    active_stream=active_stream,
                    enabled=cam_config.get('enabled', True),
                    workflows=cam_config.get('workflows', []),
                    settings=cam_config.get('settings', {})
                )
                db.add(cam)
                logger.info(f"Created camera: {cam.name} ({active_stream} quality)")
            else:
                cam.name = cam_config['name']
                cam.type = cam_config.get('type', 'generic')
                cam.sensor_type = cam_config.get('sensor_type', 'camera')
                cam.rtsp_url = rtsp_url
                cam.streams = streams
                cam.active_stream = active_stream
                cam.enabled = cam_config.get('enabled', True)
                cam.workflows = cam_config.get('workflows', [])
                cam.settings = cam_config.get('settings', {})
                
    async def get_hierarchy_tree(self) -> Dict:
        """Get complete hierarchy as nested dict"""
        db = SessionLocal()
        try:
            result = {'organizations': []}
            
            orgs = db.query(Organization).all()
            for org in orgs:
                org_dict = {
                    'id': org.id,
                    'name': org.name,
                    'description': org.description,
                    'sites': []
                }
                
                sites = db.query(Site).filter(Site.organization_id == org.id).all()
                for site in sites:
                    site_dict = {
                        'id': site.id,
                        'name': site.name,
                        'site_type': site.site_type,
                        'location': site.location,
                        'sublocations': []
                    }
                    
                    sls = db.query(Sublocation).filter(Sublocation.site_id == site.id).all()
                    for sl in sls:
                        sl_dict = {
                            'id': sl.id,
                            'name': sl.name,
                            'sublocation_type': sl.sublocation_type,
                            'cameras': []
                        }
                        
                        cams = db.query(Camera).filter(Camera.sublocation_id == sl.id).all()
                        for cam in cams:
                            sl_dict['cameras'].append({
                                'id': cam.id,
                                'name': cam.name,
                                'type': cam.type,
                                'sensor_type': cam.sensor_type,
                                'enabled': bool(cam.enabled)
                            })
                            
                        site_dict['sublocations'].append(sl_dict)
                        
                    org_dict['sites'].append(site_dict)
                    
                result['organizations'].append(org_dict)
                
            return result
        finally:
            db.close()

