from flask import session, request, jsonify, Blueprint
from utils.db import get_db_connection
from utils.stats_tracker import update_daily_stats

challenges_bp = Blueprint("challenges", __name__)

@challenges_bp.route('/daily_challenges', methods=['POST'])
def daily_challenges():
    data = request.get_json()
    challenge = data.get('challenge')
    completed = bool(data.get('completed', 1))  # Convert to boolean

    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    
    # Update the challenge state
    cursor.execute(
        "UPDATE daily SET completed = %s WHERE challenge = %s AND user_id = %s", 
        (completed, challenge, user_id)
    )
    
    # Get total completed challenges count
    cursor.execute(
        "SELECT COUNT(*) FROM daily WHERE user_id = %s AND completed = TRUE",
        (user_id,)
    )
    completed_count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return jsonify(success=True, completed_count=completed_count)
