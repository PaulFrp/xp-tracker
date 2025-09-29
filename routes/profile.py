from flask import render_template, session, Blueprint
from utils.db import get_db_connection
from utils.card_data import BADGES, TITLES, skill_to_category
import json

profile_bp= Blueprint("profile", __name__)

@profile_bp.route("/<username>")
def public_profile(username):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = %s", (username,))
        row = c.fetchone()
        if not row:
            return "User not found", 404
        user_id = row[0]


        c.execute("SELECT skill, level FROM progress WHERE user_id = %s", (user_id,))
        stats = c.fetchall()
        user_levels = {skill: level for skill, level in stats}

        # Get selected titles and levels
        c.execute("SELECT selected_titles FROM selected_titles WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        selected_titles = json.loads(row[0]) if row and row[0] else []

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

        # Get selected badges
        c.execute("SELECT selected_badges FROM selected_badges WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        selected_badges = json.loads(row[0]) if row and row[0] else []
        c.execute("SELECT selected_titles FROM selected_titles WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        selected_titles = json.loads(row[0]) if row and row[0] else []
        

        # Collect full badge info
        badge_details = []
        for badge in BADGES.get("badges", []):
            if badge["name"] in selected_badges:
                badge_details.append(badge)
    
    title_info = {}
    for skill, titles in TITLES.items():
        for level, title in titles.items():
            title_info[title] = {
                "skill": skill,
                "level": int(level)
            }

    return render_template(
        "public_profile.html",
        username=username,
        selected_titles=selected_titles,
        unlocked_titles=unlocked_titles,
        badges=badge_details,
        skill_to_category=skill_to_category,
        title_info=title_info,
    )

