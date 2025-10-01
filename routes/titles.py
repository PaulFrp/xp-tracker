from flask import render_template, session, redirect, url_for, request, jsonify, Blueprint
from utils.db import get_db_connection
from utils.card_data import TITLES
import json

titles_bp = Blueprint("titles", __name__)

@titles_bp.route('/titles')
def titles():
    user_id = session.get('user_id')    
    if not user_id:
        return redirect(url_for('login.login'))

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT skill, level FROM progress WHERE user_id = %s", (user_id,))
        stats = c.fetchall()
        c.execute("SELECT selected_titles FROM selected_decorations WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        current_selected_titles = json.loads(row[0]) if row and row[0] else []

    user_levels = {skill: level for skill, level in stats}
    unlocked_titles = {}

    for skill, level in user_levels.items():
        available_titles = TITLES.get(skill, {})
        unlocked = [
            (int(req_level), title)
            for req_level, title in available_titles.items()
            if level >= int(req_level)
        ]
        if unlocked:
            unlocked_titles[skill] = sorted(unlocked)
    
    skill_to_category= {
        "Strength": "Red", "Endurance": "Red", "Mobility": "Red", "Speed": "Red",
        "Intelligence": "Blue", "Concentration": "Blue", "Logic": "Blue", "Creativity": "Blue",
        "Dexterity": "Green", "Vitality": "Green", "Recovery": "Green", "Affection": "Green",
        "Discipline": "Gold", "Planning": "Gold", "Reflection": "Gold", "Good deeds": "Gold"
    }

    return render_template("titles.html", unlocked_titles=unlocked_titles, skill_to_category=skill_to_category, current_selected_titles=current_selected_titles,user_id=user_id)


@titles_bp.route('/update_selected_titles', methods=['POST'])
def update_selected_titles():
    if request.method == 'POST':
        data = request.get_json()
        user_id = session.get('user_id')
        title = data['title']
        action = data['action']
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT selected_titles FROM selected_decorations WHERE user_id = %s", (user_id,))
            row = c.fetchone()

            if row and row[0]:
                selected_titles = json.loads(row[0])
            else:
                selected_titles = []

            # Add or remove the title based on the action
            if action == 'add' and title not in selected_titles:
                selected_titles.append(title)
            elif action == 'remove' and title in selected_titles:
                selected_titles.remove(title)

            # Save the updated selection back into the database
            selected_json = json.dumps(selected_titles)
            c.execute("""
                INSERT INTO selected_decorations (user_id, selected_titles)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET selected_titles = EXCLUDED.selected_titles
            """, (user_id, selected_json))
            conn.commit()

    return jsonify({"status": "success"}), 200