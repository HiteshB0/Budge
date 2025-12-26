# app/services/rag_service.py
import json
import os
from typing import List, Dict
import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.allmodels import ConceptEmbedding
from pathlib import Path

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class RAGService:
    def __init__(self):
        self.embedding_model = "models/embedding-001"
        kb_path = Path(__file__).parent.parent / "knowledge" / "finance_concepts.json"
        with open(kb_path) as f:
            self.knowledge_base = json.load(f)
    
    def initialize_embeddings(self, db: Session):
        """Run once to embed knowledge base"""
        for concept in self.knowledge_base["concepts"]:
            existing = db.query(ConceptEmbedding).filter(
                ConceptEmbedding.concept_id == concept["id"]
            ).first()
            
            if existing:
                continue
            
            # Combine all text for embedding
            content = f"""
            {concept['title']}
            {concept['definition']}
            Examples: {' '.join(concept['examples'])}
            """
            
            embedding = genai.embed_content(
                model=self.embedding_model,
                content=content,
                task_type="retrieval_document"
            )["embedding"]
            
            db_embedding = ConceptEmbedding(
                concept_id=concept["id"],
                content=content,
                embedding=embedding
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
        
        # Direct mapping (deterministic fallback)
        for concept in self.knowledge_base["concepts"]:
            if concept["id"] == bias_mapping.lower():
                return concept
        
        # Semantic search if no direct match
        query_text = f"Spending pattern: {pattern_details}"
        query_embedding = genai.embed_content(
            model=self.embedding_model,
            content=query_text,
            task_type="retrieval_query"
        )["embedding"]
        
        # Find nearest neighbor
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
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text

# Singleton instance
rag_service = RAGService()