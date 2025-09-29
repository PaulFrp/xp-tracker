

from datetime import datetime
from flask import Flask
import psycopg2
import urllib.parse as urlparse
from dotenv import load_dotenv
import os
import json
from utils.db import get_db_connection, init_db

load_dotenv()  # Load environment variables from a .env file


def create_app():
    
    app = Flask(__name__)

    #Import blue prints
    from routes.dashboard import dashboard_bp
    from routes.login import login_bp
    from routes.cards import cards_bp
    from routes.titles import titles_bp
    from routes.badges import badges_bp
    from routes.xp import xp_bp
    from routes.leaderboard import leaderboard_bp
    from routes.challenges import challenges_bp
    from routes.profile import profile_bp

    #Register blue prints
    app.register_blueprint(login_bp, url_prefix='')
    app.register_blueprint(dashboard_bp, url_prefix='')
    app.register_blueprint(cards_bp, url_prefix='')
    app.register_blueprint(titles_bp, url_prefix='')
    app.register_blueprint(badges_bp, url_prefix='')
    app.register_blueprint(xp_bp, url_prefix='')
    app.register_blueprint(leaderboard_bp, url_prefix='')
    app.register_blueprint(challenges_bp, url_prefix='')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    app.secret_key = os.getenv("SECRET_KEY", "default_secret_key") 

    init_db()

    return app
    

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)