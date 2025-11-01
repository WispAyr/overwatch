"""
Device Manager
Handles device updates, configuration, and system management
"""
import asyncio
import logging
import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from models.device_config import DeviceConfig


logger = logging.getLogger('overwatch.device')


class DeviceManager:
    """Manages device updates and configuration"""
    
    def __init__(self, config: DeviceConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent.parent
        self._update_lock = asyncio.Lock()
        self._last_update_check: Optional[datetime] = None
        self._update_available: Optional[Dict[str, Any]] = None
    
    async def check_for_updates(self) -> Dict[str, Any]:
        """Check if updates are available from GitHub"""
        async with self._update_lock:
            try:
                branch = self.config.get_branch_for_device()
                
                # Fetch latest from origin
                result = await self._run_command(
                    ['git', 'fetch', 'origin', branch],
                    cwd=self.project_root
                )
                
                if result['returncode'] != 0:
                    logger.error(f"Failed to fetch updates: {result['stderr']}")
                    return {
                        'available': False,
                        'error': result['stderr']
                    }
                
                # Check if we're behind
                result = await self._run_command(
                    ['git', 'rev-list', '--count', f'HEAD..origin/{branch}'],
                    cwd=self.project_root
                )
                
                if result['returncode'] != 0:
                    return {
                        'available': False,
                        'error': result['stderr']
                    }
                
                commits_behind = int(result['stdout'].strip() or '0')
                
                # Get current commit
                current_commit = await self._get_current_commit()
                
                # Get latest remote commit
                result = await self._run_command(
                    ['git', 'rev-parse', f'origin/{branch}'],
                    cwd=self.project_root
                )
                latest_commit = result['stdout'].strip() if result['returncode'] == 0 else None
                
                self._last_update_check = datetime.utcnow()
                self._update_available = {
                    'available': commits_behind > 0,
                    'commits_behind': commits_behind,
                    'current_commit': current_commit,
                    'latest_commit': latest_commit,
                    'branch': branch,
                    'checked_at': self._last_update_check.isoformat()
                }
                
                return self._update_available
                
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                return {
                    'available': False,
                    'error': str(e)
                }
    
    async def apply_update(self, restart: bool = False) -> Dict[str, Any]:
        """Apply available updates from GitHub"""
        async with self._update_lock:
            try:
                branch = self.config.get_branch_for_device()
                
                logger.info(f"Applying updates from branch: {branch}")
                
                # Stash any local changes
                await self._run_command(
                    ['git', 'stash'],
                    cwd=self.project_root
                )
                
                # Pull latest changes
                result = await self._run_command(
                    ['git', 'pull', 'origin', branch],
                    cwd=self.project_root
                )
                
                if result['returncode'] != 0:
                    logger.error(f"Failed to pull updates: {result['stderr']}")
                    return {
                        'success': False,
                        'error': result['stderr']
                    }
                
                # Update Python dependencies
                pip_result = await self._run_command(
                    ['pip', 'install', '-r', 'requirements.txt'],
                    cwd=self.project_root
                )
                
                # Update npm dependencies if package.json exists
                npm_result = {'returncode': 0}
                if (self.project_root / 'package.json').exists():
                    npm_result = await self._run_command(
                        ['npm', 'install'],
                        cwd=self.project_root
                    )
                
                new_commit = await self._get_current_commit()
                
                response = {
                    'success': True,
                    'commit': new_commit,
                    'branch': branch,
                    'pip_updated': pip_result['returncode'] == 0,
                    'npm_updated': npm_result['returncode'] == 0,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                if restart:
                    response['restart_scheduled'] = True
                    asyncio.create_task(self._schedule_restart())
                
                return response
                
            except Exception as e:
                logger.error(f"Error applying update: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
    
    async def _schedule_restart(self, delay: int = 5):
        """Schedule a system restart"""
        logger.info(f"Scheduling restart in {delay} seconds...")
        await asyncio.sleep(delay)
        
        # Use the restart script if available
        restart_script = self.project_root / 'restart-all.sh'
        if restart_script.exists():
            subprocess.Popen(['bash', str(restart_script)])
        else:
            # Fallback: just exit and let systemd/supervisor restart
            os._exit(0)
    
    async def _get_current_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        result = await self._run_command(
            ['git', 'rev-parse', 'HEAD'],
            cwd=self.project_root
        )
        
        if result['returncode'] == 0:
            return result['stdout'].strip()
        return None
    
    async def get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        result = await self._run_command(
            ['git', 'branch', '--show-current'],
            cwd=self.project_root
        )
        
        if result['returncode'] == 0:
            return result['stdout'].strip()
        return None
    
    async def switch_branch(self, branch: str) -> Dict[str, Any]:
        """Switch to a different branch"""
        async with self._update_lock:
            try:
                # Fetch the branch first
                await self._run_command(
                    ['git', 'fetch', 'origin', branch],
                    cwd=self.project_root
                )
                
                # Stash changes
                await self._run_command(
                    ['git', 'stash'],
                    cwd=self.project_root
                )
                
                # Checkout the branch
                result = await self._run_command(
                    ['git', 'checkout', branch],
                    cwd=self.project_root
                )
                
                if result['returncode'] != 0:
                    return {
                        'success': False,
                        'error': result['stderr']
                    }
                
                # Pull latest
                await self._run_command(
                    ['git', 'pull', 'origin', branch],
                    cwd=self.project_root
                )
                
                return {
                    'success': True,
                    'branch': branch,
                    'commit': await self._get_current_commit()
                }
                
            except Exception as e:
                logger.error(f"Error switching branch: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        import psutil
        import platform
        
        current_branch = await self.get_current_branch()
        current_commit = await self._get_current_commit()
        
        # Update device config with git info
        if self.config.info:
            self.config.info.git_branch = current_branch
            self.config.info.git_commit = current_commit
            self.config.save()
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        
        # Get network info
        network_interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:  # IPv4
                    network_interfaces.append({
                        'interface': interface,
                        'ip': addr.address
                    })
        
        return {
            'device': self.config.to_dict(),
            'system': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': disk.total,
                'disk_free': disk.free,
                'disk_percent': disk.percent
            },
            'git': {
                'branch': current_branch,
                'commit': current_commit
            },
            'network': network_interfaces,
            'update_check': self._update_available
        }
    
    async def enable_autostart(self) -> Dict[str, Any]:
        """Enable autostart on boot (systemd or cron)"""
        try:
            # Check if running on systemd
            if await self._command_exists('systemctl'):
                return await self._setup_systemd_autostart()
            else:
                return await self._setup_cron_autostart()
        except Exception as e:
            logger.error(f"Error enabling autostart: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def disable_autostart(self) -> Dict[str, Any]:
        """Disable autostart on boot"""
        try:
            if await self._command_exists('systemctl'):
                result = await self._run_command(
                    ['sudo', 'systemctl', 'disable', 'overwatch']
                )
                return {
                    'success': result['returncode'] == 0,
                    'method': 'systemd'
                }
            else:
                # Remove from crontab
                result = await self._run_command(
                    ['crontab', '-l']
                )
                
                if result['returncode'] == 0:
                    lines = result['stdout'].split('\n')
                    filtered = [l for l in lines if 'overwatch' not in l.lower()]
                    
                    # Write back
                    proc = await asyncio.create_subprocess_exec(
                        'crontab', '-',
                        stdin=asyncio.subprocess.PIPE
                    )
                    await proc.communicate('\n'.join(filtered).encode())
                    
                    return {
                        'success': True,
                        'method': 'cron'
                    }
                
                return {
                    'success': False,
                    'error': 'Could not read crontab'
                }
                
        except Exception as e:
            logger.error(f"Error disabling autostart: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _setup_systemd_autostart(self) -> Dict[str, Any]:
        """Setup systemd service for autostart"""
        service_content = f"""[Unit]
Description=Overwatch Surveillance System
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'overwatch')}
WorkingDirectory={self.project_root}
ExecStart={self.project_root}/run.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path('/etc/systemd/system/overwatch.service')
        
        try:
            # Write service file (requires sudo)
            proc = await asyncio.create_subprocess_exec(
                'sudo', 'tee', str(service_file),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await proc.communicate(service_content.encode())
            
            # Reload systemd
            await self._run_command(['sudo', 'systemctl', 'daemon-reload'])
            
            # Enable the service
            result = await self._run_command(
                ['sudo', 'systemctl', 'enable', 'overwatch']
            )
            
            return {
                'success': result['returncode'] == 0,
                'method': 'systemd',
                'service_file': str(service_file)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _setup_cron_autostart(self) -> Dict[str, Any]:
        """Setup cron job for autostart"""
        cron_line = f"@reboot cd {self.project_root} && ./run.sh\n"
        
        # Get current crontab
        result = await self._run_command(['crontab', '-l'])
        
        current_cron = result['stdout'] if result['returncode'] == 0 else ""
        
        # Check if already exists
        if 'overwatch' in current_cron.lower() or 'run.sh' in current_cron:
            return {
                'success': True,
                'method': 'cron',
                'message': 'Already configured'
            }
        
        # Add new line
        new_cron = current_cron + cron_line
        
        # Write back
        proc = await asyncio.create_subprocess_exec(
            'crontab', '-',
            stdin=asyncio.subprocess.PIPE
        )
        
        await proc.communicate(new_cron.encode())
        
        return {
            'success': True,
            'method': 'cron'
        }
    
    async def _command_exists(self, command: str) -> bool:
        """Check if a command exists"""
        result = await self._run_command(['which', command])
        return result['returncode'] == 0
    
    async def _run_command(
        self,
        command: list,
        cwd: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Run a shell command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"Command failed: {' '.join(command)}: {e}")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }

