from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.allmodels import User, Transaction, Snapshot
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import uuid

router = APIRouter()

class TransactionCreate(BaseModel):
    user_id: str
    date: date
    merchant: str
    amount: float
    category: Optional[str] = None

class TransactionResponse(BaseModel):
    id: uuid.UUID
    date: date
    merchant: str
    amount: float
    category: Optional[str]
    
    class Config:
        orm_mode = True

class DashboardStats(BaseModel):
    total_spent: float
    tx_count: int
    top_category: Optional[str]
    category_breakdown: dict

@router.post("/", response_model=TransactionResponse)
def add_transaction(
    tx: TransactionCreate,
    db: Session = Depends(get_db)
):
    # Ensure user exists (hacky check for demo)
    user_uuid =  uuid.UUID(tx.user_id)
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        # Auto-create if not exists for demo flow
        user = User(id=user_uuid, email=f"demo_{tx.user_id}@budge.app")
        db.add(user)
        db.commit()
    
    db_tx = Transaction(
        user_id=user_uuid,
        snapshot_id=None, # Manual entry
        date=tx.date,
        merchant=tx.merchant,
        amount=tx.amount,
        category=tx.category,
        verified=True
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

@router.get("/{user_id}", response_model=List[TransactionResponse])
def get_transactions(
    user_id: str,
    db: Session = Depends(get_db)
):
    try:
        uid = uuid.UUID(user_id)
        return db.query(Transaction).filter(Transaction.user_id == uid).order_by(Transaction.date.desc()).all()
    except ValueError:
        return []

@router.get("/{user_id}/stats", response_model=DashboardStats)
def get_dashboard_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    try:
        uid = uuid.UUID(user_id)
        txs = db.query(Transaction).filter(Transaction.user_id == uid).all()
        
        total = sum(t.amount for t in txs)
        count = len(txs)
        
        # Category breakdown
        breakdown = {}
        for t in txs:
            cat = t.category or "Uncategorized"
            breakdown[cat] = breakdown.get(cat, 0) + t.amount
            
        top_cat = max(breakdown, key=breakdown.get) if breakdown else None
        
        return {
            "total_spent": total,
            "tx_count": count,
            "top_category": top_cat,
            "category_breakdown": breakdown
        }
    except Exception as e:
        print(f"Stats error: {e}")
        return {
            "total_spent": 0,
            "tx_count": 0,
            "top_category": None,
            "category_breakdown": {}
        }
