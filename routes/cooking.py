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


def _get_user_by_username(cursor, username):
    cursor.execute("SELECT id, username FROM users WHERE LOWER(username) = LOWER(%s)", (username,))
    return cursor.fetchone()


def _get_user_by_id(cursor, user_id):
    cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()


def _get_access_level(cursor, actor_user_id, owner_user_id):
    if actor_user_id == owner_user_id:
        return "owner"

    cursor.execute(
        "SELECT permission FROM cooking_access WHERE owner_user_id = %s AND viewer_user_id = %s",
        (owner_user_id, actor_user_id)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _can_view(access_level):
    return access_level in ("owner", "edit", "view")


def _can_edit(access_level):
    return access_level in ("owner", "edit")


def _get_accessible_drives(cursor, user_id):
    cursor.execute(
        """
        SELECT u.id, u.username
        FROM users u
        WHERE u.id = %s

        UNION

        SELECT u.id, u.username
        FROM cooking_access ca
        JOIN users u ON u.id = ca.owner_user_id
        WHERE ca.viewer_user_id = %s

        ORDER BY username ASC
        """,
        (user_id, user_id)
    )
    drives = cursor.fetchall()
    return [{"id": row[0], "username": row[1]} for row in drives]

@cooking_bp.route("/cooking")
def cooking():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login.login'))

        owner_username_query = (request.args.get('owner') or '').strip()
        
        search_query = request.args.get('search', '').lower()
        filter_tags = request.args.getlist('tag')  # Get all tag filters
        filter_difficulty = request.args.get('difficulty', '')
        filter_time = request.args.get('time', '')
        filter_cost = request.args.get('cost', '')
        
        with get_db_connection() as conn:
            c = conn.cursor()

            if owner_username_query:
                owner_row = _get_user_by_username(c, owner_username_query)
            else:
                owner_row = _get_user_by_id(c, user_id)

            if not owner_row:
                return render_template("error.html", message="Shared cooking drive not found"), 404

            owner_id, owner_username = owner_row
            access_level = _get_access_level(c, user_id, owner_id)
            if not _can_view(access_level):
                return render_template("error.html", message="You do not have access to this cooking drive"), 403

            can_edit = _can_edit(access_level)
            is_owner = access_level == "owner"
            accessible_drives = _get_accessible_drives(c, user_id)

            c.execute(
                """
                SELECT
                    r.id,
                    r.name,
                    r.ingredients,
                    r.tags,
                    r.prep_time,
                    r.cook_time,
                    r.servings,
                    r.difficulty,
                    r.calories,
                    r.cost,
                    r.cuisine,
                    r.instructions,
                    r.notes,
                    COALESCE(creator.username, owner.username) AS created_by_username
                FROM recipes r
                JOIN users owner ON owner.id = r.user_id
                LEFT JOIN users creator ON creator.id = r.created_by_user_id
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
                """,
                (owner_id,)
            )
            recipes = c.fetchall()
        
        # Process recipes
        processed_recipes = []
        all_tags = set()
        
        for recipe_data in recipes:
            recipe_id, name, ingredients_json, tags_json, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes, created_by_username = recipe_data
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

            # Apply cost/price filter
            if filter_cost and cost != filter_cost:
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
                'notes': notes,
                'created_by_username': created_by_username
            })
        
        all_tags = sorted(list(all_tags))
        
        return render_template(
            "cooking.html",
            recipes=processed_recipes,
            all_tags=all_tags,
            current_tag=filter_tags,
            search_query=search_query,
            selected_difficulty=filter_difficulty,
            selected_time=filter_time,
            selected_cost=filter_cost,
            predefined_tags=PREDEFINED_TAGS,
            owner_user_id=owner_id,
            owner_username=owner_username,
            is_owner=is_owner,
            can_edit=can_edit,
            accessible_drives=accessible_drives
        )
    
    except Exception as e:
        import traceback
        print(f"Error in cooking route: {str(e)}")
        print(traceback.format_exc())
        return render_template("error.html", message=f"Error loading cooking page: {str(e)}"), 500

@cooking_bp.route('/add_recipe', methods=['POST'])
def add_recipe():
    try:
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
            owner_user_id = data.get('owner_user_id')

            try:
                owner_user_id = int(owner_user_id) if owner_user_id else user_id
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Invalid owner drive"}), 400
            
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

                owner_row = _get_user_by_id(c, owner_user_id)
                if not owner_row:
                    return jsonify({"status": "error", "message": "Cooking drive not found"}), 404

                access_level = _get_access_level(c, user_id, owner_user_id)
                if not _can_edit(access_level):
                    return jsonify({"status": "error", "message": "You do not have edit access to this drive"}), 403

                c.execute(
                    "INSERT INTO recipes (user_id, created_by_user_id, name, ingredients, tags, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                    (owner_user_id, user_id, name, ingredients_json, tags_json, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes)
                )
                recipe_id = c.fetchone()[0]
                conn.commit()
            
            return jsonify({
                "status": "success",
                "recipe_id": recipe_id,
                "name": name
            }), 201
    except Exception as e:
        import traceback
        print(f"Error in add_recipe: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Error adding recipe: {str(e)}"}), 500

@cooking_bp.route('/delete_recipe/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    with get_db_connection() as conn:
        c = conn.cursor()

        c.execute("SELECT user_id FROM recipes WHERE id = %s", (recipe_id,))
        result = c.fetchone()
        
        if not result:
            return jsonify({"status": "error", "message": "Recipe not found"}), 404

        recipe_owner_user_id = result[0]
        access_level = _get_access_level(c, user_id, recipe_owner_user_id)

        if not _can_edit(access_level):
            return jsonify({"status": "error", "message": "You do not have edit access to delete this recipe"}), 403
        
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

        c.execute("SELECT user_id FROM recipes WHERE id = %s", (recipe_id,))
        result = c.fetchone()
        
        if not result:
            return jsonify({"status": "error", "message": "Recipe not found"}), 404

        recipe_owner_user_id = result[0]
        access_level = _get_access_level(c, user_id, recipe_owner_user_id)
        if not _can_edit(access_level):
            return jsonify({"status": "error", "message": "You do not have edit access to this recipe"}), 403
        
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
            """
            SELECT
                r.id,
                r.user_id,
                r.name,
                r.ingredients,
                r.tags,
                r.prep_time,
                r.cook_time,
                r.servings,
                r.difficulty,
                r.calories,
                r.cost,
                r.cuisine,
                r.instructions,
                r.notes,
                COALESCE(creator.username, owner.username) AS created_by_username
            FROM recipes r
            JOIN users owner ON owner.id = r.user_id
            LEFT JOIN users creator ON creator.id = r.created_by_user_id
            WHERE r.id = %s
            """,
            (recipe_id,)
        )
        recipe_data = c.fetchone()
    
    if not recipe_data:
        return jsonify({"status": "error", "message": "Recipe not found"}), 404
    
    recipe_id, owner_user_id, name, ingredients_json, tags_json, prep_time, cook_time, servings, difficulty, calories, cost, cuisine, instructions, notes, created_by_username = recipe_data

    with get_db_connection() as conn:
        c = conn.cursor()
        access_level = _get_access_level(c, user_id, owner_user_id)

    if not _can_view(access_level):
        return jsonify({"status": "error", "message": "Recipe not found"}), 404

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
        "notes": notes,
        "created_by_username": created_by_username,
        "can_edit": _can_edit(access_level),
        "can_delete": _can_edit(access_level)
    }), 200


@cooking_bp.route('/cooking/share', methods=['POST'])
def share_cooking_drive():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    permission = (data.get('permission') or 'edit').strip().lower()

    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400

    if permission not in ('view', 'edit'):
        return jsonify({"status": "error", "message": "Invalid permission"}), 400

    with get_db_connection() as conn:
        c = conn.cursor()
        target_user = _get_user_by_username(c, username)
        if not target_user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        target_user_id, target_username = target_user
        if target_user_id == user_id:
            return jsonify({"status": "error", "message": "You already own this drive"}), 400

        c.execute(
            """
            INSERT INTO cooking_access (owner_user_id, viewer_user_id, permission)
            VALUES (%s, %s, %s)
            ON CONFLICT (owner_user_id, viewer_user_id)
            DO UPDATE SET permission = EXCLUDED.permission, updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, target_user_id, permission)
        )
        conn.commit()

    return jsonify({
        "status": "success",
        "shared_with": target_username,
        "permission": permission
    }), 200


@cooking_bp.route('/cooking/shares', methods=['GET'])
def list_cooking_shares():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT u.id, u.username, ca.permission, ca.created_at, ca.updated_at
            FROM cooking_access ca
            JOIN users u ON u.id = ca.viewer_user_id
            WHERE ca.owner_user_id = %s
            ORDER BY u.username ASC
            """,
            (user_id,)
        )
        rows = c.fetchall()

    shares = [
        {
            "viewer_user_id": row[0],
            "username": row[1],
            "permission": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
            "updated_at": row[4].isoformat() if row[4] else None
        }
        for row in rows
    ]
    return jsonify({"status": "success", "shares": shares}), 200


@cooking_bp.route('/cooking/share/<int:viewer_user_id>', methods=['DELETE'])
def revoke_cooking_share(viewer_user_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM cooking_access WHERE owner_user_id = %s AND viewer_user_id = %s",
            (user_id, viewer_user_id)
        )
        deleted = c.rowcount
        conn.commit()

    if deleted == 0:
        return jsonify({"status": "error", "message": "Share not found"}), 404

    return jsonify({"status": "success"}), 200
