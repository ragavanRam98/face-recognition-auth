#!/usr/bin/env python3
"""
Face-Id Application Runner
Face recognition authentication system
"""

import os
import sys
from app import create_app

def main() -> None:
    """Main application entry point"""
    # Get configuration from environment
    config_name = os.getenv('FLASK_ENV', 'development')
    
    # Create application
    app = create_app(config_name)
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Run application
    if __name__ == '__main__':
        print(f"Starting Face-Id application on {host}:{port}")
        print(f"Environment: {config_name}")
        print(f"Debug mode: {app.debug}")
        
        app.run(
            host=host,
            port=port,
            debug=app.debug
        )

if __name__ == '__main__':
    main() 