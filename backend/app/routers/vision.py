"""
Kestrel Vision — Chart Scanning Router
Upload chart images for AI-driven pattern analysis.
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.core.config import settings
from app.core.security import get_current_user_id
from app.services.shield.audit import log_action

router = APIRouter(prefix="/api/vision", tags=["Vision"])


@router.post("/analyze")
async def analyze_chart(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a chart image for AI analysis.
    Returns detected patterns, support/resistance levels, and confidence scores.
    """
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/webp", "image/bmp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    
    # Validate file size
    contents = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB.")
    
    # Save file
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if file.filename else "png"
    filepath = os.path.join(settings.UPLOAD_DIR, f"{file_id}.{ext}")
    with open(filepath, "wb") as f:
        f.write(contents)
    
    from app.services.vision.pipeline import vision_pipeline
    analysis_result = vision_pipeline.analyze_image(contents, file.filename or "chart.png")
    analysis_result["id"] = file_id
    
    # Audit log
    await log_action(
        db, "vision_scan", user_id,
        {"file_id": file_id, "patterns_found": len(analysis_result["detected_patterns"])},
    )
    
    return analysis_result
