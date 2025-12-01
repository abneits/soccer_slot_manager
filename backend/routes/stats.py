from flask import Blueprint, request, jsonify
from models.slot import Slot
from models.user import User
from middleware.auth import require_auth
import re

bp = Blueprint('stats', __name__)

@bp.route('/', methods=['GET'])
@require_auth
def get_statistics():
    """Get all statistics"""
    try:
        # Get all completed slots (with final scores)
        completed_slots = Slot.objects(details__final_score__ne=None, details__final_score__exists=True)
        
        # Get all slots for attendance
        all_slots = Slot.objects()
        
        # Initialize user stats
        user_stats = {}
        
        # Calculate attendance and guests invited
        for slot in all_slots:
            for reg in slot.registrations:
                user_id = str(reg.user_id.id)
                user = reg.user_id
                
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'userId': user_id,
                        'displayName': user.display_name,
                        'firstName': user.first_name,
                        'lastName': user.last_name,
                        'attendance': 0,
                        'wins': 0,
                        'guestsInvited': 0
                    }
                
                user_stats[user_id]['attendance'] += 1
                user_stats[user_id]['guestsInvited'] += len(reg.guests)
        
        # Calculate wins
        for slot in completed_slots:
            if not slot.details or not slot.details.teams or not slot.details.final_score:
                continue
            
            # Parse score
            score_match = re.search(r'(\d+)[–-](\d+)', slot.details.final_score)
            if not score_match:
                continue
            
            score_a = int(score_match.group(1))
            score_b = int(score_match.group(2))
            
            winning_team = None
            if score_a > score_b:
                winning_team = 'teamA'
            elif score_b > score_a:
                winning_team = 'teamB'
            
            if winning_team and winning_team in slot.details.teams:
                for player_name in slot.details.teams[winning_team]:
                    # Find user by display name
                    for reg in slot.registrations:
                        if reg.user_id.display_name == player_name:
                            user_id = str(reg.user_id.id)
                            if user_id in user_stats:
                                user_stats[user_id]['wins'] += 1
                            break
        
        # Calculate sponsored users count
        all_users = User.objects(is_active=True)
        for user in all_users:
            if user.sponsored_by:
                sponsor_id = str(user.sponsored_by.id)
                if sponsor_id in user_stats:
                    user_stats[sponsor_id]['guestsInvited'] += 1
        
        # Convert to list
        stats_list = list(user_stats.values())
        
        # Find top players
        most_wins = max(stats_list, key=lambda x: x['wins']) if stats_list else None
        best_attendance = max(stats_list, key=lambda x: x['attendance']) if stats_list else None
        top_contributor = max(stats_list, key=lambda x: x['guestsInvited']) if stats_list else None
        
        # Sort by attendance
        stats_list.sort(key=lambda x: x['attendance'], reverse=True)
        
        return jsonify({
            'statistics': {
                'mostWins': most_wins,
                'bestAttendance': best_attendance,
                'topContributor': top_contributor
            },
            'allStats': stats_list
        }), 200
        
    except Exception as e:
        print(f"Get statistics error: {e}")
        return jsonify({'error': 'Server error'}), 500

@bp.route('/user/<user_id>', methods=['GET'])
@require_auth
def get_user_statistics(user_id):
    """Get user-specific statistics"""
    try:
        user = User.objects.get(id=user_id)
        
        # Get slots where user participated
        slots = Slot.objects(registrations__user_id=user_id)
        
        attendance = 0
        wins = 0
        guests_invited = 0
        
        for slot in slots:
            # Find user's registration
            user_reg = None
            for reg in slot.registrations:
                if str(reg.user_id.id) == user_id:
                    user_reg = reg
                    break
            
            if user_reg:
                attendance += 1
                guests_invited += len(user_reg.guests)
                
                # Check if user won this match
                if slot.details and slot.details.final_score and slot.details.teams:
                    score_match = re.search(r'(\d+)[–-](\d+)', slot.details.final_score)
                    if score_match:
                        score_a = int(score_match.group(1))
                        score_b = int(score_match.group(2))
                        
                        winning_team = None
                        if score_a > score_b:
                            winning_team = 'teamA'
                        elif score_b > score_a:
                            winning_team = 'teamB'
                        
                        if winning_team and winning_team in slot.details.teams:
                            if user.display_name in slot.details.teams[winning_team]:
                                wins += 1
        
        # Count sponsored users
        sponsored_users = User.objects(sponsored_by=user_id, is_active=True).count()
        
        return jsonify({
            'user': user.to_dict(),
            'statistics': {
                'attendance': attendance,
                'wins': wins,
                'guestsInvited': guests_invited,
                'sponsoredUsers': sponsored_users,
                'totalContributions': guests_invited + sponsored_users
            }
        }), 200
        
    except User.DoesNotExist:
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Get user statistics error: {e}")
        return jsonify({'error': 'Server error'}), 500
