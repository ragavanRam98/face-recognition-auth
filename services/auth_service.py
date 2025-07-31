from typing import Optional, Dict, Any
from models import User
from interfaces.repositories import IUserRepository
from interfaces.validators import IInputValidator
from services.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service"""
    
    def __init__(self, user_repository: IUserRepository, validator: IInputValidator):
        """Initialize authentication service
        
        Args:
            user_repository: User repository interface
            validator: Input validator interface
        """
        self.user_repository = user_repository
        self.validator = validator
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user
        
        Args:
            username: Username
            email: Email address
            password: Password
            
        Returns:
            Dict[str, Any]: Registration result with success status and user data or error
        """
        try:
            # Validate input
            if not self.validator.validate_username(username):
                return {'success': False, 'error': 'Invalid username format'}
            
            if not self.validator.validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            password_validation = self.validator.validate_password(password)
            if not password_validation['valid']:
                return {'success': False, 'error': 'Password validation failed', 'details': password_validation['errors']}
            
            # Check if user already exists
            if self.user_repository.find_by_username(username):
                return {'success': False, 'error': 'Username already exists'}
            
            if self.user_repository.find_by_email(email):
                return {'success': False, 'error': 'Email already exists'}
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            created_user = self.user_repository.create(user)
            
            logger.info(f'New user registered: {username}')
            
            return {
                'success': True,
                'user': created_user.to_dict()
            }
            
        except Exception as e:
            logger.error(f'Registration error: {e}')
            return {'success': False, 'error': 'Registration failed'}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Dict[str, Any]: Authentication result with success status and user data or error
        """
        try:
            # Find user
            user = self.user_repository.find_by_username(username)
            if not user:
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Check password
            if not user.check_password(password):
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Check if user is active
            if not user.is_active:
                return {'success': False, 'error': 'Account is disabled'}
            
            logger.info(f'User authenticated: {username}')
            
            return {
                'success': True,
                'user': user.to_dict()
            }
            
        except Exception as e:
            logger.error(f'Authentication error: {e}')
            return {'success': False, 'error': 'Authentication failed'}
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User object or None
        """
        return self.user_repository.find_by_id(user_id) 