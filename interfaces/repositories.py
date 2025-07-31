from abc import ABC, abstractmethod
from typing import Optional, List
from models import User, FaceImage, Client, Grant, Token

class IUserRepository(ABC):
    """Interface for user repository operations"""
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username
        
        Args:
            username: Username to search for
            
        Returns:
            Optional[User]: User object or None
        """
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email
        
        Args:
            email: Email to search for
            
        Returns:
            Optional[User]: User object or None
        """
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User object or None
        """
        pass
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Create new user
        
        Args:
            user: User object to create
            
        Returns:
            User: Created user object
        """
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Update user
        
        Args:
            user: User object to update
            
        Returns:
            User: Updated user object
        """
        pass

class IFaceImageRepository(ABC):
    """Interface for face image repository operations"""
    
    @abstractmethod
    def find_by_user_id(self, user_id: int) -> List[FaceImage]:
        """Find face images by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            List[FaceImage]: List of face images
        """
        pass
    
    @abstractmethod
    def find_by_id(self, image_id: int) -> Optional[FaceImage]:
        """Find face image by ID
        
        Args:
            image_id: Image ID
            
        Returns:
            Optional[FaceImage]: Face image object or None
        """
        pass
    
    @abstractmethod
    def create(self, face_image: FaceImage) -> FaceImage:
        """Create new face image
        
        Args:
            face_image: Face image object to create
            
        Returns:
            FaceImage: Created face image object
        """
        pass
    
    @abstractmethod
    def delete(self, face_image: FaceImage) -> None:
        """Delete face image
        
        Args:
            face_image: Face image object to delete
        """
        pass
    
    @abstractmethod
    def find_by_file_path(self, file_path: str) -> Optional[FaceImage]:
        """Find face image by file path
        
        Args:
            file_path: File path to search for
            
        Returns:
            Optional[FaceImage]: Face image object or None
        """
        pass 