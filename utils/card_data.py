import os
import json

#Path is probably fucked because changed the file location
with open(os.path.join(os.path.dirname(__file__), 'titles.json')) as f:
    TITLES = json.load(f)

#Same here
with open(os.path.join(os.path.dirname(__file__), 'badges.json')) as f:
    BADGES = json.load(f)


# Put into utils.card_data
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
    "Red": "🏋️ Gym, 🏃 Running, cardio — ~1 XP/min; 5 XP for solid sets; 10 XP for full sessions",
    "Blue": "📖 Reading, 🧠 Deep work, 🎮 Logic — ~1 XP/min; 5 XP focused blocks; 10 XP for 20–30 min",
    "Green": "🎻 Instruments, 🎯 Dexterity, 🍎 Healthy living — ~1 XP/min; 5 XP for sustained practice; 10 XP for full routines",
    "Gold": "📅 Habits, ✅ daily goals — 1–5 XP for small wins; 10 XP for full-day execution"
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
    "Strength": "🏋️ Bodyweight/weights — ~1 XP/min; 5 XP for solid sets; 10 XP for full workout blocks",
    "Endurance": "🏃 Runs/rides — ~1 XP/min; 5 XP for steady efforts; 10 XP for long intervals or sessions" ,
    "Mobility": "🧘 Mobility drills/yoga — ~1 XP/min; 5 XP for focused blocks; 10 XP for full routines",
    "Speed": "⏱ Sprints/agility — ~1 XP per minute of drills; 5 XP for a focused block; 10 XP for full sprint sessions",
    "Intelligence": "📚 Reading/courses — ~1 XP/min or page; 5 XP for 5–10 min focused; 10 XP for 20–30 min",
    "Concentration": "🧠 Deep work/mindfulness — ~1 XP/min; 5 XP for 5–10 min blocks; 10 XP for 20–30 min",
    "Logic": "♟ Puzzles/code/strategy — ~1 XP/min; 5 XP for focused blocks; 10 XP for long sessions",
    "Creativity": "🎨 Draw/write/music/design — ~1 XP/min; 5 XP for 5–10 min sprints; 10 XP for 20–30 min",
    "Dexterity": "🎯 Instruments/juggling/precision sports — ~1 XP/min; 5 XP for focused practice; 10 XP for full sessions",
    "Vitality": "💧 Sleep, hydration, healthy meals — 1–5 XP per solid habit; 10 XP for a full day on plan (avoid negative foods)",
    "Recovery": "🛀 Stretch/foam roll/breathing — ~1 XP/min; 5 XP for focused recovery; 10 XP for full session",
    "Affection": "💞 Calls, quality time — 1–5 XP for small gestures; 10 XP for long, meaningful connection",
    "Discipline": "📅 Routines, wake-up on time — 1–5 XP for small wins; 10 XP for full routine completion",
    "Planning": "📝 Plan day/week — 1–5 XP for quick planning; 10 XP for full daily/weekly plan",
    "Reflection": "🪞 Journaling/meditation — ~1 XP/min; 5 XP for 5–10 min; 10 XP for 20–30 min",
    "Good deeds": "🤝 Kind acts — 1–5 XP for small deeds; 10 XP for significant help or volunteering"
}
