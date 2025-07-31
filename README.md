# Face Recognition Authentication System

A face recognition authentication system built with Flask, featuring OAuth2 integration and security measures.

## Features

- User registration and authentication
- Face recognition using dlib and face_recognition library
- OAuth2 provider implementation
- RESTful API endpoints
- Security headers and rate limiting
- Docker containerization
- Nginx reverse proxy
- Logging and monitoring

## Project Structure

```
Face-Id/
├── app.py                          # Application factory
├── models.py                       # Database models
├── config.py                       # Configuration management
├── run.py                          # Application entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
├── docker-compose.yml             # Docker Compose setup
├── deploy.sh                      # Deployment script
├── .gitignore                     # Git ignore rules
├── env.example                    # Environment variables template
├── interfaces/                     # SOLID interfaces
│   ├── __init__.py
│   ├── face_recognition.py        # Face recognition interface
│   ├── repositories.py            # Repository interfaces
│   └── validators.py              # Validator interface
├── repositories/                   # Repository implementations
│   ├── __init__.py
│   ├── user_repository.py         # User repository
│   └── face_image_repository.py   # Face image repository
├── services/                       # Business logic services
│   ├── __init__.py
│   ├── face_recognition_service.py # Face recognition service
│   ├── auth_service.py            # Authentication service
│   ├── face_service.py            # Face management service
│   └── error_handler.py           # Error handling service
├── routes/                        # API route blueprints
│   ├── __init__.py
│   ├── auth.py                    # Authentication routes
│   ├── face.py                    # Face management routes
│   ├── oauth.py                   # OAuth2 routes
│   └── api.py                     # General API routes
├── utils/                         # Utility functions
│   ├── __init__.py
│   └── validators.py              # Input validation
├── templates/                      # HTML templates
├── static/                        # Static files
└── nginx/                         # Nginx configuration
```



## Installation and Setup

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- Git

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Face-Id
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   python run.py
   ```

6. **Run the application**:
   ```bash
   python run.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Or use the deployment script**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user profile

### Face Management
- `POST /face/register` - Register face images
- `POST /face/recognize` - Recognize face
- `GET /face/images` - Get user face images
- `DELETE /face/images/<id>` - Delete face image
- `POST /face/update` - Update face images

### OAuth2
- `GET /oauth/authorize` - Authorization endpoint
- `POST /oauth/token` - Token endpoint
- `GET /oauth/revoke` - Token revocation

### General
- `GET /health` - Health check endpoint

## Configuration

Key configuration options in `config.py`:

- `SECRET_KEY`: Application secret key
- `DATABASE_URL`: Database connection string
- `FACES_DIR`: Directory for face images
- `FACE_RECOGNITION_TOLERANCE`: Face recognition tolerance
- `MAX_IMAGES_PER_USER`: Maximum face images per user
- `RATE_LIMIT`: Rate limiting configuration

## Security Features

- Password hashing with bcrypt
- CSRF protection
- Security headers (HSTS, CSP, XSS Protection)
- Rate limiting
- Input validation and sanitization
- OAuth2 implementation

## Logging

The application uses structured logging with:
- File rotation
- Different log levels for development/production
- Error tracking and monitoring

## Monitoring

- Health check endpoint (`/health`)
- Database connection monitoring
- Service status monitoring
- Cache statistics

## Contributing

1. Follow SOLID principles
2. Add proper type hints and docstrings
3. Write unit tests for new functionality
4. Update documentation
5. Follow the existing code style

## License

This project is licensed under the MIT License. 