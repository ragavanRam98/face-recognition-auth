from typing import Optional, Dict, Any, List
from models import FaceImage
from interfaces.face_recognition import IFaceRecognitionService
from interfaces.repositories import IFaceImageRepository
from services.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)

class FaceService:
    """Face management service"""
    
    def __init__(self, face_recognition_service: IFaceRecognitionService, face_image_repository: IFaceImageRepository):
        """Initialize face service
        
        Args:
            face_recognition_service: Face recognition service interface
            face_image_repository: Face image repository interface
        """
        self.face_recognition_service = face_recognition_service
        self.face_image_repository = face_image_repository
    
    def register_face(self, user_id: int, image_data: bytes) -> Dict[str, Any]:
        """Register a new face for a user
        
        Args:
            user_id: User ID
            image_data: Raw image bytes
            
        Returns:
            Dict[str, Any]: Registration result with success status and face data or error
        """
        try:
            # Detect and save face
            filename = self.face_recognition_service.detect_faces(image_data)
            if not filename:
                return {'success': False, 'error': 'No face detected or multiple faces found'}
            
            # Get face encoding
            encoding = self.face_recognition_service.get_face_encoding(image_data)
            if not encoding:
                return {'success': False, 'error': 'Could not encode face'}
            
            # Create face image record
            face_image = FaceImage(
                user_id=user_id,
                file_path=f"faces/{filename}",
                encoding_data=self.face_recognition_service.encode_face_encoding(encoding)
            )
            
            created_face = self.face_image_repository.create(face_image)
            
            logger.info(f'Face registered for user {user_id}: {filename}')
            
            return {
                'success': True,
                'face_image': {
                    'id': created_face.id,
                    'filename': filename,
                    'file_path': created_face.file_path
                }
            }
            
        except Exception as e:
            logger.error(f'Face registration error: {e}')
            return {'success': False, 'error': 'Face registration failed'}
    
    def recognize_face(self, image_data: bytes) -> Dict[str, Any]:
        """Recognize a face
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dict[str, Any]: Recognition result with success status and user data or error
        """
        try:
            # Recognize face
            recognition_result = self.face_recognition_service.recognize_face(image_data)
            if not recognition_result:
                return {'success': False, 'error': 'Face not recognized'}
            
            # Find face image in database
            face_image = self.face_image_repository.find_by_file_path(recognition_result['file_path'])
            if not face_image:
                return {'success': False, 'error': 'Face not found in database'}
            
            logger.info(f'Face recognized: {recognition_result["filename"]}')
            
            return {
                'success': True,
                'user_id': face_image.user_id,
                'confidence': recognition_result['confidence'],
                'filename': recognition_result['filename']
            }
            
        except Exception as e:
            logger.error(f'Face recognition error: {e}')
            return {'success': False, 'error': 'Face recognition failed'}
    
    def get_user_faces(self, user_id: int) -> Dict[str, Any]:
        """Get all face images for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: Result with success status and face images or error
        """
        try:
            face_images = self.face_image_repository.find_by_user_id(user_id)
            
            return {
                'success': True,
                'face_images': [
                    {
                        'id': face.id,
                        'file_path': face.file_path,
                        'is_primary': face.is_primary,
                        'created_at': face.created_at.isoformat() if face.created_at else None
                    }
                    for face in face_images
                ]
            }
            
        except Exception as e:
            logger.error(f'Error getting user faces: {e}')
            return {'success': False, 'error': 'Failed to get face images'}
    
    def delete_face_image(self, image_id: int, user_id: int) -> Dict[str, Any]:
        """Delete a face image
        
        Args:
            image_id: Face image ID
            user_id: User ID for verification
            
        Returns:
            Dict[str, Any]: Deletion result with success status or error
        """
        try:
            face_image = self.face_image_repository.find_by_id(image_id)
            if not face_image:
                return {'success': False, 'error': 'Face image not found'}
            
            # Verify ownership
            if face_image.user_id != user_id:
                return {'success': False, 'error': 'Access denied'}
            
            self.face_image_repository.delete(face_image)
            
            logger.info(f'Face image deleted: {image_id}')
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f'Error deleting face image: {e}')
            return {'success': False, 'error': 'Failed to delete face image'} 