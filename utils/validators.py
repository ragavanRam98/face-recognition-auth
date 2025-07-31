import re
import validators
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

from interfaces.validators import IInputValidator

class InputValidator(IInputValidator):
    """Input validation utilities implementation"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
        
        # Use validators library for additional checks
        return validators.email(email)
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        if not username or not isinstance(username, str):
            return False
        
        # Username should be 3-30 characters, alphanumeric and underscores only
        username_pattern = r'^[a-zA-Z0-9_]{3,30}$'
        return bool(re.match(username_pattern, username))
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            return {'valid': False, 'errors': ['Password is required']}
        
        errors = []
        
        # Check minimum length
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        
        # Check for digit
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one digit')
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_base64_image(image_data: str) -> bool:
        """Validate base64 image data"""
        if not image_data or not isinstance(image_data, str):
            return False
        
        # Check if it's a valid base64 string
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',')[1]
            
            # Check if it's valid base64
            import base64
            base64.b64decode(image_data)
            
            # Check reasonable size (max 10MB)
            if len(image_data) > 15 * 1024 * 1024:  # Base64 is ~33% larger
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        
        return validators.url(url)
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> Optional[str]:
        """Sanitize string input
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum length of output string
            
        Returns:
            Optional[str]: Sanitized string or None
        """
        if not input_str or not isinstance(input_str, str):
            return None
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_str)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_json_data(data: Dict[str, Any], required_fields: list) -> Dict[str, Any]:
        """Validate JSON request data"""
        if not isinstance(data, dict):
            return {'valid': False, 'errors': ['Invalid JSON data']}
        
        errors = []
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            errors.append(f'Missing required fields: {", ".join(missing_fields)}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
        """Validate file extension"""
        if not filename or not isinstance(filename, str):
            return False
        
        # Get file extension
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in allowed_extensions
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
        """Validate file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        return 0 < file_size <= max_size_bytes 