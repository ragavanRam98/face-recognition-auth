from flask import jsonify
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Error handling service"""
    
    @staticmethod
    def handle_validation_error(errors: List[str]) -> tuple:
        """Handle validation errors
        
        Args:
            errors: List of validation error messages
            
        Returns:
            tuple: JSON response and status code
        """
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    @staticmethod
    def handle_authentication_error(message: str = 'Authentication required') -> tuple:
        """Handle authentication errors
        
        Args:
            message: Error message
            
        Returns:
            tuple: JSON response and status code
        """
        return jsonify({'error': 'Unauthorized', 'message': message}), 401
    
    @staticmethod
    def handle_authorization_error(message: str = 'Access denied') -> tuple:
        """Handle authorization errors
        
        Args:
            message: Error message
            
        Returns:
            tuple: JSON response and status code
        """
        return jsonify({'error': 'Forbidden', 'message': message}), 403
    
    @staticmethod
    def handle_not_found_error(message: str = 'Resource not found') -> tuple:
        """Handle not found errors
        
        Args:
            message: Error message
            
        Returns:
            tuple: JSON response and status code
        """
        return jsonify({'error': 'Not found', 'message': message}), 404
    
    @staticmethod
    def handle_server_error(message: str = 'Something went wrong') -> tuple:
        """Handle server errors
        
        Args:
            message: Error message
            
        Returns:
            tuple: JSON response and status code
        """
        logger.error(f'Server Error: {message}')
        return jsonify({'error': 'Internal server error', 'message': message}), 500
    
    @staticmethod
    def handle_conflict_error(message: str = 'Resource conflict') -> tuple:
        """Handle conflict errors
        
        Args:
            message: Error message
            
        Returns:
            tuple: JSON response and status code
        """
        return jsonify({'error': 'Conflict', 'message': message}), 409 