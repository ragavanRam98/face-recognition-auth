from flask import Blueprint, request, jsonify, current_app
from models import db, User, Client, Token
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

@api_bp.route('/user', methods=['GET'])
def get_user_info():
    """Get current user information (requires OAuth2)"""
    oauth = current_app.oauth
    
    @oauth.require_oauth('email')
    def protected():
        oauth = request.oauth
        user = oauth.user
        
        return jsonify({
            'user': user.to_dict(),
            'client': {
                'name': oauth.client.name,
                'client_id': oauth.client.client_id
            }
        })
    
    return protected()

@api_bp.route('/user/face', methods=['GET'])
def get_user_face_info():
    """Get user face information (requires OAuth2)"""
    oauth = current_app.oauth
    
    @oauth.require_oauth('email')
    def protected():
        oauth = request.oauth
        user = oauth.user
        
        face_images = user.face_images
        images_data = []
        
        for face_image in face_images:
            images_data.append({
                'id': face_image.id,
                'is_primary': face_image.is_primary,
                'created_at': face_image.created_at.isoformat() if face_image.created_at else None
            })
        
        return jsonify({
            'user': user.to_dict(),
            'face_images': images_data,
            'total_face_images': len(images_data)
        })
    
    return protected()

@api_bp.route('/user/face', methods=['POST'])
def register_user_face():
    """Register face images for user (requires OAuth2)"""
    oauth = current_app.oauth
    
    @oauth.require_oauth('email')
    def protected():
        oauth = request.oauth
        user = oauth.user
        
        try:
            data = request.get_json()
            
            # Validate required fields
            from utils.validators import InputValidator
            required_fields = ['images']
            validation = InputValidator.validate_json_data(data, required_fields)
            if not validation['valid']:
                return jsonify({'error': 'Validation failed', 'details': validation['errors']}), 400
            
            images = data['images']
            
            if not isinstance(images, list):
                return jsonify({'error': 'Images must be a list'}), 400
            
            # Validate number of images
            max_images = current_app.config['MAX_IMAGES_PER_USER']
            if len(images) < 3:
                return jsonify({'error': f'At least 3 images required, got {len(images)}'}), 400
            
            if len(images) > max_images:
                return jsonify({'error': f'Maximum {max_images} images allowed, got {len(images)}'}), 400
            
            # Check if user already has face images
            existing_images = len(user.face_images)
            if existing_images > 0:
                return jsonify({'error': 'Face images already registered for this user'}), 409
            
            face_service = current_app.face_service
            successful_images = 0
            
            for i, image_data in enumerate(images):
                try:
                    # Validate base64 image
                    if not InputValidator.validate_base64_image(image_data):
                        logger.warning(f'Invalid image format for image {i+1}')
                        continue
                    
                    # Convert base64 to bytes
                    import base64
                    if image_data.startswith('data:image/'):
                        image_data = image_data.split(',')[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    
                    # Detect and save face
                    filename = face_service.detect_faces(image_bytes)
                    if not filename:
                        logger.warning(f'No face detected in image {i+1}')
                        continue
                    
                    # Get face encoding
                    encoding = face_service.get_face_encoding(image_bytes)
                    if encoding is None:
                        logger.warning(f'Could not get face encoding for image {i+1}')
                        continue
                    
                    # Save to database
                    from models import FaceImage
                    face_image = FaceImage(
                        user_id=user.id,
                        file_path=filename,
                        encoding_data=face_service.encode_face_encoding(encoding),
                        is_primary=(i == 0)  # First image is primary
                    )
                    
                    db.session.add(face_image)
                    successful_images += 1
                    
                except Exception as e:
                    logger.error(f'Error processing image {i+1}: {e}')
                    continue
            
            if successful_images < 3:
                # Rollback if not enough successful images
                db.session.rollback()
                return jsonify({'error': f'Only {successful_images} valid images processed, minimum 3 required'}), 400
            
            db.session.commit()
            
            logger.info(f'Face registration successful for user {user.username}: {successful_images} images')
            
            return jsonify({
                'message': 'Face registration successful',
                'images_processed': successful_images,
                'user_id': user.id
            }), 201
            
        except Exception as e:
            logger.error(f'Face registration error: {e}')
            db.session.rollback()
            return jsonify({'error': 'Face registration failed'}), 500
    
    return protected()

@api_bp.route('/face/recognize', methods=['POST'])
def recognize_face_api():
    """Recognize face from image (requires OAuth2)"""
    oauth = current_app.oauth
    
    @oauth.require_oauth('email')
    def protected():
        try:
            data = request.get_json()
            
            # Validate required fields
            from utils.validators import InputValidator
            required_fields = ['image']
            validation = InputValidator.validate_json_data(data, required_fields)
            if not validation['valid']:
                return jsonify({'error': 'Validation failed', 'details': validation['errors']}), 400
            
            image_data = data['image']
            
            # Validate base64 image
            if not InputValidator.validate_base64_image(image_data):
                return jsonify({'error': 'Invalid image format'}), 400
            
            # Convert base64 to bytes
            import base64
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            
            # Recognize face
            face_service = current_app.face_service
            recognition_result = face_service.recognize_face(image_bytes)
            
            if not recognition_result:
                return jsonify({'error': 'Face not recognized'}), 404
            
            # Find user by face image
            from models import FaceImage
            face_image = FaceImage.query.filter_by(file_path=recognition_result['file_path']).first()
            if not face_image:
                return jsonify({'error': 'Face not registered'}), 404
            
            recognized_user = face_image.user
            
            return jsonify({
                'message': 'Face recognized',
                'user': recognized_user.to_dict(),
                'confidence': recognition_result['confidence'],
                'face_image_id': face_image.id
            }), 200
            
        except Exception as e:
            logger.error(f'Face recognition error: {e}')
            return jsonify({'error': 'Face recognition failed'}), 500
    
    return protected()

@api_bp.route('/stats', methods=['GET'])
def get_api_stats():
    """Get API statistics (requires OAuth2)"""
    oauth = current_app.oauth
    
    @oauth.require_oauth('email')
    def protected():
        oauth = request.oauth
        user = oauth.user
        
        try:
            # Get user statistics
            total_face_images = len(user.face_images)
            total_clients = len(user.clients)
            total_tokens = len(user.tokens)
            
            # Get face service statistics
            face_service = current_app.face_service
            cache_stats = face_service.get_cache_stats()
            
            return jsonify({
                'user': user.to_dict(),
                'statistics': {
                    'face_images': total_face_images,
                    'oauth_clients': total_clients,
                    'oauth_tokens': total_tokens
                },
                'face_service': cache_stats
            }), 200
            
        except Exception as e:
            logger.error(f'Error getting API stats: {e}')
            return jsonify({'error': 'Failed to get statistics'}), 500
    
    return protected()

@api_bp.route('/health', methods=['GET'])
def api_health_check():
    """API health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Test face service
        face_service = current_app.face_service
        cache_stats = face_service.get_cache_stats()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'face_service': 'operational',
            'cache_stats': cache_stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f'API health check failed: {e}')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@api_bp.route('/version', methods=['GET'])
def get_api_version():
    """Get API version information"""
    return jsonify({
        'version': '1.0.0',
        'name': 'Face-Id API',
        'description': 'Face Recognition Authentication API',
        'features': [
            'Face recognition authentication',
            'OAuth2 provider',
            'User management',
            'Face image registration'
        ]
    }), 200 