from flask import session, request, jsonify, Blueprint
from utils.db import get_db_connection

xp_bp = Blueprint("xp", __name__)

@xp_bp.route('/add_xp', methods=['POST'])
def add_xp():
    data = request.get_json()
    skill = data.get('skill')
    xp_to_add = int(data.get('xp', 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']

    # Fetch current XP and level
    cursor.execute("SELECT xp, level FROM progress WHERE user_id = %s AND skill = %s", (user_id, skill))
    row = cursor.fetchone()

    if row:
        current_xp, current_level = row
        old_level = current_level
        new_xp = current_xp + xp_to_add

        # Level-up loop with increasing XP requirement per level
        while True:
            xp_needed = 100*current_level + 25 * sum(range(1, current_level))
            if new_xp >= xp_needed:
                new_xp -= xp_needed
                current_level += 1
            else:
                break

        # Update database
        cursor.execute(
            "UPDATE progress SET xp = %s, level = %s WHERE user_id = %s AND skill = %s",
            (new_xp, current_level, user_id, skill)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "old_level": old_level,
            "current_level": current_level,
            "skill": skill
        })

    else:
        conn.close()
        return jsonify(success=False, error="Skill not found"), 404


    
@xp_bp.route('/delete_xp', methods=['POST'])
def delete_xp():
    data = request.get_json()
    skill = data.get('skill')
    xp_to_delete = int(data.get('xp', 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']

    # Fetch current XP and level
    cursor.execute("SELECT xp, level FROM progress WHERE user_id = %s AND skill = %s", (user_id, skill))
    row = cursor.fetchone()

    if row:
        current_xp, current_level = row
        new_xp = current_xp - xp_to_delete
        
        # Level-down logic with increasing XP per level
        while new_xp < 0 and current_level > 1:
            # Calculate the XP needed for the current level
            current_level -= 1
            xp_needed_for_last_level = 100  + 25 * sum(range(1, current_level))
            new_xp += xp_needed_for_last_level

        # Ensure XP doesn't go below 0 and level doesn't go below 1
        if new_xp < 0 and current_level == 1:
            new_xp = 0

        cursor.execute(
            "UPDATE progress SET xp = %s, level = %s WHERE user_id = %s AND skill = %s",
            (new_xp, current_level, user_id, skill)
        )
        conn.commit()
        conn.close()

        return jsonify(success=True, current_level=current_level, new_xp=new_xp)

    else:
        conn.close()
        return jsonify(success=False, error="Skill not found"), 404