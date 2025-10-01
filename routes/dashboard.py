import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Blueprint
from utils.db import get_db_connection
from utils.reset_challenges import reset_daily_challenges_if_needed
from utils.card_data import TITLES, BADGES, skill_to_category, skill_order
from utils.challenge_bank import CHALLENGE_BANK

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('login.login'))

@dashboard_bp.route('/dashboard', endpoint="dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))
    
    reset_daily_challenges_if_needed() 
    user_id = session['user_id']
    # Query skills for this user only
    with get_db_connection() as conn:
        c = conn.cursor()

        #Make sure that skills are ordered in the same way as in the dashboard
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

        c.execute("SELECT challenge, completed FROM daily WHERE user_id = %s", (user_id,))
        daily_challenges = c.fetchall()
        c.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_data = c.fetchone()
        if user_data is None:
            return redirect(url_for('login.login'))  # or render an error page
        username = user_data[0]

        c.execute("SELECT selected_titles FROM selected_decorations WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        if row and row[0]:
            selected_titles = json.loads(row[0])
        else:
            selected_titles = []
        c.execute("SELECT selected_badges FROM selected_decorations WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        if row and row[0]:
            selected_badges = json.loads(row[0])
        else:
            selected_badges = []

    title_info = {}
    for skill, titles in TITLES.items():
        for level, title in titles.items():
            title_info[title] = {
                "skill": skill,
                "level": int(level)
            }

    badge_images = {}
    for badge in BADGES.get("badges", []):
        badge_images[badge["name"]] = badge["image"]

    return render_template(
        "dashboard.html",
        stats=stats,
        daily_challenges=daily_challenges,
        challenge_bank=CHALLENGE_BANK,
        username=username,
        selected_titles=selected_titles,
        selected_badges=selected_badges,
        title_info=title_info,
        badge_images=badge_images,
        skill_to_category=skill_to_category
    )
