from typing import Optional
from models import db, User
from interfaces.repositories import IUserRepository

class UserRepository(IUserRepository):
    """User repository implementation"""
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username
        
        Args:
            username: Username to search for
            
        Returns:
            Optional[User]: User object or None
        """
        return User.query.filter_by(username=username).first()
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email
        
        Args:
            email: Email to search for
            
        Returns:
            Optional[User]: User object or None
        """
        return User.query.filter_by(email=email).first()
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User object or None
        """
        return User.query.get(user_id)
    
    def create(self, user: User) -> User:
        """Create new user
        
        Args:
            user: User object to create
            
        Returns:
            User: Created user object
        """
        db.session.add(user)
        db.session.commit()
        return user
    
    def update(self, user: User) -> User:
        """Update user
        
        Args:
            user: User object to update
            
        Returns:
            User: Updated user object
        """
        db.session.commit()
        return user 