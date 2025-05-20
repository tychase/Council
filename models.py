from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

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

class Question(BaseModel):
    """Model representing a question asked by a user."""
    id: str = Field(..., description="Unique identifier for the question")
    text: str = Field(..., description="Text of the question")
    timestamp: str = Field(..., description="ISO timestamp when the question was created")

class SharedContext(BaseModel):
    """Model representing the shared context for a question."""
    question_id: str = Field(..., description="ID of the question")
    question_text: str = Field(..., description="Text of the question")
    timestamp: str = Field(..., description="ISO timestamp when the context was created")
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent responses")
    critiques: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent critiques")
    research: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent research")
    conclusions: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent conclusions")
