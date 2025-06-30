from flask import Flask
from flask_cors import CORS
from expense_analyzer_backend.config import Config
from expense_analyzer_backend.services.database import init_db
import logging
from datetime import datetime


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize database
    init_db(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_blueprints(app):
    """Register application blueprints"""
    from expense_analyzer_backend.routes.expenses import expenses_bp
    from expense_analyzer_backend.routes.analysis import analysis_bp
    
    api_prefix = app.config['API_PREFIX']
    app.register_blueprint(expenses_bp, url_prefix=f'{api_prefix}/expenses')
    app.register_blueprint(analysis_bp, url_prefix=f'{api_prefix}/analysis')


def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'message': str(error)}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden', 'message': 'Insufficient permissions'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error', 'message': 'Something went wrong'}, 500


def setup_logging(app):
    """Setup application logging"""
    if not app.debug:
        logging.basicConfig(
            level=getattr(logging, app.config['LOG_LEVEL']),
            format='%(asctime)s %(levelname)s: %(message)s'
        )