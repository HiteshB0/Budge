import json
import os
import requests
from typing import Dict
from sqlalchemy.orm import Session

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Static concept definitions as fallback/context
CONCEPTS_DB = {
    "PRESENT_BIAS": {
        "id": "present_bias",
        "title": "Present Bias",
        "definition": "Overvaluing immediate rewards at the expense of long-term goals."
    },
    "EMOTIONAL_SPENDING": {
        "id": "emotional_spending",
        "title": "Emotional Spending",
        "definition": "Using spending to manage emotions rather than for utility."
    },
    "ANCHORING": {
        "id": "anchoring",
        "title": "Anchoring Bias",
        "definition": "Relying too heavily on the first piece of information (like a sale price)."
    },
    "SUNK_COST": {
        "id": "sunk_cost",
        "title": "Sunk Cost Fallacy",
        "definition": "Continuing to pay for something because of past investment, not future value."
    }
}

class RAGService:
    def __init__(self):
        pass
    
    def retrieve_relevant_concept(self, db: Session, bias_mapping: str, pattern_details: Dict) -> Dict:
        """Find best matching concept for a detected pattern"""
        # Simple lookup for now since we have a direct mapping
        # bias_mapping from pattern_engine matches keys in CONCEPTS_DB
        return CONCEPTS_DB.get(bias_mapping, {
            "id": "unknown", 
            "title": bias_mapping, 
            "definition": "A financial behavioral pattern."
        })

    def get_explanation(self, concept: Dict, pattern_details: Dict) -> str:
        """Generate personalized explanation using Groq"""
        
        prompt = f"""You are a friendly financial coach.
        
Concept: {concept['title']}
Definition: {concept['definition']}
User Pattern Data: {json.dumps(pattern_details)}

Task: Write a 2-sentence explanation for the user about why this pattern matters.
- Be specific to their data (mention amounts/merchants).
- Be non-judgmental but insightful.
- Do NOT use markdown.
"""

        try:
            if not GROQ_API_KEY:
                return f"{concept['title']}: {concept['definition']} (AI unavailable)"

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"Groq Error: {response.text}")
                return f"{concept['title']}: {concept['definition']}"
                
        except Exception as e:
            print(f"RAG Error: {e}")
            return f"{concept['title']}: {concept['definition']}"

rag_service = RAGService()