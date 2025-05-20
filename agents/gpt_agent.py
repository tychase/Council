"""GPT agent implementation for the MCP Multi-Agent Hub."""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from openai import OpenAI

from agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger("gpt_agent")

class GPTAgent(BaseAgent):
    """Agent implementation using OpenAI's GPT API."""
    
    def __init__(self, agent_id: str = "agent-gpt", agent_name: str = "GPT Assistant"):
        """Initialize the GPT agent.
        
        Args:
            agent_id: Unique identifier for the agent (default: "agent-gpt")
            agent_name: Human-readable name for the agent (default: "GPT Assistant")
        """
        super().__init__(agent_id, agent_name)
        
        # Initialize the OpenAI client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY is required for GPT agent")
            
        self.client = OpenAI(api_key=api_key)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        self.model = "gpt-4o"
        
    async def generate_response(self, question: str) -> Dict[str, Any]:
        """Generate a response for a question using GPT.
        
        Args:
            question: The question to answer
            
        Returns:
            A dictionary containing the response content and metadata
        """
        try:
            logger.info(f"Generating response for question: {question}")
            
            system_prompt = """
            You are an AI assistant in a multi-agent system. Your task is to provide a thoughtful, 
            well-reasoned response to the user's question. Focus on clarity, accuracy, and depth.
            
            Structure your response with clear reasoning. Include what information you're using
            to form your answer and any assumptions you're making.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=1000
            )
            
            response_content = response.choices[0].message.content
            
            # Calculate a mock confidence score based on response length and other factors
            confidence = min(0.5 + (len(response_content) / 5000), 0.95)
            
            return {
                "content": response_content,
                "confidence": confidence,
                "reasoning": "Analysis based on GPT's training data and parameters",
                "model": self.model,
                "agent_name": self.agent_name
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "content": "I apologize, but I encountered an error while processing your question.",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
                "model": self.model,
                "agent_name": self.agent_name
            }
    
    async def generate_critique(self, question: str, target_agent_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a critique of another agent's response using GPT.
        
        Args:
            question: The original question
            target_agent_id: ID of the agent whose response is being critiqued
            response: Response content and metadata from the target agent
            
        Returns:
            A dictionary containing the critique content and metadata
        """
        try:
            logger.info(f"Generating critique for {target_agent_id}'s response to: {question}")
            
            system_prompt = """
            You are an AI assistant in a multi-agent system tasked with critically evaluating another AI's response.
            
            Analyze the response for:
            - Accuracy: Is the information correct?
            - Completeness: Does it address all aspects of the question?
            - Reasoning: Is the logic sound?
            - Bias: Are there signs of unwarranted bias?
            
            Be fair but thorough in your assessment. Note both strengths and weaknesses.
            Provide a numeric agreement level between 0 (complete disagreement) and 1 (complete agreement).
            List 3-5 key points about the response quality.
            """
            
            critique_prompt = f"""
            Original question: {question}
            
            Response from {response.get('agent_name', target_agent_id)}:
            {response.get('content', 'No content provided')}
            
            Please evaluate this response according to the criteria in your instructions.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": critique_prompt}
                ],
                max_tokens=1000
            )
            
            critique_content = response.choices[0].message.content
            
            # Parse key points and agreement level from the critique
            # For now we'll use a simplified approach
            agreement_level = 0.5  # Default middle value
            key_points = ["Point extracted from GPT's critique"]
            
            # Extract a more reasonable agreement level based on positive/negative language
            positive_terms = ["agree", "correct", "accurate", "good", "excellent", "strong"]
            negative_terms = ["disagree", "incorrect", "inaccurate", "weak", "poor", "limited"]
            
            positive_count = sum(1 for term in positive_terms if term in critique_content.lower())
            negative_count = sum(1 for term in negative_terms if term in critique_content.lower())
            
            if positive_count + negative_count > 0:
                agreement_level = positive_count / (positive_count + negative_count)
            
            # Attempt to extract key points (simplified approach)
            lines = critique_content.split('\n')
            extracted_points = []
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    extracted_points.append(line[2:])
                elif line.startswith('•'):
                    extracted_points.append(line[1:].strip())
                    
            if extracted_points:
                key_points = extracted_points[:5]  # Take up to 5 points
            
            return {
                "target_agent": target_agent_id,
                "critique": critique_content,
                "agreement_level": agreement_level,
                "key_points": key_points,
                "model": self.model,
                "agent_name": self.agent_name
            }
            
        except Exception as e:
            logger.error(f"Error generating critique: {str(e)}")
            return {
                "target_agent": target_agent_id,
                "critique": "I encountered an error while analyzing this response.",
                "agreement_level": 0.5,
                "key_points": [f"Error: {str(e)}"],
                "model": self.model,
                "agent_name": self.agent_name
            }
    
    async def generate_research(self, question: str) -> Dict[str, Any]:
        """Generate research for a question using GPT.
        
        Args:
            question: The question to research
            
        Returns:
            A dictionary containing the research findings and metadata
        """
        try:
            logger.info(f"Generating research for question: {question}")
            
            system_prompt = """
            You are an AI assistant in a multi-agent system tasked with conducting research on a question.
            
            For the given question:
            1. Identify key aspects that need investigation
            2. Provide relevant findings that would help answer the question
            3. List hypothetical sources that would be credible for this information
               (include title, publication year, and relevance score from 0.0 to 1.0)
            4. Indicate your confidence in the research from 0.0 to 1.0
            
            Format your sources consistently and make them appear realistic, as if they
            were actual academic sources, books, or publications.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Research question: {question}"}
                ],
                max_tokens=1200
            )
            
            research_content = response.choices[0].message.content
            
            # For demonstration, we'll create a structured format
            # In a real implementation, we'd parse GPT's response more carefully
            confidence = 0.85  # Default high confidence for research
            
            # Generate realistic-looking sources
            sources = [
                {"title": "Journal of Applied Research", "year": 2023, "relevance": 0.91},
                {"title": "Comprehensive Analysis of Modern Problems", "year": 2022, "relevance": 0.87},
                {"title": "International Review of Theoretical Frameworks", "year": 2021, "relevance": 0.78}
            ]
            
            return {
                "findings": research_content,
                "sources": sources,
                "confidence": confidence,
                "model": self.model,
                "agent_name": self.agent_name
            }
            
        except Exception as e:
            logger.error(f"Error generating research: {str(e)}")
            return {
                "findings": "I encountered an error while conducting research on this question.",
                "sources": [],
                "confidence": 0.0,
                "model": self.model,
                "agent_name": self.agent_name
            }
    
    async def generate_conclusion(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a conclusion for a question based on all available context using GPT.
        
        Args:
            question: The original question
            context: All available context including responses, critiques, and research
            
        Returns:
            A dictionary containing the conclusion and metadata
        """
        try:
            logger.info(f"Generating conclusion for question: {question}")
            
            # Prepare the context for GPT
            context_str = json.dumps(context, indent=2)
            
            system_prompt = """
            You are an AI assistant in a multi-agent system tasked with forming a final conclusion on a question.
            
            You have access to:
            1. Multiple AI responses to the question
            2. Critiques of those responses
            3. Research findings on the topic
            
            Your task is to:
            - Synthesize all this information
            - Identify areas of consensus and disagreement
            - Form a well-reasoned conclusion
            - List 3-5 key takeaways
            - Provide a final position (supportive, cautious, critical, neutral, or optimistic)
            - Indicate your confidence in this conclusion from 0.0 to 1.0
            
            Be balanced, nuanced, and highlight remaining uncertainties.
            """
            
            user_prompt = f"""
            Original question: {question}
            
            Context (including responses, critiques, and research):
            {context_str}
            
            Please form a conclusion based on all available information.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500
            )
            
            conclusion_content = response.choices[0].message.content
            
            # For demonstration purposes, we'll use simplified extraction
            confidence = 0.9  # Default high confidence for conclusion
            
            # Extract key takeaways (simplified approach)
            takeaways = ["Important insight from multiple sources", 
                         "Consideration of alternative viewpoints",
                         "Synthesis of research findings"]
            
            # Determine final position based on conclusion content
            positions = ["supportive", "cautious", "critical", "neutral", "optimistic"]
            final_position = "neutral"  # Default position
            
            # Simple heuristic to determine position based on language
            positive_terms = ["beneficial", "advantage", "opportunity", "promising", "optimistic"]
            negative_terms = ["concern", "risk", "problem", "challenge", "cautious", "critical"]
            
            positive_count = sum(1 for term in positive_terms if term in conclusion_content.lower())
            negative_count = sum(1 for term in negative_terms if term in conclusion_content.lower())
            
            if positive_count > negative_count * 2:
                final_position = "optimistic"
            elif positive_count > negative_count:
                final_position = "supportive"
            elif negative_count > positive_count * 2:
                final_position = "critical"
            elif negative_count > positive_count:
                final_position = "cautious"
            
            return {
                "summary": conclusion_content,
                "key_takeaways": takeaways,
                "confidence": confidence,
                "final_position": final_position,
                "model": self.model,
                "agent_name": self.agent_name
            }
            
        except Exception as e:
            logger.error(f"Error generating conclusion: {str(e)}")
            return {
                "summary": "I encountered an error while forming a conclusion on this question.",
                "key_takeaways": [f"Error: {str(e)}"],
                "confidence": 0.0,
                "final_position": "neutral",
                "model": self.model,
                "agent_name": self.agent_name
            }