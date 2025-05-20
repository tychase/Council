"""API routes for real agent integration in the MCP Multi-Agent Hub."""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, request, jsonify
import asyncio

from agents.real_agent_runner import process_question_with_agents
from app import db
from models import Question, Context

# Configure logging
logger = logging.getLogger("agent_routes")

# Create a Blueprint for agent routes
agent_routes = Blueprint('agent_routes', __name__)

@agent_routes.route('/api/real-agents/run', methods=['POST'])
def run_real_agents():
    """Process a question with real AI agents.
    
    Expects JSON with:
    - question: string - The question to process
    - use_real_agents: boolean (optional) - Whether to use real AI APIs or mock agents
    
    Returns:
    - JSON with question ID and status
    """
    try:
        data = request.json
        if not data or 'question' not in data:
            return jsonify({"error": "Missing required field: question"}), 400
            
        question_text = data.get('question')
        use_real_agents = data.get('use_real_agents', True)
        
        logger.info(f"Running real agents for question: {question_text}")
        
        # Generate a question ID
        question_id = str(uuid.uuid4())
        
        # Create the question in the database
        new_question = Question(
            id=question_id,
            text=question_text
        )
        
        # Initialize empty context
        new_context = Context(
            id=str(uuid.uuid4()),
            question_id=question_id,
            responses={},
            critiques={},
            research={},
            conclusions={}
        )
        
        # Add to database to create the question entry
        db.session.add(new_question)
        db.session.add(new_context)
        db.session.commit()
        
        # Instead of async, we'll start a separate thread
        import threading
        thread = threading.Thread(
            target=process_in_thread,
            args=(question_id, question_text, use_real_agents)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "question_id": question_id,
            "status": "processing",
            "message": "Question submitted for processing with real agents"
        })
        
    except Exception as e:
        logger.error(f"Error running real agents: {str(e)}")
        return jsonify({"error": str(e)}), 500

def process_in_thread(question_id: str, question_text: str, use_real_agents: bool):
    """Process the question with agents in a separate thread.
    
    Args:
        question_id: The ID of the question in the database
        question_text: The text of the question
        use_real_agents: Whether to use real AI APIs or mock agents
    """
    try:
        logger.info(f"Starting processing for question {question_id} in thread")
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Process the question with agents
        result = loop.run_until_complete(
            process_question_with_agents(question_text, use_real_agents)
        )
        
        # Update the database with the results
        from app import app
        with app.app_context():
            # Get the context object
            context = Context.query.filter_by(question_id=question_id).first()
            if not context:
                logger.error(f"Context not found for question {question_id}")
                return
                
            # Update the context with the results
            if "responses" in result:
                context.responses = result["responses"]
            if "critiques" in result:
                context.critiques = result["critiques"]
            if "research" in result:
                context.research = result["research"]
            if "conclusions" in result:
                context.conclusions = result["conclusions"]
                
            # Commit the changes
            db.session.commit()
            
            logger.info(f"Updated database with results for question {question_id}")
        
        # Close the loop
        loop.close()
    
    except Exception as e:
        logger.error(f"Error processing question {question_id}: {str(e)}")

@agent_routes.route('/api/real-agents/status/<question_id>', methods=['GET'])
def check_processing_status(question_id: str):
    """Check the processing status of a question.
    
    Args:
        question_id: The ID of the question
        
    Returns:
        JSON with status information
    """
    try:
        # Get the question and context
        question = Question.query.get(question_id)
        if not question:
            return jsonify({"error": "Question not found"}), 404
            
        context = Context.query.filter_by(question_id=question_id).first()
        if not context:
            return jsonify({"error": "Context not found"}), 404
            
        # Determine status based on content
        status = "pending"
        progress = 0
        
        if context.responses and len(context.responses) > 0:
            progress = 25
            status = "responses_ready"
            
        if context.critiques and len(context.critiques) > 0:
            progress = 50
            status = "critiques_ready"
            
        if context.research and len(context.research) > 0:
            progress = 75
            status = "research_ready"
            
        if context.conclusions and len(context.conclusions) > 0:
            progress = 100
            status = "complete"
            
        return jsonify({
            "question_id": question_id,
            "status": status,
            "progress": progress,
            "question_text": question.text
        })
        
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        return jsonify({"error": str(e)}), 500