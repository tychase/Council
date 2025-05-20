import asyncio
import random
import json
import logging
from typing import Dict, List, Any
import uuid
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Base URL for the MCP server
BASE_URL = "http://0.0.0.0:5000"

# Define agents
AGENTS = [
    {"id": "agent-gpt", "name": "GPT Assistant"},
    {"id": "agent-claude", "name": "Claude AI"},
    {"id": "agent-grok", "name": "Grok AI"}
]

# Sample questions
SAMPLE_QUESTIONS = [
    "What are the ethical implications of AI in healthcare?",
    "How does quantum computing differ from classical computing?",
    "What are the most promising renewable energy sources for the next decade?",
    "How might we solve the global water crisis?",
    "What are the long-term effects of social media on society?"
]

# Generate sample agent responses
def generate_response(agent_id: str, question: str) -> Dict[str, Any]:
    """Generate a mock response for an agent."""
    responses = {
        "agent-gpt": {
            "content": f"As GPT, I believe {question} involves several key aspects. First, we must consider the technological implications. Second, there are societal factors to consider. Finally, there are economic considerations.",
            "confidence": random.uniform(0.7, 0.95),
            "reasoning": "I've analyzed this question based on my training data which includes research papers, articles, and discussions on this topic."
        },
        "agent-claude": {
            "content": f"Considering {question}, I would approach this from multiple angles. There are scientific aspects, ethical dimensions, and practical considerations that all need to be balanced.",
            "confidence": random.uniform(0.7, 0.95),
            "reasoning": "My analysis draws from a comprehensive review of relevant literature and case studies in this domain."
        },
        "agent-grok": {
            "content": f"When tackling {question}, I think it's important to be direct. The key issues are often overlooked in conventional analysis. Let me offer a fresh perspective on this topic.",
            "confidence": random.uniform(0.7, 0.95),
            "reasoning": "I'm basing this response on my understanding of cutting-edge developments and alternative viewpoints in this area."
        }
    }
    return responses.get(agent_id, {"content": "No specific response", "confidence": 0.5, "reasoning": "Generic reasoning"})

# Generate critiques
def generate_critique(agent_id: str, target_agent_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a mock critique of another agent's response."""
    critique_templates = [
        "I think the response is {quality}, but {improvement}.",
        "The analysis is {quality}. However, {improvement}.",
        "While I agree with parts of this response, {improvement}."
    ]
    
    qualities = ["insightful", "comprehensive", "interesting", "well-structured", "thoughtful"]
    improvements = [
        "it could benefit from more concrete examples",
        "it overlooks some important historical context",
        "it doesn't fully address the economic implications",
        "it might be making some assumptions that need verification",
        "it could consider alternative viewpoints more thoroughly"
    ]
    
    return {
        "target_agent": target_agent_id,
        "critique": random.choice(critique_templates).format(
            quality=random.choice(qualities),
            improvement=random.choice(improvements)
        ),
        "agreement_level": random.uniform(0.3, 0.9),
        "key_points": ["point1", "point2", "point3"]
    }

# Generate research
def generate_research(agent_id: str, question: str) -> Dict[str, Any]:
    """Generate mock research findings for a question."""
    research_templates = [
        "Based on my analysis of recent studies, {finding}.",
        "According to the latest research in this field, {finding}.",
        "My research indicates that {finding}."
    ]
    
    findings = [
        "there are significant developments that suggest new approaches",
        "experts are divided on this issue with compelling arguments on both sides",
        "the historical trends provide valuable insights for future directions",
        "cross-disciplinary approaches yield the most promising results",
        "practical implementation faces several challenges that need addressing"
    ]
    
    sources = [
        {"title": f"Journal of {random.choice(['AI', 'Computing', 'Ethics', 'Science', 'Technology'])}", "year": random.randint(2018, 2023), "relevance": random.uniform(0.7, 0.95)},
        {"title": f"International Conference on {random.choice(['AI', 'Computing', 'Ethics', 'Science', 'Technology'])}", "year": random.randint(2018, 2023), "relevance": random.uniform(0.7, 0.95)},
        {"title": f"Handbook of {random.choice(['AI', 'Computing', 'Ethics', 'Science', 'Technology'])}", "year": random.randint(2018, 2023), "relevance": random.uniform(0.7, 0.95)}
    ]
    
    return {
        "findings": random.choice(research_templates).format(finding=random.choice(findings)),
        "sources": random.sample(sources, k=random.randint(1, 3)),
        "confidence": random.uniform(0.7, 0.95)
    }

# Generate conclusion
def generate_conclusion(agent_id: str, question: str) -> Dict[str, Any]:
    """Generate a mock conclusion for a question."""
    conclusion_templates = [
        "After considering all perspectives, I conclude that {conclusion}.",
        "My final assessment is that {conclusion}.",
        "Taking all factors into account, {conclusion}."
    ]
    
    conclusions = [
        "this is a multifaceted issue requiring a balanced approach",
        "the evidence points to several promising directions for future work",
        "there are significant trade-offs that need careful consideration",
        "a combination of approaches is likely to yield the best results",
        "further research is needed but current findings suggest preliminary directions"
    ]
    
    return {
        "summary": random.choice(conclusion_templates).format(conclusion=random.choice(conclusions)),
        "key_takeaways": ["takeaway1", "takeaway2", "takeaway3"],
        "confidence": random.uniform(0.7, 0.95),
        "final_position": random.choice(["supportive", "cautious", "critical", "neutral", "optimistic"])
    }

async def submit_question(client, question_text: str) -> str:
    """Submit a new question to the MCP server."""
    response = await client.post(f"{BASE_URL}/question", params={"question_text": question_text})
    response.raise_for_status()
    data = response.json()
    question_id = data["question_id"]
    logger.info(f"Created question: '{question_text}' with ID: {question_id}")
    return question_id

async def submit_agent_contribution(client, question_id: str, agent: Dict[str, str], stage: str, payload: Dict[str, Any]):
    """Submit an agent's contribution (response, critique, research, or conclusion)."""
    submission = {
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "stage": stage,
        "payload": payload
    }
    
    response = await client.post(f"{BASE_URL}/submit/{question_id}", json=submission)
    response.raise_for_status()
    logger.info(f"Submitted {stage} from {agent['name']} for question {question_id}")

async def simulate_agent_interaction(client, question_text: str):
    """Simulate a complete multi-agent interaction for a question."""
    # Submit the question
    question_id = await submit_question(client, question_text)
    
    # Step 1: Each agent provides an initial response
    responses = {}
    for agent in AGENTS:
        response_payload = generate_response(agent["id"], question_text)
        await submit_agent_contribution(client, question_id, agent, "response", response_payload)
        responses[agent["id"]] = response_payload
    
    logger.info(f"All agents have submitted responses for question {question_id}")
    
    # Step 2: Each agent critiques others' responses
    for agent in AGENTS:
        for target_agent in AGENTS:
            if agent["id"] != target_agent["id"]:
                critique_payload = generate_critique(agent["id"], target_agent["id"], responses[target_agent["id"]])
                await submit_agent_contribution(client, question_id, agent, "critique", critique_payload)
    
    logger.info(f"All agents have submitted critiques for question {question_id}")
    
    # Step 3: Each agent conducts research
    for agent in AGENTS:
        research_payload = generate_research(agent["id"], question_text)
        await submit_agent_contribution(client, question_id, agent, "research", research_payload)
    
    logger.info(f"All agents have submitted research for question {question_id}")
    
    # Step 4: Each agent provides a conclusion
    for agent in AGENTS:
        conclusion_payload = generate_conclusion(agent["id"], question_text)
        await submit_agent_contribution(client, question_id, agent, "conclusion", conclusion_payload)
    
    logger.info(f"All agents have submitted conclusions for question {question_id}")
    
    # Get and print the final context
    response = await client.get(f"{BASE_URL}/context/{question_id}")
    context = response.json()
    logger.info(f"Final context for question '{question_text}':")
    logger.info(json.dumps(context, indent=2))
    
    return question_id

async def main():
    """Run the agent simulator."""
    logger.info("Starting agent simulator")
    
    async with httpx.AsyncClient() as client:
        # Select a random question from the sample questions
        question = random.choice(SAMPLE_QUESTIONS)
        
        try:
            await simulate_agent_interaction(client, question)
            logger.info("Simulation completed successfully")
        except Exception as e:
            logger.error(f"Simulation failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
