# === app.py ===
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

@app.route("/")
def index():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT skill, category, xp, level FROM progress")
        stats = c.fetchall()
    return render_template("index.html", stats=stats)


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
    

if __name__ == '__main__':
    init_db()  # Initialize the database at application startup
    app.run(debug=True)