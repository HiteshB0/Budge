from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime

class PatternBase(BaseModel):
    pattern_code: str  
    bias_mapping: str 
    details: Dict[str, Any] 
    trigger_transaction_ids: List[UUID]

class DetectedPatternCreate(PatternBase):
    pass

class DetectedPatternResponse(PatternBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True