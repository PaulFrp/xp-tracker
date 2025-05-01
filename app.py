# === app.py ===
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import sqlite3
# Removed unused import

app = Flask(__name__)

def init_db():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')

        skills = [
            ("Strength", "Red"), ("Endurance", "Red"), ("Mobility", "Red"), ("Speed", "Red"),
            ("Intelligence", "Blue"), ("Concentration", "Blue"), ("Logic", "Blue"), ("Creativity", "Blue"),
            ("Dexterity", "Green"), ("Vitality", "Green"), ("Recovery", "Green"), ("Affection", "Green"),
            ("Discipline", "Gold"), ("Planning", "Gold"), ("Reflection", "Gold"), ("Good deeds", "Gold")
        ]

        for skill, category in skills:
            c.execute("INSERT OR IGNORE INTO progress (skill, category, xp, level) VALUES (?, ?, ?, ?)",
                      (skill, category, 0, 1))
        conn.commit()

        c.execute('''
            CREATE TABLE IF NOT EXISTS daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge TEXT NOT NULL UNIQUE,
            completed BOOLEAN DEFAULT 0
            )
        ''')

        # Insert daily challenges if they don't already exist
        challenges = ["Gym", "Running", "Reading", "Work"]
        for challenge in challenges:
            c.execute("INSERT OR IGNORE INTO daily (challenge, completed) VALUES (?, ?)", (challenge, 0))
        
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
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT skill, category, xp, level FROM progress")
        stats = c.fetchall()
        c.execute("SELECT challenge, completed FROM daily")
        daily_challenges = c.fetchall()
    return render_template("index.html", stats=stats , daily_challenges=daily_challenges)

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

@app.route("/card_red")
def card_red():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Red'")
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
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Blue'")
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
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Green'")
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
        c.execute("SELECT skill, category, xp, level FROM progress WHERE category = 'Gold'")
        stats = c.fetchall()

    return render_template(
        "card_gold.html", 
        stats=stats, 
        descriptions=descriptions, 
        earning_guide=earning_guide,
        skill_descriptions=skill_descriptions,
        skill_guides=skill_guides
        )

@app.route('/add_xp', methods=['POST'])
def add_xp():
    data = request.get_json()
    skill = data.get('skill')
    xp_to_add = int(data.get('xp', 0))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT xp FROM progress WHERE skill = ?", (skill,))
    row = cursor.fetchone()

    if row:
        new_xp = row[0] + xp_to_add
        cursor.execute("UPDATE progress SET xp = ? WHERE skill = ?", (new_xp, skill))
        conn.commit()
        cursor.execute("SELECT level FROM progress WHERE skill = ?", (skill,))
        current_level = cursor.fetchone()[0]
        while new_xp >= current_level * 100: 
            cursor.execute("UPDATE progress SET level = ? WHERE skill = ?", (current_level + 1, skill))
            new_xp -= current_level * 100
            cursor.execute("UPDATE progress SET xp = ? WHERE skill = ?", (new_xp, skill))
            current_level += 1
            conn.commit()
        conn.close()
        return jsonify(success=True)
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
    cursor.execute("SELECT xp FROM progress WHERE skill = ?", (skill,))
    row = cursor.fetchone()

    if row:
        new_xp = row[0] - xp_to_delete
        cursor.execute("UPDATE progress SET xp = ? WHERE skill = ?", (new_xp, skill))
        conn.commit()
        cursor.execute("SELECT level FROM progress WHERE skill = ?", (skill,))
        current_level = cursor.fetchone()[0]
        #Need logic to avoid level to go below 1
        while new_xp < 0: 
            if current_level == 1: 
                new_xp = 0
                cursor.execute("UPDATE progress SET xp = ? WHERE skill = ?", (new_xp, skill))
                break
            else:
                cursor.execute("UPDATE progress SET level = ? WHERE skill = ?", (current_level - 1, skill))
                new_xp += (current_level - 1) * 100
                cursor.execute("UPDATE progress SET xp = ? WHERE skill = ?", (new_xp, skill))
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
    cursor.execute("UPDATE daily set completed = ?  WHERE challenge = ?", (1, challenge))
    conn.commit()
    conn.close()
    return jsonify(success=True)
    

if __name__ == '__main__':
    init_db()  # Initialize the database at application startup
    app.run(debug=True)