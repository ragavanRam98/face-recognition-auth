import face_recognition as fr
import cv2
import numpy as np
import json
import os
import logging
from typing import List, Optional, Tuple, Dict
from PIL import Image
import io
import base64
from functools import lru_cache
import threading
import time

logger = logging.getLogger(__name__)

from interfaces.face_recognition import IFaceRecognitionService

class FaceRecognitionService(IFaceRecognitionService):
    """Face recognition service implementation"""
    
    def __init__(self, faces_dir: str, tolerance: float = 0.6):
        self.faces_dir = faces_dir
        self.tolerance = tolerance
        self._face_cache = {}
        self._cache_lock = threading.Lock()
        self._last_cache_update = 0
        self._cache_ttl = 300  # 5 minutes
        
        # Ensure faces directory exists
        os.makedirs(faces_dir, exist_ok=True)
        
        # Initialize face cache
        self._update_face_cache()
    
    def _update_face_cache(self) -> None:
        """Update face encodings cache"""
        try:
            with self._cache_lock:
                current_time = time.time()
                if current_time - self._last_cache_update < self._cache_ttl:
                    return
                
                self._face_cache.clear()
                if not os.path.exists(self.faces_dir):
                    return
                
                for filename in os.listdir(self.faces_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(self.faces_dir, filename)
                        try:
                            image = cv2.imread(file_path)
                            if image is None:
                                continue
                            
                            # Convert BGR to RGB
                            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            encodings = fr.face_encodings(rgb_image)
                            
                            if encodings:
                                self._face_cache[filename] = {
                                    'encoding': encodings[0],
                                    'file_path': file_path
                                }
                        except Exception as e:
                            logger.error(f"Error processing face file {filename}: {e}")
                
                self._last_cache_update = current_time
                logger.info(f"Updated face cache with {len(self._face_cache)} faces")
                
        except Exception as e:
            logger.error(f"Error updating face cache: {e}")
    
    def validate_image(self, image_data: bytes) -> bool:
        """Validate image data"""
        try:
            image = Image.open(io.BytesIO(image_data))
            # Check image format
            if image.format not in ['JPEG', 'PNG']:
                return False
            
            # Check image size (max 10MB)
            if len(image_data) > 10 * 1024 * 1024:
                return False
            
            # Check image dimensions
            if image.width > 4096 or image.height > 4096:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False
    
    def detect_faces(self, image_data: bytes) -> Optional[str]:
        """Detect and save face from image data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Optional[str]: Filename of saved face image or None
        """
        try:
            if not self.validate_image(image_data):
                return None
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return None
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = fr.face_locations(rgb_image)
            face_encodings = fr.face_encodings(rgb_image)
            
            # Ensure exactly one face
            if len(face_locations) != 1 or len(face_encodings) != 1:
                logger.warning(f"Expected 1 face, found {len(face_locations)}")
                return None
            
            # Generate unique filename
            filename = f"{int(time.time())}_{os.getpid()}.jpg"
            file_path = os.path.join(self.faces_dir, filename)
            
            # Save image
            cv2.imwrite(file_path, image)
            
            # Update cache
            self._face_cache[filename] = {
                'encoding': face_encodings[0],
                'file_path': file_path
            }
            
            logger.info(f"Face detected and saved: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return None
    
    def recognize_face(self, image_data: bytes) -> Optional[Dict]:
        """Recognize face from image data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Optional[Dict]: Recognition result with filename, file_path, and confidence
        """
        try:
            if not self.validate_image(image_data):
                return None
            
            # Update cache if needed
            self._update_face_cache()
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return None
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get face encoding
            face_encodings = fr.face_encodings(rgb_image)
            if not face_encodings:
                return None
            
            input_encoding = face_encodings[0]
            
            # Compare with cached faces
            with self._cache_lock:
                for filename, face_data in self._face_cache.items():
                    try:
                        matches = fr.compare_faces(
                            [face_data['encoding']], 
                            input_encoding, 
                            tolerance=self.tolerance
                        )
                        
                        if matches[0]:
                            # Calculate confidence
                            distance = fr.face_distance([face_data['encoding']], input_encoding)[0]
                            confidence = 1 - distance
                            
                            return {
                                'filename': filename,
                                'file_path': face_data['file_path'],
                                'confidence': float(confidence)
                            }
                    except Exception as e:
                        logger.error(f"Error comparing face {filename}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return None
    
    def get_face_encoding(self, image_data: bytes) -> Optional[np.ndarray]:
        """Get face encoding from image data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Optional[np.ndarray]: Face encoding array or None
        """
        try:
            if not self.validate_image(image_data):
                return None
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return None
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get face encoding
            face_encodings = fr.face_encodings(rgb_image)
            if not face_encodings:
                return None
            
            return face_encodings[0]
            
        except Exception as e:
            logger.error(f"Error getting face encoding: {e}")
            return None
    
    def encode_face_encoding(self, encoding: np.ndarray) -> str:
        """Encode face encoding to JSON string
        
        Args:
            encoding: Face encoding numpy array
            
        Returns:
            str: JSON string representation of encoding
        """
        return json.dumps(encoding.tolist())
    
    def decode_face_encoding(self, encoding_str: str) -> np.ndarray:
        """Decode face encoding from JSON string
        
        Args:
            encoding_str: JSON string representation of encoding
            
        Returns:
            np.ndarray: Face encoding numpy array
        """
        return np.array(json.loads(encoding_str))
    
    def cleanup_old_files(self, max_age_days: int = 30) -> None:
        """Clean up old temporary files
        
        Args:
            max_age_days: Maximum age of files to keep in days
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            for filename in os.listdir(self.faces_dir):
                file_path = os.path.join(self.faces_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            logger.info(f"Cleaned up old file: {filename}")
                        except OSError as e:
                            logger.error(f"Error cleaning up file {filename}: {e}")
                            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics
        
        Returns:
            Dict: Cache statistics including cached_faces, last_update, and cache_ttl
        """
        with self._cache_lock:
            return {
                'cached_faces': len(self._face_cache),
                'last_update': self._last_cache_update,
                'cache_ttl': self._cache_ttl
            } 