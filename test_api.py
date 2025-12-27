import requests
from datetime import date, timedelta
from app.db.session import SessionLocal
from app.models.allmodels import User, Transaction
import uuid

BASE_URL = "http://localhost:8000"

# 1. Create test user and transactions in DB
def seed_test_data():
    db = SessionLocal()
    
    user_id = uuid.uuid4()
    user = User(id=user_id, email="test@example.com")
    db.add(user)
    
    # Create 6 small Starbucks purchases (triggers LATTE_FACTOR)
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
    
    db.commit()
    print(f"✅ Created test user: {user_id}")
    db.close()
    return str(user_id)

# 2. Test pattern detection
def test_patterns(user_id):
    print("\n🔍 Testing pattern detection...")
    response = requests.post(f"{BASE_URL}/api/v1/patterns/scan/{user_id}")
    patterns = response.json()
    print(f"✅ Found {len(patterns)} patterns")
    return patterns[0]['id'] if patterns else None

# 3. Test question generation
def test_question(pattern_id, user_id):
    print("\n❓ Testing question generation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/learning/generate-question/{pattern_id}",
        params={"user_id": user_id}
    )
    data = response.json()
    print(f"✅ Question: {data['question_text']}")
    print(f"📚 Explanation: {data['explanation']}")
    return data['question_id']

# 4. Test answer submission
def test_answer(question_id, user_id):
    print("\n💬 Testing answer submission...")
    response = requests.post(
        f"{BASE_URL}/api/v1/learning/submit-answer",
        params={"user_id": user_id},
        json={
            "question_id": question_id,
            "answer_text": "I realize I'm spending on coffee without thinking about long-term goals. It's become a habit when I'm stressed."
        }
    )
    print(f"✅ {response.json()['message']}")

if __name__ == "__main__":
    user_id = seed_test_data()
    pattern_id = test_patterns(user_id)
    
    if pattern_id:
        question_id = test_question(pattern_id, user_id)
        test_answer(question_id, user_id)
    
    print("\n All tests passed!")