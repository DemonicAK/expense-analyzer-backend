from functools import wraps
from flask import request, jsonify, current_app,g
import jwt
from expense_analyzer_backend.models.user import User
import logging
from ..models.user import User # Replace with your actual User model import

logger = logging.getLogger(__name__)


def authenticate_token(f):
    """Authentication middleware decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'message': 'Access token required'}), 401
            
            # Extract token
            token_parts = auth_header.split(' ')
            if len(token_parts) != 2 or token_parts[0] != 'Bearer':
                return jsonify({'message': 'Invalid token format'}), 401
            
            token = token_parts[1]
            
            # Decode token
            decoded = jwt.decode(
                token,
                current_app.config['JWT_SECRET'],
                algorithms=['HS256']
            )
            
            # Get user
            user = User.find_by_id(decoded['userId'])
            if not user:
                return jsonify({'message': 'User not found'}), 401
            
            # Add user to request context
            g.user = user
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return jsonify({'message': 'Token expired'}), 403
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return jsonify({'message': 'Invalid token'}), 403
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return jsonify({'message': 'Authentication failed'}), 403
    
    return decorated_function


def optional_auth(f):
    """Optional authentication middleware"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                token_parts = auth_header.split(' ')
                if len(token_parts) == 2 and token_parts[0] == 'Bearer':
                    token = token_parts[1]
                    decoded = jwt.decode(
                        token,
                        current_app.config['JWT_SECRET'],
                        algorithms=['HS256']
                    )
                    user = User.find_by_id(decoded['userId'])
                    if user:
                        g.user = user
            
            return f(*args, **kwargs)
            
        except Exception:
            # Ignore auth errors for optional auth
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function
