import os
import psycopg2
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
                CREATE TABLE IF NOT EXISTS selected_decorations (
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
            
            conn.commit()

            
    except Exception as e:
        # Handle any exceptions (e.g., DB already initialized or connection issues)
        print(f"Error initializing the database: {e}")