from sqlalchemy.orm import Session
from typing import List
from collections import defaultdict
from app.models.allmodels import Transaction, DetectedPattern
from app.schemas.patterns import DetectedPatternCreate
import uuid
from datetime import timedelta

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
    
    if not txs:
        return []

    new_patterns = []

    # 1. Latte Factor (Small frequent purchases)
    merchant_counts = defaultdict(list)
    for tx in txs:
        if tx.amount < 25.0:
            merchant_counts[tx.merchant].append(tx)
    
    for merchant, merchant_txs in merchant_counts.items():
        if len(merchant_txs) >= 3:
            total_spent = sum(t.amount for t in merchant_txs)
            new_patterns.append(DetectedPatternCreate(
                pattern_code="LATTE_FACTOR",
                bias_mapping="PRESENT_BIAS",
                details={
                    "merchant": merchant, 
                    "count": len(merchant_txs), 
                    "total_spent": total_spent,
                    "avg_amount": total_spent/len(merchant_txs)
                },
                trigger_transaction_ids=[t.id for t in merchant_txs]
            ))

    # 2. Impulse Cluster (Crowded spending days)
    date_counts = defaultdict(list)
    for tx in txs:
        date_counts[tx.date].append(tx)
        
    for date_obj, day_txs in date_counts.items():
        if len(day_txs) >= 4:
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

    # 3. Big Splurge (High value single purchase)
    for tx in txs:
        if tx.amount > 150.0 and tx.category in ["Shopping", "Entertainment", "Electronics"]:
            new_patterns.append(DetectedPatternCreate(
                pattern_code="BIG_SPLURGE",
                bias_mapping="ANCHORING", # Often result of sales/anchoring
                details={
                    "merchant": tx.merchant,
                    "amount": tx.amount,
                    "date": str(tx.date)
                },
                trigger_transaction_ids=[tx.id]
            ))

    # 4. Subscription Trap (Recurring amounts)
    # Group by (Merchant, Amount)
    sub_counts = defaultdict(list)
    for tx in txs:
        sub_counts[(tx.merchant, tx.amount)].append(tx)
    
    for (merch, amt), sub_txs in sub_counts.items():
        if len(sub_txs) >= 2 and amt > 10.0:
            # Check if dates are somewhat spaced (e.g. > 20 days) for monthly
            # For demo, just recurrence is enough
            new_patterns.append(DetectedPatternCreate(
                pattern_code="SUBSCRIPTION_TRAP",
                bias_mapping="SUNK_COST",
                details={
                    "merchant": merch,
                    "amount": amt,
                    "frequency": "recurring"
                },
                trigger_transaction_ids=[t.id for t in sub_txs]
            ))

    # Clear old patterns (Simpler for demo than deduplication)
    db.query(DetectedPattern).filter(DetectedPattern.user_id == user_uuid).delete()
    db.flush()

    # Save patterns
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
    for pat in saved_patterns:
        db.refresh(pat)
    
    return saved_patterns