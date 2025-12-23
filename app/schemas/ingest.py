from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class TransactionDraft(BaseModel):
    date: str = Field(..., description="ISO 8601 format YYYY-MM-DD")
    merchant: str = Field(..., description="Cleaned merchant name (e.g., 'Apple' not 'APPLE #1234')")
    amount: float
    currency: str = "INR"
    confidence_flag: bool = Field(True, description="False if unsure OCR")

class ExtractedReceipt(BaseModel):
    transactions: List[TransactionDraft]
    total_amount_check: Optional[float] = Field(None, description="Sum of items if visible")