"""Base agent class for the MCP Multi-Agent Hub."""
import abc
from typing import Dict, Any, List, Optional


class BaseAgent(abc.ABC):
    """Abstract base class for all agent implementations."""
    
    def __init__(self, agent_id: str, agent_name: str):
        """Initialize the agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name for the agent
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
    
    @abc.abstractmethod
    async def generate_response(self, question: str) -> Dict[str, Any]:
        """Generate a response for a question.
        
        Args:
            question: The question to answer
            
        Returns:
            A dictionary containing the response content and metadata
        """
        pass
    
    @abc.abstractmethod
    async def generate_critique(self, question: str, target_agent_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a critique of another agent's response.
        
        Args:
            question: The original question
            target_agent_id: ID of the agent whose response is being critiqued
            response: Response content and metadata from the target agent
            
        Returns:
            A dictionary containing the critique content and metadata
        """
        pass
    
    @abc.abstractmethod
    async def generate_research(self, question: str) -> Dict[str, Any]:
        """Generate research for a question.
        
        Args:
            question: The question to research
            
        Returns:
            A dictionary containing the research findings and metadata
        """
        pass
    
    @abc.abstractmethod
    async def generate_conclusion(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a conclusion for a question based on all available context.
        
        Args:
            question: The original question
            context: All available context including responses, critiques, and research
            
        Returns:
            A dictionary containing the conclusion and metadata
        """
        pass