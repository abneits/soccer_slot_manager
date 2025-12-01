from flask import Blueprint, request, jsonify
from models.user import User
from middleware.auth import generate_token, require_auth
from email_validator import validate_email, EmailNotValidError

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    """Register new user (requires sponsor)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'firstName', 'lastName', 'displayName', 'sponsorId']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate email
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            return jsonify({'error': 'Invalid email address'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        existing_user = User.objects(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        existing_display = User.objects(display_name=data['displayName']).first()
        if existing_display:
            return jsonify({'error': 'Display name already taken'}), 400
        
        # Verify sponsor exists
        try:
            sponsor = User.objects.get(id=data['sponsorId'])
        except:
            return jsonify({'error': 'Invalid sponsor'}), 400
        
        # Create new user
        user = User(
            email=data['email'].lower(),
            first_name=data['firstName'],
            last_name=data['lastName'],
            display_name=data['displayName'],
            sponsored_by=sponsor
        )
        user.set_password(data['password'])
        user.save()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Server error during registration'}), 500

@bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.objects(email=data['email'].lower()).first()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check password
        if not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 401
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Server error during login'}), 500

@bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user"""
    try:
        return jsonify({'user': request.current_user.to_dict()}), 200
    except Exception as e:
        print(f"Get current user error: {e}")
        return jsonify({'error': 'Server error'}), 500
