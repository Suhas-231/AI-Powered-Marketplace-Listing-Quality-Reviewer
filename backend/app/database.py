import logging
import os
import pymysql
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

logger = logging.getLogger(__name__)

db = SQLAlchemy()

def verify_and_configure_database(app):
    """
    Checks if the configured database URI is reachable.
    If MySQL connection fails, seamlessly switches to local SQLite fallback before db.init_app.
    """
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if "mysql" in db_uri.lower():
        # Test connection directly using pymysql
        try:
            user = app.config.get('MYSQL_USER', 'root')
            password = app.config.get('MYSQL_PASSWORD', '')
            host = app.config.get('MYSQL_HOST', 'localhost')
            port = int(app.config.get('MYSQL_PORT', 3306))
            dbname = app.config.get('MYSQL_DB', 'marketplace_reviewer')
            
            logger.info(f"Testing MySQL connection to {host}:{port} user={user}...")
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connect_timeout=2
            )
            # Create database if it does not exist
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4;")
            conn.close()
            logger.info(f"MySQL connection verified. Database '{dbname}' ready.")
        except Exception as e:
            logger.warning(f"MySQL connection failed ({e}). Switching to local SQLite database.")
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'marketplace_reviewer.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
            app.config.pop('SQLALCHEMY_ENGINE_OPTIONS', None)

def init_db(app):
    """
    Creates tables and seeds initial data within the application context.
    """
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables initialized successfully.")
            from app.utils.seed_data import seed_initial_data
            seed_initial_data()
        except Exception as e:
            logger.error(f"Error creating tables or seeding: {e}")
            raise e
