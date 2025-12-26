from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from datetime import timedelta
from collections import defaultdict
from app.models.allmodels import Transaction, DetectedPattern
from app.schemas.patterns import DetectedPatternCreate

def run_pattern_scan(db: Session, user_id: str) -> List[DetectedPattern]:
    txs = db.query(Transaction).filter(
        Transaction.user_id == user_id, 
        Transaction.verified == True
    ).order_by(Transaction.date.asc()).all()
    
    if not txs:
        return []

    new_patterns = []

    merchant_counts = defaultdict(list)
    for tx in txs:
        if tx.amount < 20.0:
            merchant_counts[tx.merchant].append(tx)
    
    for merchant, merchant_txs in merchant_counts.items():
        if len(merchant_txs) >= 5:
            new_patterns.append(DetectedPatternCreate(
                pattern_code="LATTE_FACTOR",
                bias_mapping="PRESENT_BIAS",
                details={"merchant": merchant, "count": len(merchant_txs), "avg_amount": sum(t.amount for t in merchant_txs)/len(merchant_txs)},
                trigger_transaction_ids=[t.id for t in merchant_txs]
            ))

    date_counts = defaultdict(list)
    for tx in txs:
        date_counts[tx.date].append(tx)
        
    for date_obj, day_txs in date_counts.items():
        if len(day_txs) >= 5:
            new_patterns.append(DetectedPatternCreate(
                pattern_code="IMPULSE_CLUSTER",
                bias_mapping="EMOTIONAL_SPENDING", 
                details={"date": str(date_obj), "count": len(day_txs), "total_spent": sum(t.amount for t in day_txs)},
                trigger_transaction_ids=[t.id for t in day_txs]
            ))

    saved_patterns = []
    for p in new_patterns:
        db_pat = DetectedPattern(
            user_id=user_id,
            pattern_code=p.pattern_code,
            bias_mapping=p.bias_mapping,
            details=p.details,
            trigger_transaction_ids=p.trigger_transaction_ids
        )
        db.add(db_pat)
        saved_patterns.append(db_pat)
    
    db.commit()
    return saved_patterns