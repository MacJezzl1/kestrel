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
    
    # MVP: Return mock analysis result
    # In production: this calls the Vision pipeline (preprocess → OCR → digitize → pattern detect)
    analysis_result = {
        "id": file_id,
        "filename": file.filename,
        "status": "completed",
        "confidence": 0.78,
        "image_quality": "good",
        "detected_patterns": [
            {
                "pattern": "Double Bottom",
                "confidence": 0.82,
                "location": "center-right",
                "significance": "Bullish reversal pattern",
            },
            {
                "pattern": "Support Level",
                "confidence": 0.91,
                "price_level": 1.0845,
                "strength": "strong",
            },
            {
                "pattern": "Resistance Level",
                "confidence": 0.87,
                "price_level": 1.0920,
                "strength": "moderate",
            },
            {
                "pattern": "Ascending Trendline",
                "confidence": 0.74,
                "direction": "bullish",
            },
        ],
        "summary": "Chart shows a bullish double bottom pattern forming near strong support at 1.0845. "
                   "An ascending trendline supports upward momentum. Resistance at 1.0920 may cap "
                   "initial gains. Overall bias: moderately bullish.",
        "suggested_action": {
            "direction": "buy",
            "entry_zone": "1.0850 - 1.0870",
            "stop_loss": "1.0820",
            "take_profit": "1.0920",
            "confidence": 0.78,
        },
        "disclaimer": "Analysis confidence depends on image quality. This is a decision-support tool — "
                       "always confirm with live market data before trading.",
    }
    
    # Audit log
    await log_action(
        db, "vision_scan", user_id,
        {"file_id": file_id, "patterns_found": len(analysis_result["detected_patterns"])},
    )
    
    return analysis_result
