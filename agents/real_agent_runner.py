"""Runner script for processing questions with real AI agents."""
import asyncio
import logging
import argparse
import sys
import json
from typing import Dict, Any

from agents.agent_manager import AgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("real_agent_runner")

async def process_question_with_agents(question: str, use_real_agents: bool = True) -> Dict[str, Any]:
    """Process a question with all available AI agents.
    
    Args:
        question: The question to process
        use_real_agents: Whether to use real AI APIs or mock agents
        
    Returns:
        Dictionary with all agent responses, critiques, research, and conclusions
    """
    try:
        # Initialize the agent manager
        agent_manager = AgentManager(use_real_agents=use_real_agents)
        
        # Check available agents
        available_agents = agent_manager.get_available_agents()
        logger.info(f"Available agents: {available_agents}")
        
        if not available_agents:
            logger.error("No agents available")
            return {
                "error": "No agents available",
                "question": question
            }
        
        # Process the question with all agents
        result = await agent_manager.process_question(question)
        return result
        
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return {
            "error": str(e),
            "question": question
        }

async def main(question: str, output_file: str = None, use_real_agents: bool = True):
    """Run the agent processing pipeline.
    
    Args:
        question: The question to process
        output_file: Path to save the results (optional)
        use_real_agents: Whether to use real AI APIs or mock agents
    """
    logger.info(f"Processing question: {question}")
    logger.info(f"Using real agents: {use_real_agents}")
    
    # Process the question
    result = await process_question_with_agents(question, use_real_agents)
    
    # Print or save the result
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a question with AI agents")
    parser.add_argument("question", help="The question to process")
    parser.add_argument("--output", "-o", help="Path to save the results (optional)")
    parser.add_argument("--mock", action="store_true", help="Use mock agents instead of real AI APIs")
    
    args = parser.parse_args()
    
    asyncio.run(main(
        question=args.question,
        output_file=args.output,
        use_real_agents=not args.mock
    ))