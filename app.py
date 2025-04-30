# === app.py ===
from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                category TEXT NOT NULL,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')
        for category in ["Strength", "Intelligence", "Discipline"]:
            c.execute("INSERT OR IGNORE INTO stats (id, category, xp, level) VALUES (?, ?, ?, ?)",
                      (hash(category) % 100000, category, 0, 1))
        conn.commit()

@app.route("/")
def index():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT category, xp, level FROM stats")
        stats = c.fetchall()
    return render_template("index.html", stats=stats)

@app.route("/add_xp", methods=["POST"])
def add_xp():
    data = request.get_json()
    category = data["category"]
    xp_gain = int(data["xp"])

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT xp, level FROM stats WHERE category = ?", (category,))
        xp, level = c.fetchone()

        xp += xp_gain
        new_level = level
        while xp >= new_level * 100:
            xp -= new_level * 100
            new_level += 1

        c.execute("UPDATE stats SET xp = ?, level = ? WHERE category = ?", (xp, new_level, category))
        conn.commit()

    return jsonify({"xp": xp, "level": new_level})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
