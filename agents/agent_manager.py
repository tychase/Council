"""Agent manager for coordinating multiple AI agents in the MCP Multi-Agent Hub."""
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent
from agents.claude_agent import ClaudeAgent
from agents.gpt_agent import GPTAgent
from agents.grok_agent import GrokAgent

# Configure logging
logger = logging.getLogger("agent_manager")

class AgentManager:
    """Manager class for coordinating multiple AI agents."""
    
    def __init__(self, use_real_agents: bool = True):
        """Initialize the agent manager.
        
        Args:
            use_real_agents: Whether to use real AI APIs (True) or mock agents (False)
        """
        self.use_real_agents = use_real_agents
        self.agents: Dict[str, BaseAgent] = {}
        
        # Initialize agents
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize the available AI agents."""
        try:
            if self.use_real_agents:
                # Check for necessary API keys
                openai_key = os.environ.get("OPENAI_API_KEY")
                anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
                perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
                
                # Add agents that have available API keys
                if anthropic_key:
                    logger.info("Initializing Claude agent")
                    self.agents["agent-claude"] = ClaudeAgent()
                else:
                    logger.warning("ANTHROPIC_API_KEY not found, Claude agent will not be available")
                
                if openai_key:
                    logger.info("Initializing GPT agent")
                    self.agents["agent-gpt"] = GPTAgent()
                else:
                    logger.warning("OPENAI_API_KEY not found, GPT agent will not be available")
                
                if perplexity_key:
                    logger.info("Initializing Grok agent (simulated with Perplexity API)")
                    self.agents["agent-grok"] = GrokAgent()
                else:
                    logger.warning("PERPLEXITY_API_KEY not found, Grok agent will not be available")
                
                if not self.agents:
                    logger.warning("No API keys available for real agents, falling back to mock agents")
                    self._initialize_mock_agents()
            else:
                self._initialize_mock_agents()
                
        except Exception as e:
            logger.error(f"Error initializing agents: {str(e)}")
            logger.warning("Falling back to mock agents")
            self._initialize_mock_agents()
    
    def _initialize_mock_agents(self):
        """Initialize mock agents when real APIs are not available."""
        from agent_simulator import generate_response, generate_critique, generate_research, generate_conclusion
        
        # Create simple mock agent implementations
        class MockAgent(BaseAgent):
            def __init__(self, agent_id, agent_name):
                super().__init__(agent_id, agent_name)
                
            async def generate_response(self, question):
                return generate_response(self.agent_id, question)
                
            async def generate_critique(self, question, target_agent_id, response):
                return generate_critique(self.agent_id, target_agent_id, response)
                
            async def generate_research(self, question):
                return generate_research(self.agent_id, question)
                
            async def generate_conclusion(self, question, context):
                return generate_conclusion(self.agent_id, question)
        
        # Add mock agents
        logger.info("Initializing mock agents")
        self.agents["agent-gpt"] = MockAgent("agent-gpt", "GPT Assistant")
        self.agents["agent-claude"] = MockAgent("agent-claude", "Claude AI")
        self.agents["agent-grok"] = MockAgent("agent-grok", "Grok AI")
    
    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get a list of available agents.
        
        Returns:
            List of dictionaries with agent information
        """
        return [
            {"id": agent_id, "name": agent.agent_name}
            for agent_id, agent in self.agents.items()
        ]
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            The agent instance, or None if not found
        """
        return self.agents.get(agent_id)
    
    async def process_question(self, question: str) -> Dict[str, Any]:
        """Process a question with all available agents.
        
        Args:
            question: The question to process
            
        Returns:
            Dictionary with all agent responses, critiques, research, and conclusions
        """
        logger.info(f"Processing question with {len(self.agents)} agents: {question}")
        
        result = {
            "question": question,
            "responses": {},
            "critiques": {},
            "research": {},
            "conclusions": {}
        }
        
        # Step 1: Generate responses
        for agent_id, agent in self.agents.items():
            try:
                logger.info(f"Generating response with {agent_id}")
                response = await agent.generate_response(question)
                result["responses"][agent_id] = response
            except Exception as e:
                logger.error(f"Error generating response with {agent_id}: {str(e)}")
                result["responses"][agent_id] = {
                    "content": f"Error: {str(e)}",
                    "confidence": 0.0,
                    "agent_name": agent.agent_name
                }
        
        # Step 2: Generate critiques
        for agent_id, agent in self.agents.items():
            for target_id, target_response in result["responses"].items():
                if agent_id != target_id:
                    try:
                        logger.info(f"Generating critique from {agent_id} for {target_id}")
                        critique = await agent.generate_critique(
                            question, target_id, target_response
                        )
                        
                        # Store critique keyed by critiquing agent and target agent
                        if agent_id not in result["critiques"]:
                            result["critiques"][agent_id] = {}
                        
                        result["critiques"][agent_id][target_id] = critique
                    except Exception as e:
                        logger.error(f"Error generating critique from {agent_id} for {target_id}: {str(e)}")
                        
                        if agent_id not in result["critiques"]:
                            result["critiques"][agent_id] = {}
                            
                        result["critiques"][agent_id][target_id] = {
                            "target_agent": target_id,
                            "critique": f"Error: {str(e)}",
                            "agreement_level": 0.5,
                            "key_points": [f"Error occurred: {str(e)}"],
                            "agent_name": agent.agent_name
                        }
        
        # Step 3: Generate research
        for agent_id, agent in self.agents.items():
            try:
                logger.info(f"Generating research with {agent_id}")
                research = await agent.generate_research(question)
                result["research"][agent_id] = research
            except Exception as e:
                logger.error(f"Error generating research with {agent_id}: {str(e)}")
                result["research"][agent_id] = {
                    "findings": f"Error: {str(e)}",
                    "sources": [],
                    "confidence": 0.0,
                    "agent_name": agent.agent_name
                }
        
        # Step 4: Generate conclusions
        for agent_id, agent in self.agents.items():
            try:
                logger.info(f"Generating conclusion with {agent_id}")
                conclusion = await agent.generate_conclusion(question, result)
                result["conclusions"][agent_id] = conclusion
            except Exception as e:
                logger.error(f"Error generating conclusion with {agent_id}: {str(e)}")
                result["conclusions"][agent_id] = {
                    "summary": f"Error: {str(e)}",
                    "key_takeaways": [f"Error occurred: {str(e)}"],
                    "confidence": 0.0,
                    "final_position": "neutral",
                    "agent_name": agent.agent_name
                }
        
        logger.info(f"Completed processing question with all agents")
        return result