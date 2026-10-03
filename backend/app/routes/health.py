import os
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from app.database import db

bp = Blueprint('health', __name__, url_prefix='/api')

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint testing DB connection and environment configuration."""
    db_status = "unhealthy"
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    gemini_key = current_app.config.get("GEMINI_API_KEY", "")
    gemini_configured = bool(gemini_key and gemini_key != "your_gemini_api_key_here")

    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'database_uri_type': 'mysql' if 'mysql' in current_app.config['SQLALCHEMY_DATABASE_URI'] else 'sqlite',
        'gemini_configured': gemini_configured,
        'gemini_model': current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash"),
        'service': 'Marketplace Listing Quality Reviewer API'
    }), 200
