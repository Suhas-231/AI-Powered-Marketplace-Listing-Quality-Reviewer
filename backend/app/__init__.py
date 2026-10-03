import logging
import os
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.database import db, verify_and_configure_database, init_db
from app.routes import register_blueprints

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s]: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Pre-verify database connection and switch to SQLite if MySQL unavailable
    if not app.config.get("TESTING"):
        verify_and_configure_database(app)

    # Initialize SQLAlchemy extension
    db.init_app(app)

    # Initialize tables and seed data
    if not app.config.get("TESTING"):
        init_db(app)

    # Register blueprints
    register_blueprints(app)

    # Centralized error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': str(error.description if hasattr(error, 'description') else error)
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found.'
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected server error occurred.'
        }), 500

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        logger.exception(f"Unhandled exception: {e}")
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': str(e)
        }), 500

    return app
