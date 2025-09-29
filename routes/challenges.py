from flask import session, request, jsonify, Blueprint
from utils.db import get_db_connection

challenges_bp = Blueprint("challenges", __name__)

@challenges_bp.route('/daily_challenges', methods=['POST'])
def daily_challenges():
    data = request.get_json()
    challenge = data.get('challenge')
    completed = bool(data.get('completed', 1))  # Convert to boolean

    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute(
        "UPDATE daily SET completed = %s WHERE challenge = %s AND user_id = %s", 
        (completed, challenge, user_id)
    )
    conn.commit()
    conn.close()
    return jsonify(success=True)
