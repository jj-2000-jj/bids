#!/bin/bash

# Setup script for SCADA RFP Finder
# This script prepares the system for local deployment

echo "Setting up SCADA RFP Finder for local deployment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python -c "from webapp import create_app, db; app = create_app(); with app.app_context(): db.create_all()"

# Run migrations
echo "Running database migrations..."
python run_migrations.py

# Initialize states
echo "Initializing states..."
python init_states.py

echo "Setup complete! You can now run the application with:"
echo "python run.py"
echo ""
echo "The application will be available at http://localhost:5000"
echo ""
echo "For more information, see DEPLOYMENT.md"
