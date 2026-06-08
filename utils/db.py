import os
import psycopg2
from psycopg2 import sql
import urllib.parse as urlparse

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

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    result = urlparse.urlparse(os.environ.get("DATABASE_URL"))
    # Managed providers (Heroku/RDS) don't allow creating databases; only run locally
    if not result.hostname:
        print("DATABASE_URL not set; skipping create_database_if_not_exists")
        return

    hostname = result.hostname
    if hostname not in ("localhost", "127.0.0.1"):
        print(f"Skipping create_database_if_not_exists for managed host {hostname}")
        return

    username = result.username
    password = result.password
    database = result.path[1:]
    port = result.port

    try:
        conn = psycopg2.connect(
            database="postgres",
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}" ).format(sql.Identifier(database)))
            print(f"Database '{database}' created successfully")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def init_db():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Create tables if they don't already exist
            print("Creating users table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            ''')

            print("Creating progress table...")
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

            print("Creating daily table...")
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

            print("Creating config table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
                )
            ''')

            print("Creating selected_decorations table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS selected_decorations (
                user_id INTEGER PRIMARY KEY,
                selected_titles TEXT,
                selected_badges TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            print("Creating daily_stats table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    xp_earned INTEGER DEFAULT 0,
                    challenges_completed INTEGER DEFAULT 0,
                    UNIQUE(user_id, date),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            print("Creating streaks table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS streaks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    skill TEXT NOT NULL,
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    last_completed DATE,
                    UNIQUE(user_id, skill),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            print("Creating recipes table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS recipes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_by_user_id INTEGER,
                    name TEXT NOT NULL,
                    ingredients TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    prep_time INTEGER,
                    cook_time INTEGER,
                    servings INTEGER,
                    difficulty TEXT,
                    calories INTEGER,
                    cost TEXT,
                    cuisine TEXT,
                    instructions TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')

            print("Creating cooking_access table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS cooking_access (
                    id SERIAL PRIMARY KEY,
                    owner_user_id INTEGER NOT NULL,
                    viewer_user_id INTEGER NOT NULL,
                    permission TEXT NOT NULL DEFAULT 'edit',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_user_id, viewer_user_id),
                    CHECK (permission IN ('view', 'edit')),
                    FOREIGN KEY(owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(viewer_user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            print("Creating plant_sensor_readings table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS plant_sensor_readings (
                    id SERIAL PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    moisture REAL NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            print("Creating plant_device_config table...")
            c.execute('''
                CREATE TABLE IF NOT EXISTS plant_device_config (
                    device_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    moisture_threshold REAL DEFAULT 25
                )
            ''')

            # Add missing columns to recipes table without aborting the transaction
            print("Adding missing columns to recipes table...")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS prep_time INTEGER")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS cook_time INTEGER")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS servings INTEGER")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS difficulty TEXT")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS calories INTEGER")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS cost TEXT")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS cuisine TEXT")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS instructions TEXT")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS notes TEXT")
            c.execute("ALTER TABLE IF EXISTS recipes ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER")

            # Backfill older recipes so creator displays correctly
            c.execute("UPDATE recipes SET created_by_user_id = user_id WHERE created_by_user_id IS NULL")

            # Initialize the last reset date if it doesn't exist
            print("Initializing config values...")
            c.execute("""
                INSERT INTO config (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO NOTHING""", 
                ("last_reset_date", "1970-01-01"))
            
            conn.commit()
            print("Database initialization completed successfully")

            
    except Exception as e:
        # Handle any exceptions (e.g., DB already initialized or connection issues)
        import traceback
        print(f"CRITICAL: Error initializing the database: {e}")
        print(traceback.format_exc())