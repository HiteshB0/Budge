from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.pattern_engine import run_pattern_scan
from app.schemas.patterns import DetectedPatternResponse

router = APIRouter()

@router.post("/scan/{user_id}", response_model=List[DetectedPatternResponse])
def scan_user_patterns(user_id: str, db: Session = Depends(get_db)):
    patterns = run_pattern_scan(db, user_id)
    return patterns