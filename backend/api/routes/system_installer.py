"""
System Installer API
Install Python dependencies and manage system packages
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import subprocess
import sys
import os
import asyncio
import logging
from typing import Optional, List
from pathlib import Path

router = APIRouter()
logger = logging.getLogger('overwatch.system.installer')

# Track installation progress
installation_status = {}


class InstallRequest(BaseModel):
    package: str
    version: Optional[str] = None


class DatabaseCreateRequest(BaseModel):
    path: str


@router.post("/install-dependency")
async def install_dependency(request: InstallRequest, background_tasks: BackgroundTasks):
    """
    Install a Python package using pip
    Runs in background and provides status updates
    """
    package = request.package
    version = request.version

    # Validate package name
    allowed_packages = {
        'deepface', 'easyocr', 'openai-whisper', 'whisper',
        'tensorflow', 'tensorflow-hub', 'torch', 'torchvision', 
        'torchaudio', 'panns-inference', 'yt-dlp'
    }

    if package not in allowed_packages:
        raise HTTPException(
            status_code=400,
            detail=f"Package '{package}' is not in the allowed list for installation"
        )

    # Create install ID
    install_id = f"{package}-{os.urandom(4).hex()}"

    # Start installation in background
    background_tasks.add_task(run_pip_install, install_id, package, version)

    return {
        "status": "started",
        "install_id": install_id,
        "package": package,
        "message": f"Installation of {package} started in background"
    }


@router.get("/install-status/{install_id}")
async def get_install_status(install_id: str):
    """Get status of a package installation"""
    if install_id not in installation_status:
        raise HTTPException(status_code=404, detail="Installation not found")

    return installation_status[install_id]


@router.get("/install-status")
async def get_all_install_status():
    """Get status of all installations"""
    return {
        "installations": installation_status
    }


async def run_pip_install(install_id: str, package: str, version: Optional[str] = None):
    """
    Run pip install in subprocess
    Updates installation_status with progress
    """
    # Initialize status
    installation_status[install_id] = {
        "package": package,
        "status": "installing",
        "progress": 0,
        "output": [],
        "error": None
    }

    try:
        # Build pip command
        package_spec = f"{package}=={version}" if version else package
        cmd = [sys.executable, "-m", "pip", "install", package_spec]

        logger.info(f"Running: {' '.join(cmd)}")

        # Run pip install
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Stream output
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_str = line.decode('utf-8').strip()
            if line_str:
                installation_status[install_id]["output"].append(line_str)
                logger.info(f"[{package}] {line_str}")

        # Wait for completion
        await process.wait()

        if process.returncode == 0:
            installation_status[install_id]["status"] = "completed"
            installation_status[install_id]["progress"] = 100
            logger.info(f"Successfully installed {package}")
        else:
            # Get error output
            stderr = await process.stderr.read()
            error_msg = stderr.decode('utf-8')

            installation_status[install_id]["status"] = "failed"
            installation_status[install_id]["error"] = error_msg
            logger.error(f"Failed to install {package}: {error_msg}")

    except Exception as e:
        installation_status[install_id]["status"] = "failed"
        installation_status[install_id]["error"] = str(e)
        logger.error(f"Exception during installation of {package}: {e}")


@router.post("/face-recognition/create-database")
async def create_face_database(request: DatabaseCreateRequest):
    """Create face recognition database directory"""
    try:
        # Validate path (must be relative and within data/)
        db_path = Path(request.path)

        # Ensure it's relative
        if db_path.is_absolute():
            raise HTTPException(
                status_code=400,
                detail="Path must be relative to backend directory"
            )

        # Ensure it starts with data/
        if not str(db_path).startswith('data/'):
            raise HTTPException(
                status_code=400,
                detail="Face database must be within data/ directory"
            )

        # Create directory
        db_path.mkdir(parents=True, exist_ok=True)

        # Create a README
        readme_path = db_path / "README.md"
        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write("""# Face Recognition Database

## Structure

Create one folder per person:
```
data/faces/
├── john_doe/
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── photo3.jpg
├── jane_smith/
│   ├── image1.jpg
│   └── image2.jpg
└── ...
```

## Guidelines

1. **Folder naming**: Use person's name (lowercase, underscores for spaces)
2. **Image format**: JPG or PNG
3. **Image quality**: Clear, well-lit face photos
4. **Multiple angles**: Add 3-5 photos per person for better recognition
5. **Face size**: Face should be clearly visible (at least 100x100 pixels)

## Usage

The folder name becomes the person's identity in the recognition system.
Example: `data/faces/john_doe/` → Person identified as "john_doe"
""")

        return {
            "status": "success",
            "path": str(db_path),
            "message": f"Database directory created at {db_path}",
            "readme_created": True
        }

    except Exception as e:
        logger.error(f"Failed to create face database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-package")
async def check_package(package: str):
    """Check if a package is installed"""
    try:
        __import__(package)
        return {
            "package": package,
            "installed": True
        }
    except ImportError:
        return {
            "package": package,
            "installed": False
        }


@router.get("/installed-packages")
async def get_installed_packages():
    """Get list of installed optional packages"""
    packages_to_check = [
        'deepface', 'easyocr', 'whisper', 'tensorflow', 
        'tensorflow_hub', 'torch', 'panns_inference', 'yt_dlp'
    ]

    installed = {}
    for package in packages_to_check:
        try:
            __import__(package)
            installed[package] = True
        except ImportError:
            installed[package] = False

    return {
        "packages": installed,
        "summary": {
            "total_checked": len(packages_to_check),
            "installed": sum(installed.values()),
            "missing": len(packages_to_check) - sum(installed.values())
        }
    }

