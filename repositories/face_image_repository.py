from typing import Optional, List
from models import db, FaceImage
from interfaces.repositories import IFaceImageRepository

class FaceImageRepository(IFaceImageRepository):
    """Face image repository implementation"""
    
    def find_by_user_id(self, user_id: int) -> List[FaceImage]:
        """Find face images by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            List[FaceImage]: List of face images
        """
        return FaceImage.query.filter_by(user_id=user_id).all()
    
    def find_by_id(self, image_id: int) -> Optional[FaceImage]:
        """Find face image by ID
        
        Args:
            image_id: Image ID
            
        Returns:
            Optional[FaceImage]: Face image object or None
        """
        return FaceImage.query.get(image_id)
    
    def create(self, face_image: FaceImage) -> FaceImage:
        """Create new face image
        
        Args:
            face_image: Face image object to create
            
        Returns:
            FaceImage: Created face image object
        """
        db.session.add(face_image)
        db.session.commit()
        return face_image
    
    def delete(self, face_image: FaceImage) -> None:
        """Delete face image
        
        Args:
            face_image: Face image object to delete
        """
        # Delete the actual file first
        face_image.delete_file()
        
        # Delete from database
        db.session.delete(face_image)
        db.session.commit()
    
    def find_by_file_path(self, file_path: str) -> Optional[FaceImage]:
        """Find face image by file path
        
        Args:
            file_path: File path to search for
            
        Returns:
            Optional[FaceImage]: Face image object or None
        """
        return FaceImage.query.filter_by(file_path=file_path).first() 