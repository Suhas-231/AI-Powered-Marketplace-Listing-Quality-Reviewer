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

    ai_provider = current_app.config.get("AI_PROVIDER", "groq")
    groq_key = current_app.config.get("GROQ_API_KEY", "")
    groq_configured = bool(groq_key and groq_key not in ["your_groq_api_key_here", "YOUR_GROQ_API_KEY"])

    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'database_uri_type': 'mysql' if 'mysql' in current_app.config['SQLALCHEMY_DATABASE_URI'] else 'sqlite',
        'ai_provider': ai_provider,
        'groq_configured': groq_configured,
        'groq_model': current_app.config.get("GROQ_MODEL", "openai/gpt-oss-20b"),
        'service': 'Marketplace Listing Quality Reviewer API'
    }), 200
