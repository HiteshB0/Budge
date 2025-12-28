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
        from_attributes = True

class DashboardStats(BaseModel):
    total_spent: float
    tx_count: int
    top_category: Optional[str]
    category_breakdown: dict

def categorize_merchant(merchant_name: str) -> str:
    """Simple keyword-based categorization"""
    m = merchant_name.lower()
    if any(x in m for x in ['starbucks', 'coffee', 'cafe', 'restaurant', 'dining', 'burger', 'pizza', 'dunkin', 'mcdonalds']):
        return "Food & Dining"
    if any(x in m for x in ['uber', 'lyft', 'taxi', 'gas', 'shell', 'fuel', 'parking', 'metro']):
        return "Transportation"
    if any(x in m for x in ['amazon', 'shopping', 'store', 'walmart', 'target', 'myntra', 'flipkart', 'clothing']):
        return "Shopping"
    if any(x in m for x in ['netflix', 'spotify', 'movie', 'cinema', 'hulu', 'games']):
        return "Entertainment"
    if any(x in m for x in ['bill', 'utility', 'rent', 'electric', 'water', 'internet']):
        return "Bills & Utilities"
    if any(x in m for x in ['grocery', 'market', 'foods', 'trader']):
        return "Groceries"
    return "Uncategorized"

@router.post("/", response_model=TransactionResponse)
def add_transaction(
    tx: TransactionCreate,
    db: Session = Depends(get_db)
):
    # Ensure user exists (hacky check for demo)
    try:
        user_uuid =  uuid.UUID(tx.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        # Auto-create if not exists for demo flow
        user = User(id=user_uuid, email=f"demo_{tx.user_id}@budge.app")
        db.add(user)
        db.commit()
    
    # Auto-categorize if not provided
    category = tx.category
    if not category:
        category = categorize_merchant(tx.merchant)

    db_tx = Transaction(
        user_id=user_uuid,
        snapshot_id=None, # Manual entry
        date=tx.date,
        merchant=tx.merchant,
        amount=tx.amount,
        category=category,
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

@router.delete("/{user_id}")
def clear_all_transactions(user_id: str, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(user_id)
        db.query(Transaction).filter(Transaction.user_id == uid).delete()
        db.commit()
        return {"status": "success", "message": "All transactions deleted"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID")

@router.delete("/{user_id}/{tx_id}")
def delete_transaction(user_id: str, tx_id: str, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(user_id)
        tid = uuid.UUID(tx_id)
        
        tx = db.query(Transaction).filter(
            Transaction.user_id == uid,
            Transaction.id == tid
        ).first()
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
            
        db.delete(tx)
        db.commit()
        return {"status": "success", "message": "Transaction deleted"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
