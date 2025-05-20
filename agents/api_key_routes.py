"""API routes for managing agent API keys in the MCP Multi-Agent Hub."""
import logging
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from models import ApiKey

# Configure logging
logger = logging.getLogger("api_key_routes")

# Create a Blueprint for API key routes
api_key_routes = Blueprint('api_key_routes', __name__)

@api_key_routes.route('/api/keys', methods=['POST'])
def create_api_key():
    """Create a new API key for an agent.
    
    Expects JSON with:
    - agent_id: string - ID of the agent
    - agent_name: string - Name of the agent
    - description: string (optional) - Description of the API key usage
    - admin_password: string - Password for admin authentication
    
    Returns:
    - JSON with API key details including the key itself
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
            
        # Validate required fields
        required_fields = ['agent_id', 'agent_name', 'admin_password']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Verify admin password (replace with proper authentication in production)
        admin_password = data.get('admin_password')
        expected_password = "admin"  # In production, use a secure password from config or env var
        
        if admin_password != expected_password:
            logger.warning("Invalid admin password used for API key creation")
            return jsonify({"error": "Invalid admin password"}), 401
        
        # Generate a new API key
        api_key = ApiKey(
            id=str(uuid.uuid4()),
            key=ApiKey.generate_key(),
            agent_id=data['agent_id'],
            agent_name=data['agent_name'],
            description=data.get('description', '')
        )
        
        # Add to database
        db.session.add(api_key)
        db.session.commit()
        
        logger.info(f"Created new API key for agent: {api_key.agent_name} ({api_key.agent_id})")
        
        # Return the API key (this is the only time the full key will be returned)
        return jsonify({
            "id": api_key.id,
            "key": api_key.key,  # Include the key in the response
            "agent_id": api_key.agent_id,
            "agent_name": api_key.agent_name,
            "description": api_key.description,
            "created_at": api_key.created_at.isoformat(),
            "is_active": api_key.is_active
        })
        
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_key_routes.route('/api/keys', methods=['GET'])
def list_api_keys():
    """List all API keys (without exposing the actual keys).
    
    Expects query parameter:
    - admin_password: string - Password for admin authentication
    
    Returns:
    - JSON with list of API keys (without the actual key values)
    """
    try:
        # Verify admin password
        admin_password = request.args.get('admin_password')
        expected_password = "admin"  # In production, use a secure password from config or env var
        
        if not admin_password or admin_password != expected_password:
            logger.warning("Invalid admin password used for API key listing")
            return jsonify({"error": "Invalid admin password"}), 401
        
        # Get all API keys
        api_keys = ApiKey.query.all()
        
        # Convert to dictionary for response (excluding the actual key)
        api_keys_dict = [k.to_dict() for k in api_keys]
        
        logger.info(f"Listed {len(api_keys_dict)} API keys")
        return jsonify({"api_keys": api_keys_dict})
        
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_key_routes.route('/api/keys/<key_id>', methods=['DELETE'])
def revoke_api_key(key_id):
    """Revoke (deactivate) an API key.
    
    Expects query parameter:
    - admin_password: string - Password for admin authentication
    
    Returns:
    - JSON with status message
    """
    try:
        # Verify admin password
        admin_password = request.args.get('admin_password')
        expected_password = "admin"  # In production, use a secure password from config or env var
        
        if not admin_password or admin_password != expected_password:
            logger.warning("Invalid admin password used for API key revocation")
            return jsonify({"error": "Invalid admin password"}), 401
        
        # Find the API key
        api_key = ApiKey.query.get(key_id)
        if not api_key:
            logger.error(f"API key not found: {key_id}")
            return jsonify({"error": "API key not found"}), 404
        
        # Deactivate the key
        api_key.is_active = False
        db.session.commit()
        
        logger.info(f"Revoked API key for agent: {api_key.agent_name} ({api_key.agent_id})")
        return jsonify({"status": "success", "message": "API key revoked successfully"})
        
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        return jsonify({"error": str(e)}), 500