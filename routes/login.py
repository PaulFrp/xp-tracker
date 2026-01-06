from flask import Blueprint, render_template, request, redirect, url_for, session
from utils.db import get_db_connection
from utils.reset_challenges import reset_daily_challenges_if_needed

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = %s AND password = %s", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session.permanent = True
            return redirect(url_for('dashboard.dashboard'))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@login_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login.login'))

@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        c = conn.cursor()

        # Insert new user and get ID
        c.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, password)
        )
        user_id = c.fetchone()[0]

        # Initialize user skills
        skills = [
            ("Strength", "Red"), ("Endurance", "Red"), ("Mobility", "Red"), ("Speed", "Red"),
            ("Intelligence", "Blue"), ("Concentration", "Blue"), ("Logic", "Blue"), ("Creativity", "Blue"),
            ("Dexterity", "Green"), ("Vitality", "Green"), ("Recovery", "Green"), ("Affection", "Green"),
            ("Discipline", "Gold"), ("Planning", "Gold"), ("Reflection", "Gold"), ("Good deeds", "Gold")
        ]
        for skill, category in skills:
            c.execute(
                "INSERT INTO progress (user_id, skill, category) VALUES (%s, %s, %s)",
                (user_id, skill, category)
            )

        conn.commit()
        conn.close()

        # Immediately assign today's daily challenges for this new user
        reset_daily_challenges_if_needed()  # modified function to accept user_id

        return redirect(url_for('login.login'))

    return render_template("register.html")