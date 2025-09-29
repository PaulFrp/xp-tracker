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
    "Strength": "🏋️ Weightlifting, bodyweight strength exercises (i.e. 1 push up = 1 XP)",
    "Endurance": "🏃 Running, cycling, long-distance workouts (i.e. 100m running = 1 XP)" ,
    "Mobility": "🧘 Yoga, mobility drills (i.e. 1min of mobility training= 1 XP)",
    "Speed": "⏱ Sprinting drills, agility training (i.e. 100m sprint = 10 XP)",
    "Intelligence": "📚 Read books, take courses, learn new skills (i.e. 1 page read = 1 XP)",
    "Concentration": "🧠 Practice deep work (30+ min), mindfulness, no-phone blocks (i.e. 1 min of deep work = 1 XP)",
    "Logic": "♟ Solve puzzles, do math problems, write code, play strategy games (i.e. 1 min of coding = 1 XP)",
    "Creativity": "🎨 Draw, write, compose music, brainstorm, design projects (i.e. 1 min of drawing = 1 XP)",
    "Dexterity": "🎯 Play an instrument, juggle, craft, do precise movements or sports like tennis (i.e. 1 min of tennis = 1 XP)",
    "Vitality": "💧 Track hydration, sleep 7–8h, eat balanced meals, avoid junk food (i.e. 1 healthy meal = 10 XP, -10XP if junk food or alcohol)",
    "Recovery": "🛀 Do deep stretching, foam rolling, breathing exercises, quality sleep (i.e. Stretching session after excercise = 10 XP)",
    "Affection": "💞 Send kind messages, call loved ones, spend quality time with someone (i.e. 1 call with a loved one = 10 XP or 1 hug = 1XP)",
    "Discipline": "📅 Complete daily routines, habit streaks, wake-up on time (i.e. Completing daily challenges = 10 XP)",
    "Planning": "📝 Write to-do lists, plan your week, track long-term goals (i.e. Having a plan for the day = 10 XP)",
    "Reflection": "🪞Journal your thoughts, write lessons from the day, meditate on choices (i.e. 1min reflecting = 1 XP)",
    "Good deeds": "🤝 Help someone, donate, volunteer, pick up trash, small acts of kindness (i.e. 1 act of kindness = 10 XP)"
}
