from flask import Blueprint, request, jsonify
from models.slot import Slot, Registration, SlotDetails
from models.user import User
from middleware.auth import require_auth
from datetime import datetime, timedelta

bp = Blueprint('slots', __name__)

def get_next_wednesday():
    """Get next Wednesday at 19:00"""
    today = datetime.now()
    days_until_wednesday = (2 - today.weekday()) % 7
    if days_until_wednesday == 0 and today.hour >= 19:
        days_until_wednesday = 7
    
    next_wednesday = today + timedelta(days=days_until_wednesday if days_until_wednesday != 0 else 7)
    next_wednesday = next_wednesday.replace(hour=19, minute=0, second=0, microsecond=0)
    return next_wednesday

@bp.route('/', methods=['GET'])
@require_auth
def get_all_slots():
    """Get all slots (paginated)"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit
        
        slots = Slot.objects().order_by('-date').skip(skip).limit(limit)
        total = Slot.objects().count()
        
        # Populate user info for each slot
        slots_data = []
        for slot in slots:
            slot_dict = slot.to_dict()
            for reg in slot_dict['registrations']:
                if reg['userId']:
                    user_id = reg['userId']['_id']
                    try:
                        user = User.objects.get(id=user_id)
                        reg['userId'] = user.to_dict()
                    except:
                        pass
            slots_data.append(slot_dict)
        
        return jsonify({
            'slots': slots_data,
            'pagination': {
                'total': total,
                'page': page,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except Exception as e:
        print(f"Get slots error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/next', methods=['GET'])
@require_auth
def get_next_slot():
    """Get next Wednesday slot"""
    try:
        next_wednesday = get_next_wednesday()
        
        # Find or create slot
        slot = Slot.objects(date=next_wednesday).first()
        if not slot:
            slot = Slot(date=next_wednesday, registrations=[])
            slot.save()
        
        # Populate user info
        slot_dict = slot.to_dict()
        for reg in slot_dict['registrations']:
            if reg['userId']:
                user_id = reg['userId']['_id']
                try:
                    user = User.objects.get(id=user_id)
                    reg['userId'] = user.to_dict()
                except:
                    pass
        
        return jsonify({'slot': slot_dict}), 200
    except Exception as e:
        print(f"Get next slot error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/<slot_id>', methods=['GET'])
@require_auth
def get_slot_by_id(slot_id):
    """Get slot by ID"""
    try:
        slot = Slot.objects.get(id=slot_id)
        
        # Populate user info
        slot_dict = slot.to_dict()
        for reg in slot_dict['registrations']:
            if reg['userId']:
                user_id = reg['userId']['_id']
                try:
                    user = User.objects.get(id=user_id)
                    reg['userId'] = user.to_dict()
                except:
                    pass
        
        return jsonify({'slot': slot_dict}), 200
    except Slot.DoesNotExist:
        return jsonify({'error': 'Slot not found'}), 404
    except Exception as e:
        print(f"Get slot error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/<slot_id>/register', methods=['POST'])
@require_auth
def register_for_slot(slot_id):
    """Register for a slot"""
    try:
        data = request.get_json()
        guests = data.get('guests', [])
        
        slot = Slot.objects.get(id=slot_id)
        user = request.current_user
        
        # Check if user already registered
        for reg in slot.registrations:
            if str(reg.user_id.id) == request.user_id:
                return jsonify({'error': 'Already registered for this slot'}), 400
        
        # Add registration
        registration = Registration(
            user_id=user,
            guests=[g.strip() for g in guests if g and g.strip()]
        )
        slot.registrations.append(registration)
        slot.save()
        
        # Populate user info
        slot_dict = slot.to_dict()
        for reg in slot_dict['registrations']:
            if reg['userId']:
                user_id = reg['userId']['_id']
                try:
                    u = User.objects.get(id=user_id)
                    reg['userId'] = u.to_dict()
                except:
                    pass
        
        return jsonify({
            'message': 'Successfully registered',
            'slot': slot_dict
        }), 200
    except Slot.DoesNotExist:
        return jsonify({'error': 'Slot not found'}), 404
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/<slot_id>/register', methods=['PUT'])
@require_auth
def update_registration(slot_id):
    """Update registration (edit guests)"""
    try:
        data = request.get_json()
        guests = data.get('guests', [])
        
        slot = Slot.objects.get(id=slot_id)
        
        # Find user's registration
        registration = None
        for reg in slot.registrations:
            if str(reg.user_id.id) == request.user_id:
                registration = reg
                break
        
        if not registration:
            return jsonify({'error': 'Registration not found'}), 404
        
        # Update guests
        registration.guests = [g.strip() for g in guests if g and g.strip()]
        slot.save()
        
        # Populate user info
        slot_dict = slot.to_dict()
        for reg in slot_dict['registrations']:
            if reg['userId']:
                user_id = reg['userId']['_id']
                try:
                    u = User.objects.get(id=user_id)
                    reg['userId'] = u.to_dict()
                except:
                    pass
        
        return jsonify({
            'message': 'Registration updated',
            'slot': slot_dict
        }), 200
    except Slot.DoesNotExist:
        return jsonify({'error': 'Slot not found'}), 404
    except Exception as e:
        print(f"Update registration error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/<slot_id>/register', methods=['DELETE'])
@require_auth
def cancel_registration(slot_id):
    """Cancel registration"""
    try:
        slot = Slot.objects.get(id=slot_id)
        
        # Remove user's registration
        slot.registrations = [reg for reg in slot.registrations if str(reg.user_id.id) != request.user_id]
        slot.save()
        
        # Populate user info
        slot_dict = slot.to_dict()
        for reg in slot_dict['registrations']:
            if reg['userId']:
                user_id = reg['userId']['_id']
                try:
                    u = User.objects.get(id=user_id)
                    reg['userId'] = u.to_dict()
                except:
                    pass
        
        return jsonify({
            'message': 'Registration cancelled',
            'slot': slot_dict
        }), 200
    except Slot.DoesNotExist:
        return jsonify({'error': 'Slot not found'}), 404
    except Exception as e:
        print(f"Cancel registration error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/<slot_id>/details', methods=['PUT'])
@require_auth
def update_slot_details(slot_id):
    """Update slot details (teams and score)"""
    try:
        data = request.get_json()
        slot = Slot.objects.get(id=slot_id)
        
        if not slot.details:
            slot.details = SlotDetails()
        
        if 'teams' in data:
            slot.details.teams = data['teams']
        
        if 'finalScore' in data:
            slot.details.final_score = data['finalScore']
        
        slot.save()
        
        # Populate user info
        slot_dict = slot.to_dict()
        for reg in slot_dict['registrations']:
            if reg['userId']:
                user_id = reg['userId']['_id']
                try:
                    u = User.objects.get(id=user_id)
                    reg['userId'] = u.to_dict()
                except:
                    pass
        
        return jsonify({
            'message': 'Slot details updated',
            'slot': slot_dict
        }), 200
    except Slot.DoesNotExist:
        return jsonify({'error': 'Slot not found'}), 404
    except Exception as e:
        print(f"Update slot details error: {e}")
        return jsonify({'error': 'Server error'}), 500
