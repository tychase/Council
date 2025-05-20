import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, redirect, url_for

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# In-memory storage
questions = {}
shared_context = {}

# Import models for type checking
from models import Stage, Question, SharedContext

# Routes
@app.route('/')
def index():
    """Render the main page of the application."""
    logger.info("Rendering main page")
    return render_template("index.html")

@app.route('/question', methods=['POST'])
def create_question():
    """Create a new question and initialize context."""
    question_text = request.form.get('question_text', '')
    question_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    logger.info(f"Creating new question: '{question_text}' with ID: {question_id}")
    
    # Create question object
    questions[question_id] = {
        "id": question_id,
        "text": question_text,
        "timestamp": timestamp
    }
    
    # Initialize shared context
    shared_context[question_id] = {
        "question_id": question_id,
        "question_text": question_text,
        "timestamp": timestamp,
        "responses": {},
        "critiques": {},
        "research": {},
        "conclusions": {}
    }
    
    return jsonify({"question_id": question_id, "message": "Question created successfully"})

@app.route('/submit/<question_id>', methods=['POST'])
def submit_agent_response(question_id):
    """Submit an agent's response, critique, research, or conclusion for a question."""
    if question_id not in shared_context:
        logger.error(f"Question ID {question_id} not found")
        return jsonify({"error": "Question not found"}), 404
    
    # Parse submission from JSON
    submission = request.json
    agent_id = submission.get('agent_id')
    agent_name = submission.get('agent_name')
    stage = submission.get('stage')
    payload = submission.get('payload', {})
    
    logger.info(f"Received {stage} from agent {agent_id} for question {question_id}")
    
    # Update shared context based on submission stage
    context = shared_context[question_id]
    
    if stage == "response":
        # Add agent name to payload if provided
        if agent_name:
            payload["agent_name"] = agent_name
        context["responses"][agent_id] = payload
    elif stage == "critique":
        if agent_name:
            payload["agent_name"] = agent_name
        context["critiques"][agent_id] = payload
    elif stage == "research":
        if agent_name:
            payload["agent_name"] = agent_name
        context["research"][agent_id] = payload
    elif stage == "conclusion":
        if agent_name:
            payload["agent_name"] = agent_name
        context["conclusions"][agent_id] = payload
    else:
        logger.warning(f"Unknown stage: {stage}")
        return jsonify({"error": "Invalid stage"}), 400
    
    logger.info(f"Updated context for question {question_id}, stage: {stage}")
    return jsonify({"status": "success", "message": f"{stage} recorded successfully"})

@app.route('/context/<question_id>')
def get_context(question_id):
    """Retrieve the shared context for a specific question."""
    if question_id not in shared_context:
        logger.error(f"Question ID {question_id} not found")
        return jsonify({"error": "Question not found"}), 404
    
    logger.info(f"Retrieving context for question {question_id}")
    return jsonify(shared_context[question_id])

@app.route('/questions')
def list_questions():
    """List all questions in the system."""
    logger.info("Listing all questions")
    return jsonify(questions)

@app.route('/question/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Delete a question and its shared context."""
    if question_id not in questions:
        logger.error(f"Question ID {question_id} not found")
        return jsonify({"error": "Question not found"}), 404
    
    logger.info(f"Deleting question {question_id}")
    del questions[question_id]
    if question_id in shared_context:
        del shared_context[question_id]
    
    return jsonify({"status": "success", "message": "Question deleted successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)