from flask import render_template, session, Blueprint, abort
from utils.card_data import descriptions, earning_guide, skill_descriptions, skill_guides
from utils.db import get_db_connection

cards_bp = Blueprint("cards", __name__)

# Order definitions (so your SQL queries are still consistent)
CATEGORY_ORDERS = {
    "Red": ["Strength", "Endurance", "Mobility", "Speed"],
    "Blue": ["Intelligence", "Concentration", "Logic", "Creativity"],
    "Green": ["Dexterity", "Vitality", "Recovery", "Affection"],
    "Gold": ["Discipline", "Planning", "Reflection", "Good deeds"]
}

@cards_bp.route("/card_<string:category>")
def card_category(category):
    category = category.capitalize()  # ensure first letter is uppercase
    if category not in CATEGORY_ORDERS:
        abort(404)

    with get_db_connection() as conn:
        c = conn.cursor()
        user_id = session['user_id']

        # Dynamic ORDER BY CASE
        order_cases = " ".join(
            f"WHEN '{skill}' THEN {i+1}"
            for i, skill in enumerate(CATEGORY_ORDERS[category])
        )

        query = f"""
            SELECT skill, category, xp, level
            FROM progress
            WHERE category = %s AND user_id = %s
            ORDER BY CASE skill {order_cases} END
        """
        c.execute(query, (category, user_id))
        stats = c.fetchall()

    return render_template(
        "card.html",  
        category=category,
        stats=stats,
        descriptions=descriptions,
        earning_guide=earning_guide,
        skill_descriptions=skill_descriptions,
        skill_guides=skill_guides
    )
