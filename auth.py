"""Authentication utilities for the MCP Multi-Agent Hub."""
import logging
from functools import wraps
from datetime import datetime
from flask import request, jsonify, g
from models import ApiKey
from app import db

# Configure logging
logger = logging.getLogger("auth")

def require_api_key(f):
    """Decorator to require API key authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from headers
        api_key = request.headers.get('X-API-Key')
        
        # Check if API key is provided
        if not api_key:
            logger.warning("Missing API key in request")
            return jsonify({"error": "API key is required"}), 401
            
        # Look up the API key in the database
        key_entry = ApiKey.query.filter_by(key=api_key, is_active=True).first()
        
        # Check if the API key is valid
        if not key_entry:
            logger.warning(f"Invalid or inactive API key used: {api_key[:5]}...")
            return jsonify({"error": "Invalid or inactive API key"}), 401
            
        # Update last used timestamp
        key_entry.last_used_at = datetime.utcnow()
        db.session.commit()
        
        # Set agent info in Flask's g object for access in the route function
        g.agent_id = key_entry.agent_id
        g.agent_name = key_entry.agent_name
        
        logger.info(f"Authenticated request from agent: {key_entry.agent_name} ({key_entry.agent_id})")
        return f(*args, **kwargs)
        
    return decorated_function

def get_current_agent():
    """Get information about the authenticated agent.
    
    Returns:
        Dict with agent_id and agent_name, or None if not authenticated
    """
    if hasattr(g, 'agent_id') and hasattr(g, 'agent_name'):
        return {
            "agent_id": g.agent_id,
            "agent_name": g.agent_name
        }
    return None