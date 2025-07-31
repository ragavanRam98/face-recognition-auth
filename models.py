from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
import uuid
import os

db = SQLAlchemy()

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    face_images = relationship('FaceImage', back_populates='user', cascade='all, delete-orphan')
    clients = relationship('Client', back_populates='user', cascade='all, delete-orphan')
    tokens = relationship('Token', back_populates='user', cascade='all, delete-orphan')
    grants = relationship('Grant', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password: str) -> None:
        """Hash and set password
        
        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses
        
        Returns:
            dict: User data as dictionary
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class FaceImage(db.Model):
    """Face image model"""
    __tablename__ = 'face_images'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    encoding_data = db.Column(db.Text, nullable=True)  # Store face encoding as JSON
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='face_images')
    
    def __init__(self, **kwargs):
        super(FaceImage, self).__init__(**kwargs)
        if not self.file_path:
            self.file_path = self._generate_file_path()
    
    def _generate_file_path(self) -> str:
        """Generate unique file path
        
        Returns:
            str: Unique file path
        """
        filename = f"{uuid.uuid4()}.jpg"
        return os.path.join('faces', filename)
    
    def delete_file(self) -> None:
        """Delete the actual image file"""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
        except OSError:
            pass  # File might already be deleted

class Client(db.Model):
    """OAuth2 client model"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    client_id = db.Column(db.String(40), unique=True, nullable=False)
    client_secret = db.Column(db.String(55), unique=True, nullable=False)
    client_uri = db.Column(db.Text)
    _redirect_uris = db.Column(db.Text)
    default_scope = db.Column(db.Text, default='email')
    response_types = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='clients')
    tokens = relationship('Token', back_populates='client', cascade='all, delete-orphan')
    grants = relationship('Grant', back_populates='client', cascade='all, delete-orphan')
    
    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []
    
    @property
    def default_redirect_uri(self):
        uris = self.redirect_uris
        return uris[0] if uris else None
    
    @property
    def default_scopes(self):
        if self.default_scope:
            return self.default_scope.split()
        return []
    
    @property
    def allowed_grant_types(self):
        return ['authorization_code', 'password', 'client_credentials', 'refresh_token']

class Grant(db.Model):
    """OAuth2 grant model"""
    __tablename__ = 'grants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    client_id = db.Column(db.String(40), db.ForeignKey('clients.client_id', ondelete='CASCADE'), nullable=False)
    code = db.Column(db.String(255), index=True, nullable=False)
    redirect_uri = db.Column(db.String(255))
    scope = db.Column(db.Text)
    expires = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='grants')
    client = relationship('Client', back_populates='grants')
    
    def delete(self) -> 'Grant':
        """Delete grant from database
        
        Returns:
            Grant: Deleted grant object
        """
        db.session.delete(self)
        db.session.commit()
        return self
    
    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []

class Token(db.Model):
    """OAuth2 token model"""
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(40), db.ForeignKey('clients.client_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    token_type = db.Column(db.String(40))
    access_token = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime, nullable=False)
    scope = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='tokens')
    client = relationship('Client', back_populates='tokens')
    
    def __init__(self, **kwargs):
        expires_in = kwargs.pop('expires_in', None)
        if expires_in is not None:
            self.expires = datetime.utcnow() + timedelta(seconds=expires_in)
        
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []
    
    def delete(self) -> 'Token':
        """Delete token from database
        
        Returns:
            Token: Deleted token object
        """
        db.session.delete(self)
        db.session.commit()
        return self
    
    def is_expired(self) -> bool:
        """Check if token is expired
        
        Returns:
            bool: True if token is expired, False otherwise
        """
        return datetime.utcnow() > self.expires 