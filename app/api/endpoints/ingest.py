from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
# from app.services import ocr
from app.models.allmodels import User, Transaction, Snapshot
from datetime import datetime
import uuid
import json

router = APIRouter()

@router.post("/upload")
async def upload_screenshot(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    """(OCR Temporarily Disabled) Upload bank statement"""
    
    # Read image (but don't process)
    _ = await file.read()
    
    return {
        "status": "disabled",
        "message": "OCR feature is currently disabled due to API library conflict. Please use Manual Input.",
        "transactions_found": 0,
        "extracted_data": {"transactions": []}
    }