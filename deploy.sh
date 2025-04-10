#!/bin/bash
# Deployment script for SCADA RFP Finder Web Application

echo "SCADA RFP Finder Web Application - Deployment Script"
echo "==================================================="
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker before proceeding."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose before proceeding."
    exit 1
fi

# Create data directory
mkdir -p data
echo "Created data directory for persistent storage"

# Build and start the application
echo "Building and starting the application..."
docker-compose up -d --build

# Check if the application is running
if [ $? -eq 0 ]; then
    echo
    echo "SCADA RFP Finder Web Application is now running!"
    echo "You can access it at: http://localhost:5000"
    echo
    echo "To create an admin user, run:"
    echo "docker-compose exec web python -c \"from webapp import create_app, db; from webapp.models import User; app = create_app(); app.app_context().push(); admin = User(username='admin', email='admin@example.com', password='adminpassword', is_admin=True); db.session.add(admin); db.session.commit(); print('Admin user created successfully!');\""
    echo
    echo "To stop the application, run:"
    echo "docker-compose down"
else
    echo "Failed to start the application. Please check the logs for more information."
    exit 1
fi
