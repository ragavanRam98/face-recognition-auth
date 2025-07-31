from abc import ABC, abstractmethod
from typing import Optional, Dict
import numpy as np

class IFaceRecognitionService(ABC):
    """Interface for face recognition service"""
    
    @abstractmethod
    def detect_faces(self, image_data: bytes) -> Optional[str]:
        """Detect and save face from image data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Optional[str]: Filename of saved face image or None
        """
        pass
    
    @abstractmethod
    def recognize_face(self, image_data: bytes) -> Optional[Dict]:
        """Recognize face from image data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Optional[Dict]: Recognition result with filename, file_path, and confidence
        """
        pass
    
    @abstractmethod
    def get_face_encoding(self, image_data: bytes) -> Optional[np.ndarray]:
        """Get face encoding from image data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Optional[np.ndarray]: Face encoding array or None
        """
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict:
        """Get cache statistics
        
        Returns:
            Dict: Cache statistics
        """
        pass 