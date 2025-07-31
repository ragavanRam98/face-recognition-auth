import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
from flask_oauthlib.provider import OAuth2Provider
from flask_oauthlib.contrib.oauth2 import bind_sqlalchemy
from werkzeug.security import gen_salt
from werkzeug.exceptions import HTTPException
import traceback
from datetime import datetime, timedelta

from config import config
from models import db, User, Client, Grant, Token, FaceImage
from services.face_recognition_service import FaceRecognitionService
from services.auth_service import AuthService
from services.face_service import FaceService
from services.error_handler import ErrorHandler
from utils.validators import InputValidator
from repositories.user_repository import UserRepository
from repositories.face_image_repository import FaceImageRepository
from routes.auth import auth_bp
from routes.face import face_bp
from routes.oauth import oauth_bp
from routes.api import api_bp

def create_app(config_name: str = 'default') -> Flask:
    """Create and configure Flask application
    
    Args:
        config_name: Configuration name to load
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, supports_credentials=True)
    
    # Initialize repositories
    user_repository = UserRepository()
    face_image_repository = FaceImageRepository()
    
    # Initialize services with dependency injection
    validator = InputValidator()
    face_recognition_service = FaceRecognitionService(
        faces_dir=app.config['FACES_DIR'],
        tolerance=app.config['FACE_RECOGNITION_TOLERANCE']
    )
    
    auth_service = AuthService(user_repository, validator)
    face_service = FaceService(face_recognition_service, face_image_repository)
    error_handler = ErrorHandler()
    
    # Inject services into app context
    app.auth_service = auth_service
    app.face_service = face_service
    app.face_recognition_service = face_recognition_service
    app.error_handler = error_handler
    
    # Initialize OAuth2 provider
    oauth = OAuth2Provider(app)
    bind_sqlalchemy(oauth, db.session, user=User, token=Token, client=Client, grant=Grant)
    app.oauth = oauth
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(face_bp, url_prefix='/face')
    app.register_blueprint(oauth_bp, url_prefix='/oauth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/faceid.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Face-Id startup')
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error) -> tuple:
        """Handle 400 Bad Request errors
        
        Args:
            error: The error object
            
        Returns:
            tuple: JSON response and status code
        """
        return error_handler.handle_validation_error([str(error)])
    
    @app.errorhandler(401)
    def unauthorized(error) -> tuple:
        """Handle 401 Unauthorized errors
        
        Args:
            error: The error object
            
        Returns:
            tuple: JSON response and status code
        """
        return error_handler.handle_authentication_error()
    
    @app.errorhandler(403)
    def forbidden(error) -> tuple:
        """Handle 403 Forbidden errors
        
        Args:
            error: The error object
            
        Returns:
            tuple: JSON response and status code
        """
        return error_handler.handle_authorization_error()
    
    @app.errorhandler(404)
    def not_found(error) -> tuple:
        """Handle 404 Not Found errors
        
        Args:
            error: The error object
            
        Returns:
            tuple: JSON response and status code
        """
        return error_handler.handle_not_found_error()
    
    @app.errorhandler(500)
    def internal_error(error) -> tuple:
        """Handle 500 Internal Server Error
        
        Args:
            error: The error object
            
        Returns:
            tuple: JSON response and status code
        """
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        app.logger.error(traceback.format_exc())
        return error_handler.handle_server_error('Something went wrong')
    
    @app.errorhandler(Exception)
    def handle_exception(e) -> tuple:
        """Handle unhandled exceptions
        
        Args:
            e: The exception object
            
        Returns:
            tuple: JSON response and status code
        """
        if isinstance(e, HTTPException):
            return e
        
        app.logger.error(f'Unhandled Exception: {e}')
        app.logger.error(traceback.format_exc())
        return error_handler.handle_server_error('Something went wrong')
    
    # Request handlers
    @app.before_request
    def before_request() -> None:
        """Handle pre-request tasks"""
        g.user = None
        if 'user_id' in session:
            g.user = User.query.get(session['user_id'])
    
    @app.after_request
    def after_request(response) -> 'Response':
        """Handle post-request tasks
        
        Args:
            response: The response object
            
        Returns:
            Response: Modified response with security headers
        """
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Health check endpoint
    @app.route('/health')
    def health_check() -> tuple:
        """Health check endpoint
        
        Returns:
            tuple: JSON response and status code
        """
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            
            # Test face service
            cache_stats = face_recognition_service.get_cache_stats()
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'face_service': 'operational',
                'cache_stats': cache_stats
            }), 200
        except Exception as e:
            app.logger.error(f'Health check failed: {e}')
            return error_handler.handle_server_error(str(e))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create faces directory if it doesn't exist
        os.makedirs(app.config['FACES_DIR'], exist_ok=True)
    
    return app

def create_oauth_provider(app: Flask) -> OAuth2Provider:
    """Create OAuth2 provider
    
    Args:
        app: Flask application instance
        
    Returns:
        OAuth2Provider: Configured OAuth2 provider
    """
    oauth = app.oauth
    
    @oauth.clientgetter
    def load_client(client_id: str) -> Optional[Client]:
        """Load OAuth2 client by client_id
        
        Args:
            client_id: Client identifier
            
        Returns:
            Optional[Client]: Client object or None
        """
        return Client.query.filter_by(client_id=client_id).first()
    
    @oauth.grantgetter
    def load_grant(client_id: str, code: str) -> Optional[Grant]:
        """Load OAuth2 grant by client_id and code
        
        Args:
            client_id: Client identifier
            code: Authorization code
            
        Returns:
            Optional[Grant]: Grant object or None
        """
        return Grant.query.filter_by(client_id=client_id, code=code).first()
    
    @oauth.tokengetter
    def load_token(access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> Optional[Token]:
        """Load OAuth2 token by access_token or refresh_token
        
        Args:
            access_token: Access token string
            refresh_token: Refresh token string
            
        Returns:
            Optional[Token]: Token object or None
        """
        if access_token:
            return Token.query.filter_by(access_token=access_token).first()
        if refresh_token:
            return Token.query.filter_by(refresh_token=refresh_token).first()
        return None
    
    @oauth.grantsetter
    def save_grant(client_id: str, code: dict, request, *args, **kwargs) -> Grant:
        """Save OAuth2 grant
        
        Args:
            client_id: Client identifier
            code: Authorization code dictionary
            request: OAuth2 request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Grant: Created grant object
        """
        expires = datetime.utcnow() + timedelta(seconds=100)
        grant = Grant(
            client_id=client_id,
            code=code['code'],
            redirect_uri=request.redirect_uri,
            scope=' '.join(request.scopes),
            user_id=g.user.id,
            expires=expires,
        )
        db.session.add(grant)
        db.session.commit()
        return grant
    
    @oauth.tokensetter
    def save_token(token: dict, request, *args, **kwargs) -> Token:
        """Save OAuth2 token
        
        Args:
            token: Token dictionary
            request: OAuth2 request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Token: Created token object
        """
        tok = Token(**token)
        tok.user_id = request.user.id
        tok.client_id = request.client.client_id
        db.session.add(tok)
        db.session.commit()
        return tok
    
    @oauth.usergetter
    def get_user(username: str, password: str, *args, **kwargs) -> Optional[User]:
        """Get user by username and password
        
        Args:
            username: Username
            password: Password
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Optional[User]: User object or None
        """
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
    
    return oauth

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 