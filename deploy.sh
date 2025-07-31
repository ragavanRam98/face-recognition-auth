#!/bin/bash

# Face-Id Production Deployment Script
# This script sets up the production environment

set -e  # Exit on any error

echo "Face-Id Production Deployment"
echo "============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Checking prerequisites..."

# Create necessary directories
print_status "Creating directories..."
mkdir -p faces logs nginx/ssl

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cp env.example .env
    print_status "Please edit .env file with your production settings"
    print_status "Especially update SECRET_KEY and JWT_SECRET_KEY"
fi

# Check if SSL certificates exist
if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    print_warning "SSL certificates not found in nginx/ssl/"
    print_status "Creating self-signed certificates for development..."
    
    # Create self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    print_status "Self-signed certificates created"
    print_warning "For production, replace with real SSL certificates"
fi

# Test the setup
print_status "Testing setup..."
python test_setup.py

if [ $? -eq 0 ]; then
    print_status "Setup test passed!"
else
    print_error "Setup test failed. Please check the errors above."
    exit 1
fi

# Build and start services
print_status "Building Docker images..."
docker-compose build

print_status "Starting services..."
docker-compose up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 10

# Check if services are running
print_status "Checking service status..."
if docker-compose ps | grep -q "Up"; then
    print_status "Services are running!"
else
    print_error "Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Test health endpoint
print_status "Testing health endpoint..."
sleep 5

if curl -f http://localhost/health > /dev/null 2>&1; then
    print_status "Health check passed!"
else
    print_warning "Health check failed. Services might still be starting..."
    print_status "You can check logs with: docker-compose logs -f"
fi

# Display information
echo ""
echo "Deployment completed!"
echo "===================="
echo "Application URL: https://localhost"
echo "Health Check: https://localhost/health"
echo "API Documentation: https://localhost/api/version"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Update application: docker-compose up -d --build"
echo ""
echo "For production deployment:"
echo "1. Update .env file with production settings"
echo "2. Replace SSL certificates in nginx/ssl/"
echo "3. Set up proper domain and DNS"
echo "4. Configure monitoring and backups"
echo ""
print_status "Face-Id is now running in production mode!" 