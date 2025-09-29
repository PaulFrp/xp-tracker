from flask import render_template, session, Blueprint
from utils.card_data import descriptions, earning_guide, skill_descriptions, skill_guides
from utils.db import get_db_connection

cards_bp = Blueprint("cards", __name__)

@cards_bp.route("/card_red")
def card_red():
    with get_db_connection() as conn:
        c = conn.cursor()
        user_id = session['user_id']

        #Make sure that skills are ordered in the same way as in the dashboard
        c.execute("""
            SELECT skill, category, xp, level 
            FROM progress 
            WHERE category = 'Red' AND user_id = %s 
            ORDER BY 
                CASE skill
                    WHEN 'Strength' THEN 1
                    WHEN 'Endurance' THEN 2
                    WHEN 'Mobility' THEN 3
                    WHEN 'Speed' THEN 4
                END
            """, (user_id,))
        
        stats = c.fetchall()

    return render_template(
        "card_red.html", 
        stats=stats, 
        descriptions=descriptions, 
        earning_guide=earning_guide,
        skill_descriptions=skill_descriptions,
        skill_guides=skill_guides
    )

@cards_bp.route("/card_blue")
def card_blue():
    with get_db_connection() as conn:
        c = conn.cursor()
        user_id = session['user_id']

        #Make sure that skills are ordered in the same way as in the dashboard
        c.execute("""
            SELECT skill, category, xp, level 
            FROM progress 
            WHERE category = 'Blue' AND user_id = %s 
            ORDER BY 
                CASE skill
                    WHEN 'Intelligence' THEN 1
                    WHEN 'Concentration' THEN 2
                    WHEN 'Logic' THEN 3
                    WHEN 'Creativity' THEN 4
                END
            """, (user_id,))
        stats = c.fetchall()

    return render_template(
        "card_blue.html", 
        stats=stats, 
        descriptions=descriptions, 
        earning_guide=earning_guide,
        skill_descriptions=skill_descriptions,
        skill_guides=skill_guides
    )

@cards_bp.route("/card_green", endpoint="card_green")
def card_green():
    with get_db_connection() as conn:
        c = conn.cursor()
        user_id = session['user_id']
        
        #Make sure that skills are ordered in the same way as in the dashboard
        c.execute("""
            SELECT skill, category, xp, level 
            FROM progress 
            WHERE category = 'Green' AND user_id = %s 
            ORDER BY 
                CASE skill
                    WHEN 'Dexterity' THEN 1
                    WHEN 'Vitality' THEN 2
                    WHEN 'Recovery' THEN 3
                    WHEN 'Affection' THEN 4
                END
            """, (user_id,))
        stats = c.fetchall()

    return render_template(
        "card_green.html", 
        stats=stats, 
        descriptions=descriptions, 
        earning_guide=earning_guide,
        skill_descriptions=skill_descriptions,
        skill_guides=skill_guides
    )

@cards_bp.route("/card_gold", endpoint="card_gold")
def card_gold():
    with get_db_connection() as conn:
        c = conn.cursor()
        user_id = session['user_id']
        
        #Make sure that skills are ordered in the same way as in the dashboard
        c.execute("""
            SELECT skill, category, xp, level 
            FROM progress 
            WHERE category = 'Gold' AND user_id = %s 
            ORDER BY 
                CASE skill
                    WHEN 'Discipline' THEN 1
                    WHEN 'Planning' THEN 2
                    WHEN 'Reflection' THEN 3
                    WHEN 'Good deeds' THEN 4
                END
            """, (user_id,))
        stats = c.fetchall()

    return render_template(
        "card_gold.html", 
        stats=stats, 
        descriptions=descriptions, 
        earning_guide=earning_guide,
        skill_descriptions=skill_descriptions,
        skill_guides=skill_guides
        )