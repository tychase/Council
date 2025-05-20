import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, redirect, url_for
from app import app, db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("flask_app")

# Import models
from models import Stage, Question, Context

# Create database tables
with app.app_context():
    db.create_all()
    
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
    
    logger.info(f"Creating new question: '{question_text}' with ID: {question_id}")
    
    # Create question object
    new_question = Question(
        id=question_id,
        text=question_text
    )
    
    # Initialize shared context
    new_context = Context(
        id=str(uuid.uuid4()),
        question_id=question_id,
        responses={},
        critiques={},
        research={},
        conclusions={}
    )
    
    # Add to database
    db.session.add(new_question)
    db.session.add(new_context)
    db.session.commit()
    
    return jsonify({"question_id": question_id, "message": "Question created successfully"})

@app.route('/submit/<question_id>', methods=['POST'])
def submit_agent_response(question_id):
    """Submit an agent's response, critique, research, or conclusion for a question."""
    # Find the context in the database
    context = Context.query.filter_by(question_id=question_id).first()
    if not context:
        logger.error(f"Question ID {question_id} not found")
        return jsonify({"error": "Question not found"}), 404
    
    # Parse submission from JSON
    submission = request.json
    if submission:
        agent_id = submission.get('agent_id')
        agent_name = submission.get('agent_name')
        stage = submission.get('stage')
        payload = submission.get('payload', {})
    else:
        return jsonify({"error": "Invalid submission data"}), 400
    
    logger.info(f"Received {stage} from agent {agent_id} for question {question_id}")
    
    # Add agent name to payload if provided
    if agent_name:
        payload["agent_name"] = agent_name
    
    # Update shared context based on submission stage
    if stage == "response":
        responses = context.responses or {}
        responses[agent_id] = payload
        context.responses = responses
    elif stage == "critique":
        critiques = context.critiques or {}
        critiques[agent_id] = payload
        context.critiques = critiques
    elif stage == "research":
        research = context.research or {}
        research[agent_id] = payload
        context.research = research
    elif stage == "conclusion":
        conclusions = context.conclusions or {}
        conclusions[agent_id] = payload
        context.conclusions = conclusions
    else:
        logger.warning(f"Unknown stage: {stage}")
        return jsonify({"error": "Invalid stage"}), 400
    
    # Save changes to database
    db.session.commit()
    
    logger.info(f"Updated context for question {question_id}, stage: {stage}")
    return jsonify({"status": "success", "message": f"{stage} recorded successfully"})

@app.route('/context/<question_id>')
def get_context(question_id):
    """Retrieve the shared context for a specific question."""
    context = Context.query.filter_by(question_id=question_id).first()
    if not context:
        logger.error(f"Question ID {question_id} not found")
        return jsonify({"error": "Question not found"}), 404
    
    logger.info(f"Retrieving context for question {question_id}")
    return jsonify(context.to_dict())

@app.route('/questions')
def list_questions():
    """List all questions in the system."""
    logger.info("Listing all questions")
    questions = Question.query.all()
    return jsonify({q.id: q.to_dict() for q in questions})

@app.route('/question/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Delete a question and its shared context."""
    question = Question.query.get(question_id)
    if not question:
        logger.error(f"Question ID {question_id} not found")
        return jsonify({"error": "Question not found"}), 404
    
    logger.info(f"Deleting question {question_id}")
    db.session.delete(question)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Question deleted successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)