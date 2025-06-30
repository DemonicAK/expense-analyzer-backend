import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import current_app


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_token(user_id: str, email: str) -> str:
    """Generate JWT token for user"""
    payload = {
        'userId': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS']),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')


def decode_token(token: str) -> dict:
    """Decode JWT token"""
    return jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])