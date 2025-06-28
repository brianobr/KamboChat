"""
Database models for the Kambo chatbot
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string for default values"""
    return str(uuid.uuid4())


class User(Base):
    """User model for tracking conversations"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta = Column(JSON, nullable=True)


class Conversation(Base):
    """Conversation model for grouping messages"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)  # Can be anonymous
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    meta = Column(JSON, nullable=True)


class Message(Base):
    """Message model for storing chat messages"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta = Column(JSON, nullable=True)


class MedicalVerification(Base):
    """Medical verification logs"""
    __tablename__ = "medical_verifications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    message_id = Column(String, nullable=False)
    verification_passed = Column(Boolean, nullable=False)
    issues_found = Column(JSON, nullable=True)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())


class SecurityLog(Base):
    """Security event logs"""
    __tablename__ = "security_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False)  # 'prompt_injection', 'rate_limit', etc.
    user_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 