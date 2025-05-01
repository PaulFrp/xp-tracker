# === app.py ===
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from dotenv import load_dotenv
import os
import json

with open(os.path.join(os.path.dirname(__file__), 'titles.json')) as f:
    TITLES = json.load(f)

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

def init_db():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                UNIQUE(user_id, challenge),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        
        # Create a table to track the last reset date
        c.execute('''
            CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
            )
        ''')

        # Initialize the last reset date if it doesn't exist
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('last_reset_date', ?)", ("1970-01-01",))

        # Check if the reset is needed
        c.execute("SELECT value FROM config WHERE key = 'last_reset_date'")
        last_reset_date = c.fetchone()[0]
        current_date = datetime.now().strftime("%Y-%m-%d")

        if current_date != last_reset_date:
            # Reset daily challenges
            c.execute("UPDATE daily SET completed = 0")
            conn.commit()

            # Update the last reset date
            c.execute("UPDATE config SET value = ? WHERE key = 'last_reset_date'", (current_date,))


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

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
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
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user_id = c.lastrowid

        skills = [
            ("Strength", "Red"), ("Endurance", "Red"), ("Mobility", "Red"), ("Speed", "Red"),
            ("Intelligence", "Blue"), ("Concentration", "Blue"), ("Logic", "Blue"), ("Creativity", "Blue"),
            ("Dexterity", "Green"), ("Vitality", "Green"), ("Recovery", "Green"), ("Affection", "Green"),
            ("Discipline", "Gold"), ("Planning", "Gold"), ("Reflection", "Gold"), ("Good deeds", "Gold")
        ]
        for skill, category in skills:
            c.execute("INSERT INTO progress (user_id, skill, category) VALUES (?, ?, ?)", (user_id, skill, category))
        
        daily_challenges = ["Gym", "Running", "Reading", "Work"]
        for challenge in daily_challenges:
            c.execute("INSERT INTO daily (user_id, challenge, completed) VALUES (?, ?, ?)", (user_id, challenge, 0))

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
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT skill, category, xp, level FROM progress WHERE user_id = ?", (user_id,))
        stats = c.fetchall()
        c.execute("SELECT challenge, completed FROM daily WHERE user_id = ?", (user_id,))
        daily_challenges = c.fetchall()
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = c.fetchone()[0]

    return render_template("dashboard.html", stats=stats, daily_challenges=daily_challenges, username=username)


@app.route("/card_red")
def card_red():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        user_id = session['user_id']
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Red' AND user_id = ?", (user_id,))
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
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        user_id = session['user_id']
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Blue' AND user_id = ?", (user_id,))
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
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        user_id = session['user_id']
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Green' AND user_id = ?", (user_id,))
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
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        user_id = session['user_id']
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Gold' AND user_id = ?", (user_id,))
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

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT skill, level FROM progress WHERE user_id = ?", (user_id,))
        stats = c.fetchall()

    # Convert skill stats into a dict: { "Strength": 35, "Intelligence": 12, ... }
    user_levels = {skill: level for skill, level in stats}

    # Determine unlocked titles
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

    return render_template("titles.html", unlocked_titles=unlocked_titles)


@app.route('/add_xp', methods=['POST'])
def add_xp():
    data = request.get_json()
    skill = data.get('skill')
    xp_to_add = int(data.get('xp', 0))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("SELECT xp, level FROM progress WHERE user_id = ? AND skill = ?", (user_id, skill))
    row = cursor.fetchone()

    if row:
        new_xp = row[0] + xp_to_add
        cursor.execute("UPDATE progress SET xp = ? WHERE skill = ? AND  user_id = ?", (new_xp, skill, user_id))
        conn.commit()
        cursor.execute("SELECT level FROM progress WHERE skill = ?", (skill,))
        current_level = cursor.fetchone()[0]
        while new_xp >= current_level * 100: 
            cursor.execute("UPDATE progress SET level = ? WHERE skill = ? AND user_id = ? ", (current_level + 1, skill, user_id))
            new_xp -= current_level * 100
            cursor.execute("UPDATE progress SET xp = ? WHERE skill = ? AND user_id = ?", (new_xp, skill, user_id))
            current_level += 1
            old_level = current_level - 1
            conn.commit()
        conn.close()
        return jsonify({ "old_level" : old_level,"current_level": current_level, "skill": skill })
    else:
        conn.close()
        return jsonify(success=False, error="Skill not found"), 404

    
@app.route('/delete_xp', methods=['POST'])
def delete_xp():
    data = request.get_json()
    skill = data.get('skill')
    xp_to_delete = int(data.get('xp', 0))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("SELECT xp, level FROM progress WHERE user_id = ? AND skill = ?", (user_id, skill))
    row = cursor.fetchone()

    if row:
        new_xp = row[0] - xp_to_delete
        cursor.execute("UPDATE progress SET xp = ? WHERE skill = ? AND user_id = ?", (new_xp, skill, user_id))
        conn.commit()
        cursor.execute("SELECT level FROM progress WHERE skill = ?", (skill,))
        current_level = cursor.fetchone()[0]
        #Need logic to avoid level to go below 1
        while new_xp < 0: 
            if current_level == 1: 
                new_xp = 0
                cursor.execute("UPDATE progress SET xp = ? WHERE skill = ? AND user_id = ?", (new_xp, skill, user_id))
                break
            else:
                cursor.execute("UPDATE progress SET level = ? WHERE skill = ? AND user_id = ? ", (current_level - 1, skill, user_id))
                new_xp += (current_level - 1) * 100
                cursor.execute("UPDATE progress SET xp = ? WHERE skill = ? AND user_id = ?", (new_xp, skill, user_id))
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
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("UPDATE daily set completed = ?  WHERE challenge = ? AND user_id = ?", (1, challenge, user_id))
    conn.commit()
    conn.close()
    return jsonify(success=True)
    

if __name__ == '__main__':
    init_db()  # Initialize the database at application startup
    app.run(debug=True)