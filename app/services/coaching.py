import os
from google import genai
from app.models.all_models import DetectedPattern, ReflectionSession
from app.services.knowledge_base import get_bias_context
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

def generate_coaching_question(db: Session, pattern_id: str):
    # 1. Fetch Pattern
    pattern = db.query(DetectedPattern).filter(DetectedPattern.id == pattern_id).first()
    if not pattern:
        return None

    # 2. Retrieve Context
    bias_info = get_bias_context(pattern.bias_mapping)

    # 3. Construct Prompt
    prompt = f"""
    You are a compassionate financial therapist. 
    CONTEXT: The user has triggered the pattern "{pattern.pattern_code}" which relates to "{bias_info['name']}".
    DEFINITION: {bias_info['definition']}
    DATA: {pattern.details}
    
    TASK: Generate ONE single, short, open-ended reflection question (max 20 words).
    GOAL: Help them realize *why* they did this, without judging them.
    DO NOT give advice. DO NOT start with "Why". Use "How" or "What".
    """

    try:
        # 4. Initialize Client & Call Model
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        question_text = response.text.strip()

        # 5. Save Session
        session = ReflectionSession(
            pattern_id=pattern.id,
            ai_question=question_text
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    except Exception as e:
        print(f"Coaching Generation Error: {e}")
        return None