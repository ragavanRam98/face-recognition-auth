from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> tuple:
    """User registration endpoint
    
    Returns:
        tuple: JSON response and status code
    """
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        validation = current_app.auth_service.validator.validate_json_data(data, required_fields)
        if not validation['valid']:
            return current_app.error_handler.handle_validation_error(validation['errors'])
        
        username = data['username']
        email = data['email']
        password = data['password']
        
        # Use auth service for registration
        result = current_app.auth_service.register_user(username, email, password)
        
        if not result['success']:
            if 'Username already exists' in result['error'] or 'Email already exists' in result['error']:
                return current_app.error_handler.handle_conflict_error(result['error'])
            return current_app.error_handler.handle_validation_error([result['error']])
        
        # Log in user
        session['user_id'] = result['user']['id']
        
        if request.is_json:
            return jsonify({
                'message': 'Registration successful',
                'user': result['user']
            }), 201
        else:
            flash('Registration successful!', 'success')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        logger.error(f'Registration error: {e}')
        return current_app.error_handler.handle_server_error('Registration failed')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> tuple:
    """User login endpoint
    
    Returns:
        tuple: JSON response and status code
    """
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate required fields
        required_fields = ['username', 'password']
        validation = current_app.auth_service.validator.validate_json_data(data, required_fields)
        if not validation['valid']:
            return current_app.error_handler.handle_validation_error(validation['errors'])
        
        username = data['username']
        password = data['password']
        
        # Use auth service for authentication
        result = current_app.auth_service.authenticate_user(username, password)
        
        if not result['success']:
            if 'Invalid credentials' in result['error']:
                return current_app.error_handler.handle_authentication_error(result['error'])
            elif 'Account is disabled' in result['error']:
                return current_app.error_handler.handle_authorization_error(result['error'])
            else:
                return current_app.error_handler.handle_server_error(result['error'])
        
        # Log in user
        session['user_id'] = result['user']['id']
        
        if request.is_json:
            return jsonify({
                'message': 'Login successful',
                'user': result['user']
            }), 200
        else:
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
            
    except Exception as e:
        logger.error(f'Login error: {e}')
        return current_app.error_handler.handle_server_error('Login failed')

@auth_bp.route('/logout')
def logout() -> tuple:
    """User logout endpoint
    
    Returns:
        tuple: JSON response and status code
    """
    if 'user_id' in session:
        user_id = session['user_id']
        user = current_app.auth_service.get_user_by_id(user_id)
        if user:
            logger.info(f'User logged out: {user.username}')
        
        session.pop('user_id', None)
    
    if request.is_json:
        return jsonify({'message': 'Logout successful'}), 200
    else:
        flash('Logout successful!', 'info')
        return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'PUT'])
def profile() -> tuple:
    """User profile management
    
    Returns:
        tuple: JSON response and status code
    """
    if 'user_id' not in session:
        return current_app.error_handler.handle_authentication_error()
    
    user = current_app.auth_service.get_user_by_id(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return current_app.error_handler.handle_not_found_error('User not found')
    
    if request.method == 'GET':
        if request.is_json:
            return jsonify({'user': user.to_dict()}), 200
        else:
            return render_template('profile.html', user=user)
    
    # PUT request for profile update
    try:
        data = request.get_json()
        
        # Validate email if provided
        if 'email' in data:
            if not InputValidator.validate_email(data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Check if email is already taken
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Email already exists'}), 409
            
            user.email = data['email']
        
        # Update password if provided
        if 'password' in data:
            password_validation = InputValidator.validate_password(data['password'])
            if not password_validation['valid']:
                return jsonify({'error': 'Password validation failed', 'details': password_validation['errors']}), 400
            
            user.set_password(data['password'])
        
        db.session.commit()
        
        logger.info(f'Profile updated for user: {user.username}')
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'Profile update error: {e}')
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/face-login', methods=['POST'])
def face_login() -> tuple:
    """Face recognition login endpoint
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        # Validate required fields
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
        from flask import current_app
        face_service = current_app.face_service
        recognition_result = face_service.recognize_face(image_bytes)
        
        if not recognition_result:
            logger.warning('Face recognition failed - no match found')
            return jsonify({'error': 'Face not recognized'}), 401
        
        # Find user by face image
        face_image = FaceImage.query.filter_by(file_path=recognition_result['file_path']).first()
        if not face_image:
            logger.warning('Face image not found in database')
            return jsonify({'error': 'Face not registered'}), 401
        
        user = face_image.user
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Log in user
        session['user_id'] = user.id
        
        logger.info(f'Face login successful for user: {user.username}')
        
        return jsonify({
            'message': 'Face login successful',
            'user': user.to_dict(),
            'confidence': recognition_result['confidence']
        }), 200
        
    except Exception as e:
        logger.error(f'Face login error: {e}')
        return jsonify({'error': 'Face login failed'}), 500 