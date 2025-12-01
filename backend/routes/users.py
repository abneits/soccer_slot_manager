from flask import Blueprint, request, jsonify
from models.user import User
from middleware.auth import require_auth

bp = Blueprint('users', __name__)

@bp.route('/', methods=['GET'])
@require_auth
def get_all_users():
    """Get all active users"""
    try:
        users = User.objects(is_active=True).order_by('display_name')
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/<user_id>', methods=['GET'])
@require_auth
def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        user = User.objects.get(id=user_id)
        user_dict = user.to_dict()
        
        # Populate sponsor info
        if user.sponsored_by:
            sponsor = user.sponsored_by
            user_dict['sponsoredBy'] = {
                'displayName': sponsor.display_name,
                'firstName': sponsor.first_name,
                'lastName': sponsor.last_name
            }
        
        return jsonify({'user': user_dict}), 200
    except User.DoesNotExist:
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/<user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    """Update user profile"""
    try:
        # Only allow user to update their own profile
        if user_id != request.user_id:
            return jsonify({'error': 'Not authorized to update this profile'}), 403
        
        data = request.get_json()
        user = User.objects.get(id=user_id)
        
        # Check if display name is already taken
        if 'displayName' in data and data['displayName'] != user.display_name:
            existing = User.objects(display_name=data['displayName']).first()
            if existing:
                return jsonify({'error': 'Display name already taken'}), 400
            user.display_name = data['displayName']
        
        # Update fields
        if 'firstName' in data:
            user.first_name = data['firstName']
        if 'lastName' in data:
            user.last_name = data['lastName']
        
        user.save()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except User.DoesNotExist:
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Update user error: {e}")
        return jsonify({'error': 'Server error'}), 500
