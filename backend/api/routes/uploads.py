"""
File upload routes for workflow video/image inputs
"""
import logging
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from core.config import settings

router = APIRouter()
logger = logging.getLogger('overwatch.api.uploads')


@router.post("/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for workflow processing"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith(('video/', 'image/')):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Expected video/* or image/*"
            )
        
        # Create upload directory
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        safe_filename = file.filename.replace(" ", "_")
        file_path = upload_dir / safe_filename
        
        # If file exists, add a number to make it unique
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = upload_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # Save file
        logger.info(f"Uploading file: {safe_filename} -> {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded successfully: {file_path}")
        
        return JSONResponse({
            "status": "success",
            "filename": file_path.name,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "content_type": file.content_type
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/video/{filename}")
async def delete_video(filename: str):
    """Delete an uploaded video file"""
    try:
        file_path = Path(settings.UPLOAD_DIR) / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Ensure file is in upload directory (security check)
        if not str(file_path.resolve()).startswith(str(Path(settings.UPLOAD_DIR).resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_path.unlink()
        logger.info(f"Deleted uploaded file: {file_path}")
        
        return JSONResponse({
            "status": "success",
            "message": f"File {filename} deleted"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_uploads():
    """List all uploaded files"""
    try:
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        files = []
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })
        
        return JSONResponse({
            "status": "success",
            "files": files,
            "count": len(files)
        })
        
    except Exception as e:
        logger.error(f"List failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

