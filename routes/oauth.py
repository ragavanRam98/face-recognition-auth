from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, g, current_app
from models import db, User, Client, Grant, Token
from utils.validators import InputValidator
from werkzeug.security import gen_salt
import logging

logger = logging.getLogger(__name__)
oauth_bp = Blueprint('oauth', __name__)

@oauth_bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """OAuth2 authorization endpoint"""
    oauth = current_app.oauth
    
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('auth.login', next=request.url))
    
    g.user = user
    
    if request.method == 'GET':
        # Get client information
        client_id = request.args.get('client_id')
        scope = request.args.get('scope', '')
        redirect_uri = request.args.get('redirect_uri')
        
        if not client_id:
            return jsonify({'error': 'Missing client_id parameter'}), 400
        
        client = Client.query.filter_by(client_id=client_id).first()
        if not client:
            return jsonify({'error': 'Invalid client_id'}), 400
        
        return render_template('oauth/authorize.html', 
                            client=client, 
                            scope=scope, 
                            redirect_uri=redirect_uri)
    
    # POST request - user confirmed authorization
    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'

@oauth_bp.route('/token', methods=['POST'])
def access_token():
    """OAuth2 token endpoint"""
    oauth = current_app.oauth
    return oauth.create_token_response()

@oauth_bp.route('/revoke', methods=['POST'])
def revoke_token():
    """OAuth2 token revocation endpoint"""
    oauth = current_app.oauth
    return oauth.create_endpoint_response('revoke')

@oauth_bp.route('/clients', methods=['GET'])
def list_clients():
    """List OAuth2 clients for current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        clients = Client.query.filter_by(user_id=user.id).all()
        
        clients_data = []
        for client in clients:
            clients_data.append({
                'id': client.id,
                'name': client.name,
                'client_id': client.client_id,
                'client_uri': client.client_uri,
                'redirect_uris': client.redirect_uris,
                'default_scopes': client.default_scopes,
                'created_at': client.created_at.isoformat() if client.created_at else None
            })
        
        return jsonify({
            'clients': clients_data,
            'total_clients': len(clients_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error listing clients: {e}')
        return jsonify({'error': 'Failed to list clients'}), 500

@oauth_bp.route('/clients', methods=['POST'])
def create_client():
    """Create new OAuth2 client"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'client_uri', 'redirect_uris']
        validation = InputValidator.validate_json_data(data, required_fields)
        if not validation['valid']:
            return jsonify({'error': 'Validation failed', 'details': validation['errors']}), 400
        
        name = data['name']
        client_uri = data['client_uri']
        redirect_uris = data['redirect_uris']
        
        # Validate input
        if not InputValidator.sanitize_string(name, 40):
            return jsonify({'error': 'Invalid client name'}), 400
        
        if not InputValidator.validate_url(client_uri):
            return jsonify({'error': 'Invalid client URI'}), 400
        
        # Validate redirect URIs
        if isinstance(redirect_uris, str):
            redirect_uris = [redirect_uris]
        
        for uri in redirect_uris:
            if not InputValidator.validate_url(uri):
                return jsonify({'error': f'Invalid redirect URI: {uri}'}), 400
        
        # Get user
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate client credentials
        client_id = gen_salt(24)
        client_secret = gen_salt(48)
        
        # Create client
        client = Client(
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            client_uri=client_uri,
            _redirect_uris=' '.join(redirect_uris),
            user_id=user.id
        )
        
        db.session.add(client)
        db.session.commit()
        
        logger.info(f'New OAuth2 client created: {name} by user {user.username}')
        
        return jsonify({
            'message': 'Client created successfully',
            'client': {
                'id': client.id,
                'name': client.name,
                'client_id': client.client_id,
                'client_secret': client.client_secret,
                'client_uri': client.client_uri,
                'redirect_uris': client.redirect_uris
            }
        }), 201
        
    except Exception as e:
        logger.error(f'Error creating client: {e}')
        db.session.rollback()
        return jsonify({'error': 'Failed to create client'}), 500

@oauth_bp.route('/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Get specific OAuth2 client"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        client = Client.query.filter_by(id=client_id, user_id=user.id).first()
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        return jsonify({
            'client': {
                'id': client.id,
                'name': client.name,
                'client_id': client.client_id,
                'client_secret': client.client_secret,
                'client_uri': client.client_uri,
                'redirect_uris': client.redirect_uris,
                'default_scopes': client.default_scopes,
                'created_at': client.created_at.isoformat() if client.created_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting client: {e}')
        return jsonify({'error': 'Failed to get client'}), 500

@oauth_bp.route('/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    """Update OAuth2 client"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        client = Client.query.filter_by(id=client_id, user_id=user.id).first()
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Update fields if provided
        if 'name' in data:
            name = InputValidator.sanitize_string(data['name'], 40)
            if not name:
                return jsonify({'error': 'Invalid client name'}), 400
            client.name = name
        
        if 'client_uri' in data:
            if not InputValidator.validate_url(data['client_uri']):
                return jsonify({'error': 'Invalid client URI'}), 400
            client.client_uri = data['client_uri']
        
        if 'redirect_uris' in data:
            redirect_uris = data['redirect_uris']
            if isinstance(redirect_uris, str):
                redirect_uris = [redirect_uris]
            
            for uri in redirect_uris:
                if not InputValidator.validate_url(uri):
                    return jsonify({'error': f'Invalid redirect URI: {uri}'}), 400
            
            client._redirect_uris = ' '.join(redirect_uris)
        
        db.session.commit()
        
        logger.info(f'OAuth2 client updated: {client.name} by user {user.username}')
        
        return jsonify({
            'message': 'Client updated successfully',
            'client': {
                'id': client.id,
                'name': client.name,
                'client_id': client.client_id,
                'client_uri': client.client_uri,
                'redirect_uris': client.redirect_uris
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error updating client: {e}')
        db.session.rollback()
        return jsonify({'error': 'Failed to update client'}), 500

@oauth_bp.route('/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete OAuth2 client"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        client = Client.query.filter_by(id=client_id, user_id=user.id).first()
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Delete associated tokens and grants
        Token.query.filter_by(client_id=client.client_id).delete()
        Grant.query.filter_by(client_id=client.client_id).delete()
        
        # Delete client
        db.session.delete(client)
        db.session.commit()
        
        logger.info(f'OAuth2 client deleted: {client.name} by user {user.username}')
        
        return jsonify({'message': 'Client deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f'Error deleting client: {e}')
        db.session.rollback()
        return jsonify({'error': 'Failed to delete client'}), 500

@oauth_bp.route('/tokens', methods=['GET'])
def list_tokens():
    """List OAuth2 tokens for current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        tokens = Token.query.filter_by(user_id=user.id).all()
        
        tokens_data = []
        for token in tokens:
            client = Client.query.filter_by(client_id=token.client_id).first()
            tokens_data.append({
                'id': token.id,
                'client_name': client.name if client else 'Unknown',
                'token_type': token.token_type,
                'scope': token.scope,
                'expires': token.expires.isoformat() if token.expires else None,
                'created_at': token.created_at.isoformat() if token.created_at else None,
                'is_expired': token.is_expired()
            })
        
        return jsonify({
            'tokens': tokens_data,
            'total_tokens': len(tokens_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error listing tokens: {e}')
        return jsonify({'error': 'Failed to list tokens'}), 500

@oauth_bp.route('/tokens/<int:token_id>', methods=['DELETE'])
def revoke_token_by_id(token_id):
    """Revoke specific OAuth2 token"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        token = Token.query.filter_by(id=token_id, user_id=user.id).first()
        if not token:
            return jsonify({'error': 'Token not found'}), 404
        
        db.session.delete(token)
        db.session.commit()
        
        logger.info(f'OAuth2 token revoked by user {user.username}')
        
        return jsonify({'message': 'Token revoked successfully'}), 200
        
    except Exception as e:
        logger.error(f'Error revoking token: {e}')
        db.session.rollback()
        return jsonify({'error': 'Failed to revoke token'}), 500 