from flask import session, request, jsonify, Blueprint
from utils.db import get_db_connection
from utils.stats_tracker import update_daily_stats, update_streak

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
        # XP needed to go from level N to level N+1: 80 + 12 * N * (N + 1) / 2
        while True:
            xp_needed = 80 + 12 * (current_level * (current_level + 1)) // 2
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

        # Track daily stats and streaks
        if current_level > old_level:
            update_streak(user_id, skill)
        update_daily_stats(user_id, xp_added=xp_to_add)

        # Calculate next milestone
        xp_for_next = 80 + 12 * (current_level * (current_level + 1)) // 2
        xp_remaining = max(0, xp_for_next - new_xp)

        return jsonify({
            "success": True,
            "old_level": old_level,
            "current_level": current_level,
            "skill": skill,
            "new_xp": new_xp,
            "xp_for_next": xp_for_next,
            "xp_remaining": xp_remaining,
            "leveled_up": current_level > old_level
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
            # Calculate the XP needed for the previous level
            current_level -= 1
            xp_needed_for_previous_level = 80 + 12 * (current_level * (current_level + 1)) // 2
            new_xp += xp_needed_for_previous_level

        # Ensure XP doesn't go below 0 and level doesn't go below 1
        if new_xp < 0 and current_level == 1:
            new_xp = 0

        cursor.execute(
            "UPDATE progress SET xp = %s, level = %s WHERE user_id = %s AND skill = %s",
            (new_xp, current_level, user_id, skill)
        )
        conn.commit()
        conn.close()

        # Calculate next milestone
        xp_for_next = 80 + 12 * (current_level * (current_level + 1)) // 2
        xp_remaining = max(0, xp_for_next - new_xp)

        return jsonify({
            "success": True, 
            "current_level": current_level, 
            "new_xp": new_xp,
            "xp_for_next": xp_for_next,
            "xp_remaining": xp_remaining
        })

    else:
        conn.close()
        return jsonify(success=False, error="Skill not found"), 404


@xp_bp.route('/get_daily_stats', methods=['GET'])
def get_daily_stats_route():
    """Get current daily stats without reloading page"""
    from utils.stats_tracker import get_daily_stats
    user_id = session['user_id']
    stats = get_daily_stats(user_id)
    return jsonify(stats)