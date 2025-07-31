from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IInputValidator(ABC):
    """Interface for input validation"""
    
    @abstractmethod
    def validate_email(self, email: str) -> bool:
        """Validate email format
        
        Args:
            email: Email string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_username(self, username: str) -> bool:
        """Validate username format
        
        Args:
            username: Username string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength
        
        Args:
            password: Password string to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and 'errors' list
        """
        pass
    
    @abstractmethod
    def validate_json_data(self, data: Dict[str, Any], required_fields: list) -> Dict[str, Any]:
        """Validate JSON request data
        
        Args:
            data: JSON data to validate
            required_fields: List of required field names
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and 'errors' list
        """
        pass 