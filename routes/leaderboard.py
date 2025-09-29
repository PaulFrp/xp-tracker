from flask import render_template, session, redirect, url_for, Blueprint
from utils.db import get_db_connection
from utils.card_data import skill_order

leaderboard_bp = Blueprint("leaderboard", __name__)

@leaderboard_bp.route("/leaderboard")
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))
    
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch all users and their stats
    c.execute("SELECT id, username FROM users")
    user_data = c.fetchall()

    leaderboard_data = []
    for user_id, username in user_data:
        placeholders = ','.join(['%s'] * len(skill_order))
        c.execute(f"""
            SELECT skill, category, xp, level 
            FROM progress 
            WHERE user_id = %s 
            AND skill IN ({placeholders})
            ORDER BY CASE skill
                {''.join([f"WHEN '{skill}' THEN {i} " for i, skill in enumerate(skill_order)])}
                ELSE 999 END
        """, (user_id, *skill_order))
        stats = c.fetchall()
        leaderboard_data.append({
            "username": username,
            "stats": stats,
            "overall_xp": sum(xp for _, _, xp, _ in stats),
            "overall_level": sum(level for _, _, _, level in stats) - 16 if stats else 0,
        })

    leaderboard_data.sort(key=lambda u: u["overall_level"], reverse=True)


    conn.close()
    return render_template("leaderboard.html", leaderboard_data=leaderboard_data)