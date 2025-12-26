# app/api/endpoints/learning.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.allmodels import DetectedPattern, GeneratedQuestion, ReflectionSession
from app.services.rag_service import rag_service
from app.services.question_service import question_generator
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

router = APIRouter()

class QuestionResponse(BaseModel):
    question_id: UUID
    question_text: str
    pattern_type: str
    bias_name: str
    explanation: str
    context: dict

class AnswerSubmission(BaseModel):
    question_id: UUID
    answer_text: str

@router.post("/generate-question/{pattern_id}", response_model=QuestionResponse)
def generate_question_for_pattern(
    pattern_id: UUID,
    user_id: str,  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Generate a reflection question from a detected pattern"""
    
    # Get pattern
    pattern = db.query(DetectedPattern).filter(
        DetectedPattern.id == pattern_id,
        DetectedPattern.user_id == user_id
    ).first()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # Check if question already exists
    existing = db.query(GeneratedQuestion).filter(
        GeneratedQuestion.pattern_id == pattern_id,
        GeneratedQuestion.is_answered == False
    ).first()
    
    if existing:
        concept = rag_service.retrieve_relevant_concept(
            db, pattern.bias_mapping, pattern.details
        )
        explanation = rag_service.get_explanation(concept, pattern.details)
        
        return QuestionResponse(
            question_id=existing.id,
            question_text=existing.question_text,
            pattern_type=pattern.pattern_code,
            bias_name=pattern.bias_mapping,
            explanation=explanation,
            context=existing.context_data
        )
    
    # Retrieve relevant concept
    concept = rag_service.retrieve_relevant_concept(
        db, pattern.bias_mapping, pattern.details
    )
    
    if not concept:
        raise HTTPException(status_code=500, detail="No matching concept found")
    
    # Generate question
    question_text = question_generator.generate_question(
        pattern_code=pattern.pattern_code,
        bias_name=pattern.bias_mapping,
        pattern_details=pattern.details,
        concept_context=concept
    )
    
    # Generate explanation
    explanation = rag_service.get_explanation(concept, pattern.details)
    
    # Save question
    db_question = GeneratedQuestion(
        pattern_id=pattern_id,
        user_id=user_id,
        question_text=question_text,
        question_type="reflection",
        context_data={
            "pattern_code": pattern.pattern_code,
            "bias": pattern.bias_mapping,
            "concept_id": concept["id"]
        }
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    return QuestionResponse(
        question_id=db_question.id,
        question_text=question_text,
        pattern_type=pattern.pattern_code,
        bias_name=pattern.bias_mapping,
        explanation=explanation,
        context=pattern.details
    )

@router.post("/submit-answer")
def submit_reflection_answer(
    submission: AnswerSubmission,
    user_id: str,  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """User submits their reflection answer"""
    
    question = db.query(GeneratedQuestion).filter(
        GeneratedQuestion.id == submission.question_id,
        GeneratedQuestion.user_id == user_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Calculate reflection quality (simple heuristic)
    word_count = len(submission.answer_text.split())
    quality_score = min(100, word_count * 5)  # 20 words = 100 score
    
    # Save reflection session
    session = ReflectionSession(
        pattern_id=question.pattern_id,
        ai_question=question.question_text,
        user_answer=submission.answer_text,
        reflection_quality_score=quality_score
    )
    db.add(session)
    
    # Mark question as answered
    question.is_answered = True
    
    db.commit()
    
    return {
        "status": "recorded",
        "quality_score": quality_score,
        "message": "Great reflection! This helps you build awareness of your spending patterns."
    }

@router.get("/unanswered-questions")
def get_unanswered_questions(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all pending reflection questions"""
    
    questions = db.query(GeneratedQuestion).filter(
        GeneratedQuestion.user_id == user_id,
        GeneratedQuestion.is_answered == False
    ).all()
    
    return {
        "count": len(questions),
        "questions": [
            {
                "id": q.id,
                "text": q.question_text,
                "created_at": q.created_at
            }
            for q in questions
        ]
    }