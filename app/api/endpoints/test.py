from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.allmodels import User, Transaction
from datetime import date, timedelta
import uuid

router = APIRouter()

@router.post("/create-user")
def create_test_user(db: Session = Depends(get_db)):
    """Create test user with realistic spending patterns"""
    
    user_id = uuid.uuid4()
    user = User(id=user_id, email=f"test_{user_id}@example.com")
    db.add(user)
    db.flush()
    
    today = date.today()
    transactions = []
    
    # Pattern 1: LATTE_FACTOR - Daily Starbucks (10 purchases, all under $20)
    for i in range(10):
        transactions.append(Transaction(
            user_id=user_id,
            date=today - timedelta(days=i*2),
            merchant="Starbucks",
            amount=5.75,
            verified=True
        ))
    
    # Pattern 1: More small purchases at different cafe
    for i in range(8):
        transactions.append(Transaction(
            user_id=user_id,
            date=today - timedelta(days=i*3 + 1),
            merchant="Cafe Coffee Day",
            amount=4.50,
            verified=True
        ))
    
    # Pattern 2: IMPULSE_CLUSTER - Stress shopping day (7 purchases same day)
    stress_day = today - timedelta(days=15)
    impulse_purchases = [
        ("Amazon", 89.99),
        ("Flipkart", 156.50),
        ("Myntra", 230.00),
        ("Swiggy", 45.00),
        ("Zomato", 38.50),
        ("BookMyShow", 120.00),
        ("Uber", 25.00),
    ]
    
    for merchant, amount in impulse_purchases:
        transactions.append(Transaction(
            user_id=user_id,
            date=stress_day,
            merchant=merchant,
            amount=amount,
            verified=True
        ))
    
    # Some normal larger purchases (won't trigger patterns)
    transactions.append(Transaction(
        user_id=user_id,
        date=today - timedelta(days=20),
        merchant="Grocery Store",
        amount=150.00,
        verified=True
    ))
    
    transactions.append(Transaction(
        user_id=user_id,
        date=today - timedelta(days=25),
        merchant="Gas Station",
        amount=80.00,
        verified=True
    ))
    
    for tx in transactions:
        db.add(tx)
    
    db.commit()
    
    return {
        "user_id": str(user_id),
        "transactions_count": len(transactions),
        "patterns_expected": 3,
        "details": {
            "latte_factor_starbucks": 10,
            "latte_factor_ccd": 8,
            "impulse_cluster": 7
        }
    }