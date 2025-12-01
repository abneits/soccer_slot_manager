from functools import wraps
from flask import request, jsonify
import jwt
import os
from models.user import User

def generate_token(user_id):
    """Generate JWT token for user"""
    payload = {
        'userId': str(user_id),
        'exp': None  # Token doesn't expire (7 days in production)
    }
    token = jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')
    return token

def verify_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        return payload.get('userId')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authentication token, access denied'}), 401
        
        # Extract token
        try:
            token = auth_header.replace('Bearer ', '')
        except:
            return jsonify({'error': 'Invalid token format'}), 401
        
        # Verify token
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token is not valid'}), 401
        
        # Find user
        try:
            user = User.objects.get(id=user_id)
            if not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
        except User.DoesNotExist:
            return jsonify({'error': 'User not found'}), 401
        
        # Attach user to request
        request.current_user = user
        request.user_id = str(user.id)
        
        return f(*args, **kwargs)
    
    return decorated_function
