from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.allmodels import User, Transaction
from datetime import date, timedelta
import uuid

router = APIRouter()

__all__ = ['router']

@router.post("/create-user")
def create_test_user(db: Session = Depends(get_db)):
    """Create test user with sample transactions"""
    
    user_id = uuid.uuid4()
    user = User(id=user_id, email=f"test_{user_id}@example.com")
    db.add(user)
    db.flush()  # Commit user first before adding transactions
    
    # Create 6 Starbucks purchases (triggers LATTE_FACTOR)
    today = date.today()
    for i in range(6):
        tx = Transaction(
            user_id=user_id,
            date=today - timedelta(days=i*3),
            merchant="Starbucks",
            amount=5.50,
            verified=True
        )
        db.add(tx)
    
    # Create impulse cluster (5 purchases same day)
    for i in range(5):
        tx = Transaction(
            user_id=user_id,
            date=today - timedelta(days=10),
            merchant=["Amazon", "Zara", "Swiggy", "BookMyShow", "Uber"][i],
            amount=[150, 200, 80, 120, 90][i],
            verified=True
        )
        db.add(tx)
    
    db.commit()
    
    return {
        "user_id": str(user_id),
        "transactions_count": 11,
        "message": "Test data created successfully"
    }