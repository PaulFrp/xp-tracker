from flask import render_template, session, redirect, url_for, request, jsonify, Blueprint
from utils.db import get_db_connection
from utils.card_data import BADGES
import json

badges_bp = Blueprint("badges", __name__)

@badges_bp.route("/badges")
def badges():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login.login'))

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT skill, level FROM progress WHERE user_id = %s", (user_id,))
        stats = c.fetchall()
        c.execute("SELECT selected_badges FROM selected_badges WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        current_selected_badges = json.loads(row[0]) if row and row[0] else []

    unlocked_badges = []

    for badge in BADGES.get("badges", []):
        unlock_condition = badge.get("unlock_condition", {})
        skill = unlock_condition.get("skill")
        required_level = unlock_condition.get("level")

        # Check if the user meets the unlock condition
        for skill_name, level in stats:
            if skill_name == skill and level >= required_level:
                unlocked_badges.append({
                    "name": badge.get("name"),
                    "description": badge.get("description"),
                    "image": badge.get("image"),
                    "category": unlock_condition.get("skill"),
                })

    skill_to_category= {
        "Strength": "Red", "Endurance": "Red", "Mobility": "Red", "Speed": "Red",
        "Intelligence": "Blue", "Concentration": "Blue", "Logic": "Blue", "Creativity": "Blue",
        "Dexterity": "Green", "Vitality": "Green", "Recovery": "Green", "Affection": "Green",
        "Discipline": "Gold", "Planning": "Gold", "Reflection": "Gold", "Good deeds": "Gold"
    }

    return render_template("badges.html", unlocked_badges=unlocked_badges, skill_to_category=skill_to_category, user_id=user_id, current_selected_badges=current_selected_badges)


@badges_bp.route('/update_selected_badges', methods=['POST'])
def update_selected_badges():
    if request.method == 'POST':
        data = request.get_json()
        user_id = session.get('user_id')
        badge = data['title'] 
        action = data['action']

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT selected_badges FROM selected_badges WHERE user_id = %s", (user_id,))
            row = c.fetchone()

            if row and row[0]:
                selected_badges = json.loads(row[0])
            else:
                selected_badges = []

            # Add or remove the title based on the action
            if action == 'add' and badge not in selected_badges:
                selected_badges.append(badge)
            elif action == 'remove' and badge in selected_badges:
                selected_badges.remove(badge)

            # Save the updated selection back into the database
            selected_json = json.dumps(selected_badges)

            c.execute("""
                INSERT INTO selected_badges (user_id, selected_badges) 
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET selected_badges = EXCLUDED.selected_badges
            """,(user_id, selected_json))
            conn.commit()

    return jsonify({"status": "success"}), 200