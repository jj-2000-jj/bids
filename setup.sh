#!/bin/bash
# Automated setup script for SCADA RFP Finder

echo "SCADA RFP Finder - Setup Script"
echo "=============================="
echo

# Install required dependencies
echo "Installing required dependencies..."
pip3 install beautifulsoup4 requests

# Create necessary directories
echo "Creating directories..."
mkdir -p rfp_documents

# Initialize the database
echo "Initializing database..."
python3 cli.py scrape --state AZ --db rfps.db --output rfp_documents

echo
echo "Setup completed successfully!"
echo
echo "To start using SCADA RFP Finder:"
echo "1. Edit config.json with your email settings"
echo "2. Run 'python3 cli.py scrape' to collect RFPs from all states"
echo "3. Run 'python3 cli.py filter' to analyze RFP relevance"
echo "4. Run 'python3 cli.py notify --email your@email.com --digest' to receive notifications"
echo
echo "For more information, see README.md"
