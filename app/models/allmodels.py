import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Integer, ARRAY, Text, Date
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base() 

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    imgpath = Column(String)
    ocr_res = Column(JSONB)
    at_time = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("snapshots.id"))
    
    date = Column(Date, nullable=False)
    merchant = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String)
    verified = Column(Boolean, default=False) 

class DetectedPattern(Base):
    """Behavioral events found by the Rule Engine"""
    __tablename__ = "detected_patterns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    pattern_code = Column(String) 
    bias_mapping = Column(String) 
    details = Column(JSONB)
    trigger_transaction_ids = Column(ARRAY(UUID(as_uuid=True)))
    created_at = Column(DateTime, default=datetime.utcnow)

class ReflectionSession(Base):
    __tablename__ = "reflection_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(UUID(as_uuid=True), ForeignKey("detected_patterns.id"))
    ai_question = Column(Text)
    user_answer = Column(Text)
    reflection_quality_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConceptEmbedding(Base):
    __tablename__ = "concept_embeddings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(String, unique=True)
    content = Column(Text)
    embedding = Column(Vector(768))

class GeneratedQuestion(Base):
    __tablename__ = "generated_questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(UUID(as_uuid=True), ForeignKey("detected_patterns.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String)  
    context_data = Column(JSONB)  
    
    is_answered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)