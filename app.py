

from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import psycopg2
import urllib.parse as urlparse
from dotenv import load_dotenv
import os
import json


with open(os.path.join(os.path.dirname(__file__), 'titles.json')) as f:
    TITLES = json.load(f)

with open(os.path.join(os.path.dirname(__file__), 'badges.json')) as f:
    BADGES = json.load(f)

skill_order = [
    "Strength", "Endurance", "Mobility", "Speed",
    "Intelligence", "Concentration", "Logic", "Creativity",
    "Dexterity", "Vitality", "Recovery", "Affection",
    "Discipline", "Planning", "Reflection", "Good deeds"
]


skill_to_category = {
        "Strength": "Red", "Endurance": "Red", "Mobility": "Red", "Speed": "Red",
        "Intelligence": "Blue", "Concentration": "Blue", "Logic": "Blue", "Creativity": "Blue",
        "Dexterity": "Green", "Vitality": "Green", "Recovery": "Green", "Affection": "Green",
        "Discipline": "Gold", "Planning": "Gold", "Reflection": "Gold", "Good deeds": "Gold"
    }

# Define shared data outside the functions
descriptions = {
    "Red": "Physical skills like strength and endurance.",
    "Blue": "Mental skills like intelligence, focus, and creativity.",
    "Green": "Lifestyle and physical control like dexterity and vitality.",
    "Gold": "Meta skills like discipline and consistency."
}

earning_guide = {
    "Red": "🏋️ Gym, 🏃 Running, cardio workouts",
    "Blue": "📖 Reading, 🧠 Deep work, 🎮 Logic games",
    "Green": "🎻 Instruments, 🎯 Dexterity tasks, 🍎 Healthy living",
    "Gold": "📅 Habit streaks, ✅ Daily goals"
}

skill_descriptions = {
    "Strength": "Train your muscles and improve lifting capacity.",
    "Endurance": "Boost cardiovascular health and stamina.",
    "Mobility": "Improve flexibility, range of motion, and posture.",
    "Speed": "Increase sprint performance and reaction time.",
    "Intelligence": "Expand your knowledge and learn new topics.",
    "Concentration": "Sharpen your focus and resist distractions.",
    "Logic": "Improve problem-solving and analytical thinking.",
    "Creativity": "Enhance artistic expression and idea generation.",
    "Dexterity": "Improve hand-eye coordination and precise movement.",
    "Vitality": "Maintain high physical energy through health habits.",
    "Recovery": "Support muscle repair and prevent fatigue.",
    "Affection": "Foster emotional connection and care for others.",
    "Discipline": "Stick to habits and routines with consistency.",
    "Planning": "Organize tasks and set achievable goals.",
    "Reflection": "Gain insight through self-review and thought.",
    "Good deeds": "Act with kindness and contribute positively."
}

skill_guides = {
    "Strength": "🏋️ Weightlifting, bodyweight strength exercises",
    "Endurance": "🏃 Running, cycling, long-distance workouts",
    "Mobility": "🧘 Yoga, stretching routines, mobility drills",
    "Speed": "⏱ Sprinting drills, agility training",
    "Intelligence": "📚 Read books, take courses, learn new skills (languages, science, etc.)",
    "Concentration": "🧠 Practice deep work (30+ min), mindfulness, no-phone blocks",
    "Logic": "♟ Solve puzzles, do math problems, write code, play strategy games",
    "Creativity": "🎨 Draw, write, compose music, brainstorm, design projects",
    "Dexterity": "🎯 Play an instrument, juggle, craft, do precise movements or sports like tennis",
    "Vitality": "💧 Track hydration, sleep 7–8h, eat balanced meals, avoid junk food",
    "Recovery": "🛀 Do deep stretching, foam rolling, breathing exercises, quality sleep",
    "Affection": "💞 Send kind messages, call loved ones, spend quality time with someone",
    "Discipline": "📅 Complete daily routines, habit streaks, wake-up on time",
    "Planning": "📝 Write to-do lists, plan your week, track long-term goals",
    "Reflection": "🪞Journal your thoughts, write lessons from the day, meditate on choices",
    "Good deeds": "🤝 Help someone, donate, volunteer, pick up trash, small acts of kindness"
}


load_dotenv()  # Load environment variables from a .env file

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")  # Use a default if SECRET_KEY is not set

def get_db_connection():
    result = urlparse.urlparse(os.environ.get("DATABASE_URL"))
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port

    return psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )

def init_db():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Create tables if they don't already exist
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS progress (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    skill TEXT NOT NULL,
                    category TEXT NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1, 
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS daily (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    challenge TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    UNIQUE(user_id, challenge),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS selected_titles (
                user_id INTEGER PRIMARY KEY,
                selected_titles TEXT,
                selected_badges TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS selected_badges (
                user_id INTEGER PRIMARY KEY,
                selected_titles TEXT,
                selected_badges TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            # Initialize the last reset date if it doesn't exist
            c.execute("""
                INSERT INTO config (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO NOTHING""", 
                ("last_reset_date", "1970-01-01"))

            # Check if the reset is needed
            c.execute("SELECT value FROM config WHERE key = 'last_reset_date'")
            last_reset_date = c.fetchone()[0]
            current_date = datetime.now().strftime("%Y-%m-%d")

            if current_date != last_reset_date:
                # Reset daily challenges
                c.execute("UPDATE daily SET completed = FALSE")
                conn.commit()

                # Update the last reset date
                c.execute("UPDATE config SET value = %s WHERE key = 'last_reset_date'", (current_date,))
    
    except Exception as e:
        # Handle any exceptions (e.g., DB already initialized or connection issues)
        print(f"Error initializing the database: {e}")


if __name__ == '__main__':
    init_db()  # Initialize the database at application startup
    app.run(debug=True)

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('dashboard'))  # or card_red, etc.
        else:
            return "Login failed"

    return render_template("login.html")

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id", (username, password))
        user_id = c.fetchone()[0]

        skills = [
            ("Strength", "Red"), ("Endurance", "Red"), ("Mobility", "Red"), ("Speed", "Red"),
            ("Intelligence", "Blue"), ("Concentration", "Blue"), ("Logic", "Blue"), ("Creativity", "Blue"),
            ("Dexterity", "Green"), ("Vitality", "Green"), ("Recovery", "Green"), ("Affection", "Green"),
            ("Discipline", "Gold"), ("Planning", "Gold"), ("Reflection", "Gold"), ("Good deeds", "Gold")
        ]
        for skill, category in skills:
            c.execute("INSERT INTO progress (user_id, skill, category) VALUES (%s, %s, %s)", (user_id, skill, category))
        
        daily_challenges = ["Gym", "Running", "Reading", "Work"]
        for challenge in daily_challenges:
            c.execute("INSERT INTO daily (user_id, challenge, completed) VALUES (%s, %s, %s)", (user_id, challenge, False))

        conn.commit()
        conn.close()
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    

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
            return redirect(url_for('login'))  # or render an error page
        username = user_data[0]

        c.execute("SELECT selected_titles FROM selected_titles WHERE user_id = %s", (user_id,))
        row = c.fetchone()
        if row and row[0]:
            selected_titles = json.loads(row[0])
        else:
            selected_titles = []
        c.execute("SELECT selected_badges FROM selected_badges WHERE user_id = %s", (user_id,))
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
        username=username,
        selected_titles=selected_titles,
        selected_badges=selected_badges,
        title_info=title_info,
        badge_images=badge_images,
        skill_to_category=skill_to_category
    )


@app.route("/card_red")
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

@app.route("/card_blue")
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

@app.route("/card_green")
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

@app.route("/card_gold")
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

@app.route('/titles')
def titles():
    user_id = session.get('user_id')    
    if not user_id:
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT skill, level FROM progress WHERE user_id = %s", (user_id,))
        stats = c.fetchall()
        c.execute("SELECT selected_titles FROM selected_titles WHERE user_id = %s", (user_id,))
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


@app.route('/update_selected_titles', methods=['POST'])
def update_selected_titles():
    if request.method == 'POST':
        data = request.get_json()
        user_id = session.get('user_id')
        title = data['title']
        print(title)
        action = data['action']
        print(action)

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT selected_titles FROM selected_titles WHERE user_id = %s", (user_id,))
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
                INSERT INTO selected_titles (user_id, selected_titles)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET selected_titles = EXCLUDED.selected_titles
            """, (user_id, selected_json))
            conn.commit()

    return jsonify({"status": "success"}), 200


@app.route("/badges")
def badges():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

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


@app.route('/update_selected_badges', methods=['POST'])
def update_selected_badges():
    if request.method == 'POST':
        data = request.get_json()
        user_id = session.get('user_id')
        badge = data['title'] 
        print(badge)
        action = data['action']
        print(action)

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
            print(selected_json)

            c.execute("""
                INSERT INTO selected_badges (user_id, selected_badges) 
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET selected_badges = EXCLUDED.selected_badges
            """,(user_id, selected_json))
            conn.commit()

    return jsonify({"status": "success"}), 200



@app.route('/clear-title-animation')
def clear_title_animation():
    session.pop('show_title_animation', None)
    return '', 204



@app.route('/add_xp', methods=['POST'])
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
        new_xp = row[0] + xp_to_add
        cursor.execute("UPDATE progress SET xp = %s WHERE skill = %s AND user_id = %s", (new_xp, skill, user_id))
        conn.commit()

        # Fetch level again (in case already updated elsewhere)
        cursor.execute("SELECT level FROM progress WHERE user_id = %s AND skill = %s", (user_id, skill))
        current_level = cursor.fetchone()[0]
        old_level = current_level

        # Level-up loop
        while new_xp >= current_level * 100:
            current_level += 1
            new_xp -= (current_level - 1) * 100
            cursor.execute("UPDATE progress SET level = %s, xp = %s WHERE user_id = %s AND skill = %s",
                           (current_level, new_xp, user_id, skill))
            conn.commit()

        conn.close()
        return jsonify({ "old_level": old_level, "current_level": current_level, "skill": skill })

    else:
        conn.close()
        return jsonify(success=False, error="Skill not found"), 404

    
@app.route('/delete_xp', methods=['POST'])
def delete_xp():
    data = request.get_json()
    skill = data.get('skill')
    xp_to_delete = int(data.get('xp', 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("SELECT xp, level FROM progress WHERE user_id = %s AND skill = %s", (user_id, skill))
    row = cursor.fetchone()

    if row:
        new_xp = row[0] - xp_to_delete
        cursor.execute("UPDATE progress SET xp = %s WHERE skill = %s AND user_id = %s", (new_xp, skill, user_id))
        conn.commit()
        cursor.execute("SELECT level FROM progress WHERE skill = %s", (skill,))
        current_level = cursor.fetchone()[0]
        #Need logic to avoid level to go below 1
        while new_xp < 0: 
            if current_level == 1: 
                new_xp = 0
                cursor.execute("UPDATE progress SET xp = %s WHERE skill = %s AND user_id = %s", (new_xp, skill, user_id))
                break
            else:
                cursor.execute("UPDATE progress SET level = %s WHERE skill = %s AND user_id = %s ", (current_level - 1, skill, user_id))
                new_xp += (current_level - 1) * 100
                cursor.execute("UPDATE progress SET xp = %s WHERE skill = %s AND user_id = %s", (new_xp, skill, user_id))
                current_level -= 1
        conn.commit()
        conn.close()
        return jsonify(success=True, level_down=(new_xp < 0))
            
    else:
        conn.close()
        return jsonify(success=False, error="Skill not found"), 404

@app.route('/daily_challenges', methods=['POST'])
def daily_challenges():
    data = request.get_json()
    challenge = data.get('challenge')
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("UPDATE daily set completed = %s  WHERE challenge = %s AND user_id = %s", (True, challenge, user_id))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route("/leaderboard")
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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


@app.route("/profile/<username>")
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

    
