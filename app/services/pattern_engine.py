from sqlalchemy.orm import Session
from typing import List
from collections import defaultdict
from app.models.allmodels import Transaction, DetectedPattern
from app.schemas.patterns import DetectedPatternCreate
import uuid

def run_pattern_scan(db: Session, user_id: str) -> List[DetectedPattern]:
    # Convert string to UUID for query
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return []
    
    txs = db.query(Transaction).filter(
        Transaction.user_id == user_uuid, 
        Transaction.verified == True
    ).order_by(Transaction.date.asc()).all()
    
    print(f"Found {len(txs)} transactions for user {user_id}")
    
    if not txs:
        return []

    new_patterns = []

    # Pattern 1: LATTE_FACTOR (small recurring purchases)
    merchant_counts = defaultdict(list)
    for tx in txs:
        if tx.amount < 20.0:
            merchant_counts[tx.merchant].append(tx)
    
    for merchant, merchant_txs in merchant_counts.items():
        if len(merchant_txs) >= 5:
            new_patterns.append(DetectedPatternCreate(
                pattern_code="LATTE_FACTOR",
                bias_mapping="PRESENT_BIAS",
                details={
                    "merchant": merchant, 
                    "count": len(merchant_txs), 
                    "avg_amount": sum(t.amount for t in merchant_txs)/len(merchant_txs)
                },
                trigger_transaction_ids=[t.id for t in merchant_txs]
            ))

    # Pattern 2: IMPULSE_CLUSTER (many purchases on same day)
    date_counts = defaultdict(list)
    for tx in txs:
        date_counts[tx.date].append(tx)
        
    for date_obj, day_txs in date_counts.items():
        if len(day_txs) >= 5:
            new_patterns.append(DetectedPatternCreate(
                pattern_code="IMPULSE_CLUSTER",
                bias_mapping="EMOTIONAL_SPENDING", 
                details={
                    "date": str(date_obj), 
                    "count": len(day_txs), 
                    "total_spent": sum(t.amount for t in day_txs)
                },
                trigger_transaction_ids=[t.id for t in day_txs]
            ))

    print(f"Detected {len(new_patterns)} patterns")

    # Save patterns to database
    saved_patterns = []
    for p in new_patterns:
        db_pat = DetectedPattern(
            user_id=user_uuid,
            pattern_code=p.pattern_code,
            bias_mapping=p.bias_mapping,
            details=p.details,
            trigger_transaction_ids=p.trigger_transaction_ids
        )
        db.add(db_pat)
        saved_patterns.append(db_pat)
    
    db.commit()
    
    # Refresh to get IDs
    for pat in saved_patterns:
        db.refresh(pat)
    
    return saved_patterns