from app.routes.listings import bp as listings_bp
from app.routes.reviews import bp as reviews_bp
from app.routes.suggestions import bp as suggestions_bp
from app.routes.policies import bp as policies_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.batch import bp as batch_bp
from app.routes.history import bp as history_bp
from app.routes.health import bp as health_bp

def register_blueprints(app):
    app.register_blueprint(listings_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(suggestions_bp)
    app.register_blueprint(policies_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(health_bp)
