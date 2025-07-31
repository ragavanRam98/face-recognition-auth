from flask import Blueprint, request, jsonify, session, current_app
import base64
import logging

logger = logging.getLogger(__name__)
face_bp = Blueprint('face', __name__)

@face_bp.route('/register', methods=['POST'])
def register_face() -> tuple:
    """Register face images for a user
    
    Returns:
        tuple: JSON response and status code
    """
    if 'user_id' not in session:
        return current_app.error_handler.handle_authentication_error()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['images']
        validation = current_app.auth_service.validator.validate_json_data(data, required_fields)
        if not validation['valid']:
            return current_app.error_handler.handle_validation_error(validation['errors'])
        
        images = data['images']
        
        if not isinstance(images, list):
            return current_app.error_handler.handle_validation_error(['Images must be a list'])
        
        # Validate number of images
        max_images = current_app.config['MAX_IMAGES_PER_USER']
        if len(images) < 3:
            return current_app.error_handler.handle_validation_error([f'At least 3 images required, got {len(images)}'])
        
        if len(images) > max_images:
            return current_app.error_handler.handle_validation_error([f'Maximum {max_images} images allowed, got {len(images)}'])
        
        # Get user
        user = current_app.auth_service.get_user_by_id(session['user_id'])
        if not user:
            return current_app.error_handler.handle_not_found_error('User not found')
        
        # Check if user already has face images
        existing_faces = current_app.face_service.get_user_faces(user.id)
        if existing_faces['success'] and len(existing_faces['face_images']) > 0:
            return current_app.error_handler.handle_conflict_error('Face images already registered for this user')
        
        successful_images = 0
        
        for i, image_data in enumerate(images):
            try:
                # Validate base64 image
                if not current_app.auth_service.validator.validate_base64_image(image_data):
                    logger.warning(f'Invalid image format for image {i+1}')
                    continue
                
                # Convert base64 to bytes
                if image_data.startswith('data:image/'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                
                # Use face service to register face
                result = current_app.face_service.register_face(user.id, image_bytes)
                if result['success']:
                    successful_images += 1
                else:
                    logger.warning(f'Failed to register face for image {i+1}: {result["error"]}')
                
            except Exception as e:
                logger.error(f'Error processing image {i+1}: {e}')
                continue
        
        if successful_images < 3:
            return current_app.error_handler.handle_validation_error([f'Only {successful_images} valid images processed, minimum 3 required'])
        
        logger.info(f'Face registration successful for user {user.username}: {successful_images} images')
        
        return jsonify({
            'message': 'Face registration successful',
            'images_processed': successful_images,
            'user_id': user.id
        }), 201
        
    except Exception as e:
        logger.error(f'Face registration error: {e}')
        return current_app.error_handler.handle_server_error('Face registration failed')

@face_bp.route('/recognize', methods=['POST'])
def recognize_face() -> tuple:
    """Recognize face from image
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['image']
        validation = current_app.auth_service.validator.validate_json_data(data, required_fields)
        if not validation['valid']:
            return current_app.error_handler.handle_validation_error(validation['errors'])
        
        image_data = data['image']
        
        # Validate base64 image
        if not current_app.auth_service.validator.validate_base64_image(image_data):
            return current_app.error_handler.handle_validation_error(['Invalid image format'])
        
        # Convert base64 to bytes
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Recognize face
        # Use face service to recognize face
        result = current_app.face_service.recognize_face(image_bytes)
        
        if not result['success']:
            return current_app.error_handler.handle_not_found_error('Face not recognized')
        
        # Get user information
        user = current_app.auth_service.get_user_by_id(result['user_id'])
        if not user:
            return current_app.error_handler.handle_not_found_error('User not found')
        
        return jsonify({
            'message': 'Face recognized',
            'user': user.to_dict(),
            'confidence': result['confidence'],
            'filename': result['filename']
        }), 200
        
    except Exception as e:
        logger.error(f'Face recognition error: {e}')
        return current_app.error_handler.handle_server_error('Face recognition failed')

@face_bp.route('/images', methods=['GET'])
def get_user_face_images() -> tuple:
    """Get face images for current user
    
    Returns:
        tuple: JSON response and status code
    """
    if 'user_id' not in session:
        return current_app.error_handler.handle_authentication_error()
    
    try:
        user = current_app.auth_service.get_user_by_id(session['user_id'])
        if not user:
            return current_app.error_handler.handle_not_found_error('User not found')
        
        result = current_app.face_service.get_user_faces(user.id)
        
        if not result['success']:
            return current_app.error_handler.handle_server_error(result['error'])
        
        return jsonify({
            'user_id': user.id,
            'images': result['face_images'],
            'total_images': len(result['face_images'])
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting face images: {e}')
        return current_app.error_handler.handle_server_error('Failed to get face images')

@face_bp.route('/images/<int:image_id>', methods=['DELETE'])
def delete_face_image(image_id: int) -> tuple:
    """Delete a specific face image
    
    Args:
        image_id: ID of the face image to delete
        
    Returns:
        tuple: JSON response and status code
    """
    if 'user_id' not in session:
        return current_app.error_handler.handle_authentication_error()
    
    try:
        user = current_app.auth_service.get_user_by_id(session['user_id'])
        if not user:
            return current_app.error_handler.handle_not_found_error('User not found')
        
        # Use face service to delete face image
        result = current_app.face_service.delete_face_image(image_id, user.id)
        
        if not result['success']:
            if 'Face image not found' in result['error']:
                return current_app.error_handler.handle_not_found_error(result['error'])
            elif 'Access denied' in result['error']:
                return current_app.error_handler.handle_authorization_error(result['error'])
            else:
                return current_app.error_handler.handle_validation_error([result['error']])
        
        return jsonify({'message': 'Face image deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f'Error deleting face image: {e}')
        return current_app.error_handler.handle_server_error('Failed to delete face image')

@face_bp.route('/update', methods=['POST'])
def update_face_images() -> tuple:
    """Update face images for a user
    
    Returns:
        tuple: JSON response and status code
    """
    if 'user_id' not in session:
        return current_app.error_handler.handle_authentication_error()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['images']
        validation = current_app.auth_service.validator.validate_json_data(data, required_fields)
        if not validation['valid']:
            return current_app.error_handler.handle_validation_error(validation['errors'])
        
        images = data['images']
        
        if not isinstance(images, list):
            return current_app.error_handler.handle_validation_error(['Images must be a list'])
        
        # Validate number of images
        max_images = current_app.config['MAX_IMAGES_PER_USER']
        if len(images) < 3:
            return current_app.error_handler.handle_validation_error([f'At least 3 images required, got {len(images)}'])
        
        if len(images) > max_images:
            return current_app.error_handler.handle_validation_error([f'Maximum {max_images} images allowed, got {len(images)}'])
        
        # Get user
        user = current_app.auth_service.get_user_by_id(session['user_id'])
        if not user:
            return current_app.error_handler.handle_not_found_error('User not found')
        
        # Delete existing face images first
        existing_faces = current_app.face_service.get_user_faces(user.id)
        if existing_faces['success']:
            for face_image in existing_faces['face_images']:
                current_app.face_service.delete_face_image(face_image['id'], user.id)
        
        successful_images = 0
        
        for i, image_data in enumerate(images):
            try:
                # Validate base64 image
                if not current_app.auth_service.validator.validate_base64_image(image_data):
                    logger.warning(f'Invalid image format for image {i+1}')
                    continue
                
                # Convert base64 to bytes
                if image_data.startswith('data:image/'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                
                # Use face service to register face
                result = current_app.face_service.register_face(user.id, image_bytes)
                if result['success']:
                    successful_images += 1
                else:
                    logger.warning(f'Failed to register face for image {i+1}: {result["error"]}')
                
            except Exception as e:
                logger.error(f'Error processing image {i+1}: {e}')
                continue
        
        if successful_images < 3:
            return current_app.error_handler.handle_validation_error([f'Only {successful_images} valid images processed, minimum 3 required'])
        
        logger.info(f'Face images updated for user {user.username}: {successful_images} images')
        
        return jsonify({
            'message': 'Face images updated successfully',
            'images_processed': successful_images,
            'user_id': user.id
        }), 200
        
    except Exception as e:
        logger.error(f'Face update error: {e}')
        return current_app.error_handler.handle_server_error('Face update failed') 