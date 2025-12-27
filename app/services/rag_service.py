import json
import os
from typing import Dict
import requests
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.allmodels import ConceptEmbedding

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

CONCEPTS_JSON = {
    "concepts": [
        {
            "id": "present_bias",
            "title": "Present Bias",
            "definition": "The tendency to overvalue immediate rewards while undervaluing future benefits. This leads to choosing smaller immediate pleasures over larger delayed rewards.",
            "examples": [
                "Buying daily coffee ($5) instead of investing that money ($150/month)",
                "Choosing convenient expensive food over meal planning",
                "Impulse purchases that provide instant gratification"
            ]
        },
        {
            "id": "mental_accounting",
            "title": "Mental Accounting",
            "definition": "Treating money differently based on its source or intended use, rather than recognizing all money has equal value.",
            "examples": [
                "Spending bonus money frivolously while being frugal with salary",
                "Keeping savings account while carrying credit card debt",
                "Spending gift cards immediately but saving cash carefully"
            ]
        },
        {
            "id": "anchoring",
            "title": "Anchoring Bias",
            "definition": "Over-relying on the first piece of information (the 'anchor') when making decisions, even if it's irrelevant.",
            "examples": [
                "Judging value based on 'original price' during sales",
                "Using credit card limit as spending guideline",
                "Comparing purchases to one expensive item to justify others"
            ]
        },
        {
            "id": "emotional_spending",
            "title": "Emotional Spending",
            "definition": "Making purchases to regulate emotions (stress, boredom, sadness) rather than for the item's utility.",
            "examples": [
                "Shopping when stressed or anxious",
                "Buying things when bored or lonely",
                "Retail therapy after bad news"
            ]
        },
        {
            "id": "sunk_cost",
            "title": "Sunk Cost Fallacy",
            "definition": "Continuing to invest in something because of past investment, even when it's not rational to continue.",
            "examples": [
                "Paying for unused gym membership because 'already paid'",
                "Keeping subscription services 'just in case'",
                "Finishing expensive food when already full"
            ]
        }
    ]
}

class RAGService:
    def __init__(self):
        self.knowledge_base = CONCEPTS_JSON
    
    def initialize_embeddings(self, db: Session):
        """No embeddings needed with simple mapping"""
        print(f"✓ Using {len(self.knowledge_base['concepts'])} concepts")
    
    def retrieve_relevant_concept(
        self, 
        db: Session, 
        bias_mapping: str,
        pattern_details: Dict
    ) -> Dict:
        """Find best matching concept for a detected pattern"""
        
        for concept in self.knowledge_base["concepts"]:
            if concept["id"] == bias_mapping.lower():
                return concept
        
        # Fallback to present_bias
        return self.knowledge_base["concepts"][0]
    
    def get_explanation(self, concept: Dict, pattern_details: Dict) -> str:
        """Generate personalized explanation"""
        
        prompt = f"""You are a financial education assistant. Explain this concept to someone who just discovered this pattern in their spending.

Concept: {concept['title']}
Definition: {concept['definition']}

User's Pattern: {pattern_details}

Instructions:
- Use the specific numbers from their pattern
- Connect the concept to their actual behavior
- Be conversational and non-judgmental
- Keep it under 100 words
- Do NOT give advice like "you should stop" or "try to save"
- Instead, help them understand WHY this happens

Your explanation:"""
        
        try:
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
                    "max_tokens": 200
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                return f"{concept['title']}: {concept['definition']}"
                
        except Exception as e:
            print(f"Groq API error: {e}")
            return f"{concept['title']}: {concept['definition']}"

rag_service = RAGService()