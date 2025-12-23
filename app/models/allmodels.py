import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Integer, ARRAY, Text, Date
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
    __tablename__ = "detected_patterns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    pattern_code = Column(String)
    bias_mapping = Column(String)
    
    details = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReflectionSession(Base):
    __tablename__ = "reflection_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(UUID(as_uuid=True), ForeignKey("detected_patterns.id"))
    ai_question = Column(Text)
    user_answer = Column(Text)
    reflection_quality_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)