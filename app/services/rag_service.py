import json
import os
from typing import Dict
from google import genai
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.allmodels import ConceptEmbedding
from pathlib import Path

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
        self.embedding_model = "text-embedding-004"
        self.knowledge_base = CONCEPTS_JSON
    
    def initialize_embeddings(self, db: Session):
        """Run once to embed knowledge base"""
        for concept in self.knowledge_base["concepts"]:
            existing = db.query(ConceptEmbedding).filter(
                ConceptEmbedding.concept_id == concept["id"]
            ).first()
            
            if existing:
                continue
            
            content = f"""
            {concept['title']}
            {concept['definition']}
            Examples: {' '.join(concept['examples'])}
            """
            
            response = client.models.embed_content(
                model=self.embedding_model,
                contents=content
            )
            
            db_embedding = ConceptEmbedding(
                concept_id=concept["id"],
                content=content,
                embedding=response.embeddings[0].values
            )
            db.add(db_embedding)
        
        db.commit()
        print(f"✓ Embedded {len(self.knowledge_base['concepts'])} concepts")
    
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
        
        query_text = f"Spending pattern: {pattern_details}"
        response = client.models.embed_content(
            model=self.embedding_model,
            contents=query_text
        )
        query_embedding = response.embeddings[0].values
        
        results = db.execute(
            select(ConceptEmbedding).order_by(
                ConceptEmbedding.embedding.cosine_distance(query_embedding)
            ).limit(1)
        ).scalars().all()
        
        if results:
            concept_id = results[0].concept_id
            return next(c for c in self.knowledge_base["concepts"] if c["id"] == concept_id)
        
        return None
    
    def get_explanation(self, concept: Dict, pattern_details: Dict) -> str:
        """Generate personalized explanation using RAG"""
        
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

Example good response: "This pattern shows present bias - you're valuing the immediate comfort of coffee more than the future $150/month. That's completely normal! Our brains are wired for instant rewards."

Your explanation:"""
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text

rag_service = RAGService()