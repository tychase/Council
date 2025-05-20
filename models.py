from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app import db

# Pydantic models for API validation
class Stage(str, Enum):
    """Enum representing the different stages in the multi-agent process."""
    RESPONSE = "response"
    CRITIQUE = "critique"
    RESEARCH = "research"
    CONCLUSION = "conclusion"

class AgentSubmission(BaseModel):
    """Model representing a submission from an agent."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_name: Optional[str] = Field(None, description="Human-readable name for the agent")
    stage: Stage = Field(..., description="Stage of the submission")
    payload: Dict[str, Any] = Field(..., description="Content of the submission")

class QuestionModel(BaseModel):
    """Pydantic model representing a question asked by a user."""
    id: str = Field(..., description="Unique identifier for the question")
    text: str = Field(..., description="Text of the question")
    timestamp: str = Field(..., description="ISO timestamp when the question was created")

class SharedContextModel(BaseModel):
    """Pydantic model representing the shared context for a question."""
    question_id: str = Field(..., description="ID of the question")
    question_text: str = Field(..., description="Text of the question")
    timestamp: str = Field(..., description="ISO timestamp when the context was created")
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent responses")
    critiques: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent critiques")
    research: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent research")
    conclusions: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent conclusions")

# SQLAlchemy models for database
class Question(db.Model):
    """SQLAlchemy model for questions."""
    __tablename__ = 'questions'
    
    id = db.Column(db.String(36), primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    context = db.relationship("Context", back_populates="question", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat()
        }

class Context(db.Model):
    """SQLAlchemy model for shared context."""
    __tablename__ = 'contexts'
    
    id = db.Column(db.String(36), primary_key=True)
    question_id = db.Column(db.String(36), db.ForeignKey('questions.id'), nullable=False)
    question = db.relationship("Question", back_populates="context")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Store JSON data
    responses = db.Column(db.JSON, default=dict)
    critiques = db.Column(db.JSON, default=dict)
    research = db.Column(db.JSON, default=dict)
    conclusions = db.Column(db.JSON, default=dict)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "question_id": self.question_id,
            "question_text": self.question.text,
            "timestamp": self.timestamp.isoformat(),
            "responses": {} if self.responses is None else self.responses,
            "critiques": {} if self.critiques is None else self.critiques,
            "research": {} if self.research is None else self.research,
            "conclusions": {} if self.conclusions is None else self.conclusions
        }
