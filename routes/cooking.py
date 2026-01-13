from flask import render_template, session, redirect, url_for, request, jsonify, Blueprint
from utils.db import get_db_connection
import json

cooking_bp = Blueprint("cooking", __name__)

PREDEFINED_TAGS = [
    "Vegan", "Vegetarian", "Gluten-free", "Dairy-free", "Keto", 
    "Low-carb", "High-protein", "Chicken", "Beef", "Pork", "Fish", 
    "Seafood", "Pasta", "Rice", "Soup", "Salad", "Dessert", "Breakfast", 
    "Lunch", "Dinner", "Snack", "Quick", "Slow-cooked", "Baked", "Grilled"
]

@cooking_bp.route("/cooking")
def cooking():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login.login'))
    
    search_query = request.args.get('search', '').lower()
    filter_tags = request.args.getlist('tag')  # Get all tag filters
    filter_difficulty = request.args.get('difficulty', '')
    filter_time = request.args.get('time', '')
    
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, ingredients, tags, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes FROM recipes WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        recipes = c.fetchall()
    
    # Process recipes
    processed_recipes = []
    all_tags = set()
    
    for recipe_data in recipes:
        recipe_id, name, ingredients_json, tags_json, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes = recipe_data
        ingredients = json.loads(ingredients_json) if ingredients_json else []
        tags = json.loads(tags_json) if tags_json else []
        all_tags.update(tags)
        
        # Apply search filter
        if search_query:
            ingredient_names = [ing['name'].lower() if isinstance(ing, dict) else ing.lower() for ing in ingredients]
            if search_query not in name.lower() and not any(search_query in ing_name for ing_name in ingredient_names):
                continue
        
        # Apply tag filters (recipe must have ALL selected tags)
        if filter_tags and not all(tag in tags for tag in filter_tags):
            continue
        
        # Apply difficulty filter
        if filter_difficulty and difficulty != filter_difficulty:
            continue
        
        # Apply time filter
        total_time = (prep_time or 0) + (cook_time or 0)
        if filter_time:
            if filter_time == 'quick' and total_time > 30:
                continue
            elif filter_time == 'medium' and (total_time <= 30 or total_time > 60):
                continue
            elif filter_time == 'long' and total_time <= 60:
                continue
        
        processed_recipes.append({
            'id': recipe_id,
            'name': name,
            'ingredients': ingredients,
            'tags': tags,
            'prep_time': prep_time,
            'cook_time': cook_time,
            'total_time': total_time if total_time > 0 else None,
            'servings': servings,
            'difficulty': difficulty,
            'calories': calories,
            'cost': cost,
            'cuisine': cuisine,
            'instructions': instructions,
            'notes': notes
        })
    
    all_tags = sorted(list(all_tags))
    
    return render_template("cooking.html", recipes=processed_recipes, all_tags=all_tags, current_tag=filter_tags, search_query=search_query, selected_difficulty=filter_difficulty, selected_time=filter_time, predefined_tags=PREDEFINED_TAGS)

@cooking_bp.route('/add_recipe', methods=['POST'])
def add_recipe():
    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
        data = request.get_json()
        name = (data.get('name') or '').strip()
        ingredients = data.get('ingredients', [])
        tags = data.get('tags', [])
        prep_time = data.get('prep_time')
        cook_time = data.get('cook_time')
        servings = data.get('servings')
        difficulty = data.get('difficulty') or None
        calories = data.get('calories')
        cost = data.get('cost') or None
        cuisine = (data.get('cuisine') or '').strip() or None
        instructions = (data.get('instructions') or '').strip() or None
        notes = (data.get('notes') or '').strip() or None
        
        if not name:
            return jsonify({"status": "error", "message": "Recipe name is required"}), 400
        
        # Convert to int if provided and not empty
        try:
            prep_time = int(prep_time) if prep_time and str(prep_time).strip() else None
            cook_time = int(cook_time) if cook_time and str(cook_time).strip() else None
            servings = int(servings) if servings and str(servings).strip() else None
            calories = int(calories) if calories and str(calories).strip() else None
        except (ValueError, TypeError):
            prep_time = cook_time = servings = calories = None
        
        ingredients_json = json.dumps(ingredients)
        tags_json = json.dumps(tags)
        
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO recipes (user_id, name, ingredients, tags, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, name, ingredients_json, tags_json, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes)
            )
            recipe_id = c.fetchone()[0]
            conn.commit()
        
        return jsonify({
            "status": "success",
            "recipe_id": recipe_id,
            "name": name
        }), 201

@cooking_bp.route('/delete_recipe/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    with get_db_connection() as conn:
        c = conn.cursor()
        # Verify the recipe belongs to the user
        c.execute("SELECT user_id FROM recipes WHERE id = %s", (recipe_id,))
        result = c.fetchone()
        
        if not result or result[0] != user_id:
            return jsonify({"status": "error", "message": "Recipe not found"}), 404
        
        c.execute("DELETE FROM recipes WHERE id = %s", (recipe_id,))
        conn.commit()
    
    return jsonify({"status": "success"}), 200

@cooking_bp.route('/edit_recipe/<int:recipe_id>', methods=['PUT'])
def edit_recipe(recipe_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.get_json()
    name = (data.get('name') or '').strip()
    ingredients = data.get('ingredients', [])
    tags = data.get('tags', [])
    prep_time = data.get('prep_time')
    cook_time = data.get('cook_time')
    servings = data.get('servings')
    difficulty = data.get('difficulty') or None
    calories = data.get('calories')
    cost = data.get('cost') or None
    cuisine = (data.get('cuisine') or '').strip() or None
    instructions = (data.get('instructions') or '').strip() or None
    notes = (data.get('notes') or '').strip() or None
    
    if not name:
        return jsonify({"status": "error", "message": "Recipe name is required"}), 400
    
    # Convert to int if provided and not empty
    try:
        prep_time = int(prep_time) if prep_time and str(prep_time).strip() else None
        cook_time = int(cook_time) if cook_time and str(cook_time).strip() else None
        servings = int(servings) if servings and str(servings).strip() else None
        calories = int(calories) if calories and str(calories).strip() else None
    except (ValueError, TypeError):
        prep_time = cook_time = servings = calories = None
    
    ingredients_json = json.dumps(ingredients)
    tags_json = json.dumps(tags)
    
    with get_db_connection() as conn:
        c = conn.cursor()
        # Verify the recipe belongs to the user
        c.execute("SELECT user_id FROM recipes WHERE id = %s", (recipe_id,))
        result = c.fetchone()
        
        if not result or result[0] != user_id:
            return jsonify({"status": "error", "message": "Recipe not found"}), 404
        
        c.execute(
            "UPDATE recipes SET name = %s, ingredients = %s, tags = %s, prep_time = %s, cook_time = %s, servings = %s, difficulty = %s, calories = %s, cost = %s, cuisine = %s, instructions = %s, notes = %s WHERE id = %s",
            (name, ingredients_json, tags_json, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes, recipe_id)
        )
        conn.commit()
    
    return jsonify({"status": "success"}), 200

@cooking_bp.route('/get_recipe/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, name, ingredients, tags, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes FROM recipes WHERE id = %s AND user_id = %s",
            (recipe_id, user_id)
        )
        recipe_data = c.fetchone()
    
    if not recipe_data:
        return jsonify({"status": "error", "message": "Recipe not found"}), 404
    
    recipe_id, name, ingredients_json, tags_json, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes = recipe_data
    ingredients = json.loads(ingredients_json) if ingredients_json else []
    tags = json.loads(tags_json) if tags_json else []
    total_time = (prep_time or 0) + (cook_time or 0)
    
    return jsonify({
        "id": recipe_id,
        "name": name,
        "ingredients": ingredients,
        "tags": tags,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "total_time": total_time if total_time > 0 else None,
        "servings": servings,
        "difficulty": difficulty,
        "calories": calories,
        "cost": cost,
        "cuisine": cuisine,
        "instructions": instructions,
        "notes": notes
    }), 200
