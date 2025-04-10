#!/bin/bash
# Test script for SCADA RFP Finder Web Application

echo "SCADA RFP Finder Web Application - Test Script"
echo "=============================================="
echo

# Create test directory
TEST_DIR="webapp_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p $TEST_DIR
echo "Created test directory: $TEST_DIR"

# Create test database
TEST_DB="$TEST_DIR/test_rfp_finder.db"
echo "Using test database: $TEST_DB"

# Create test configuration
TEST_CONFIG="$TEST_DIR/test_config.py"
cat > $TEST_CONFIG << EOF
import os

SECRET_KEY = 'test_secret_key'
SQLALCHEMY_DATABASE_URI = 'sqlite:///$TEST_DB'
SQLALCHEMY_TRACK_MODIFICATIONS = False
TESTING = True
WTF_CSRF_ENABLED = False
EOF

echo "Created test configuration at: $TEST_CONFIG"

# Create test application
TEST_APP="$TEST_DIR/test_app.py"
cat > $TEST_APP << EOF
import os
import sys
from flask import Flask
from webapp import create_app

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create test app
app = create_app({
    'SECRET_KEY': 'test_secret_key',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///$TEST_DB',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'TESTING': True,
    'WTF_CSRF_ENABLED': False
})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
EOF

echo "Created test application at: $TEST_APP"

# Create test data script
TEST_DATA="$TEST_DIR/create_test_data.py"
cat > $TEST_DATA << EOF
import os
import sys
import datetime
from flask import Flask
from webapp import create_app, db
from webapp.models import User, RFP, State, SystemConfig

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create test app
app = create_app({
    'SECRET_KEY': 'test_secret_key',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///$TEST_DB',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'TESTING': True
})

def create_test_data():
    """Create test data for the application"""
    with app.app_context():
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_admin=True
        )
        db.session.add(admin)
        
        # Create regular user
        user = User(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        db.session.add(user)
        
        # Create states
        states = [
            ('AZ', 'Arizona'),
            ('NM', 'New Mexico'),
            ('UT', 'Utah'),
            ('ID', 'Idaho'),
            ('IL', 'Illinois'),
            ('MO', 'Missouri'),
            ('IA', 'Iowa'),
            ('IN', 'Indiana')
        ]
        
        for code, name in states:
            state = State(code=code, name=name)
            db.session.add(state)
        
        # Create sample RFPs
        sample_rfps = [
            {
                'id': 'AZ-2025-001',
                'state': 'AZ',
                'title': 'Water Treatment SCADA System Upgrade',
                'description': 'The City of Phoenix Water Services Department is seeking proposals for the upgrade of the existing SCADA system at the 91st Avenue Wastewater Treatment Plant.',
                'publication_date': datetime.date(2025, 3, 15),
                'due_date': datetime.date(2025, 4, 15),
                'agency': 'Phoenix Water Services',
                'scada_relevance_score': 95,
                'is_water_wastewater': True,
                'is_mining': False,
                'is_oil_gas': False
            },
            {
                'id': 'NM-2025-002',
                'state': 'NM',
                'title': 'Mining Operations Control System',
                'description': 'Request for proposals for a comprehensive control system for mining operations including SCADA integration, PLC programming, and HMI development.',
                'publication_date': datetime.date(2025, 3, 10),
                'due_date': datetime.date(2025, 4, 20),
                'agency': 'New Mexico Mining and Minerals Division',
                'scada_relevance_score': 87,
                'is_water_wastewater': False,
                'is_mining': True,
                'is_oil_gas': False
            },
            {
                'id': 'UT-2025-003',
                'state': 'UT',
                'title': 'Oil Field Monitoring System',
                'description': 'The Utah Division of Oil, Gas and Mining is seeking proposals for a real-time monitoring system for oil field operations using SCADA technology.',
                'publication_date': datetime.date(2025, 3, 5),
                'due_date': datetime.date(2025, 5, 1),
                'agency': 'Utah Division of Oil, Gas and Mining',
                'scada_relevance_score': 82,
                'is_water_wastewater': False,
                'is_mining': False,
                'is_oil_gas': True
            },
            {
                'id': 'ID-2025-004',
                'state': 'ID',
                'title': 'Municipal Water System Automation',
                'description': 'The City of Boise is seeking proposals for the automation of its municipal water system, including SCADA implementation, RTU installation, and integration with existing systems.',
                'publication_date': datetime.date(2025, 3, 20),
                'due_date': datetime.date(2025, 5, 10),
                'agency': 'Boise Public Works',
                'scada_relevance_score': 90,
                'is_water_wastewater': True,
                'is_mining': False,
                'is_oil_gas': False
            },
            {
                'id': 'IL-2025-005',
                'state': 'IL',
                'title': 'Industrial Control System Security Assessment',
                'description': 'The Illinois Department of Innovation & Technology is seeking proposals for a comprehensive security assessment of industrial control systems and SCADA networks across state facilities.',
                'publication_date': datetime.date(2025, 3, 25),
                'due_date': datetime.date(2025, 5, 15),
                'agency': 'Illinois Department of Innovation & Technology',
                'scada_relevance_score': 75,
                'is_water_wastewater': True,
                'is_mining': True,
                'is_oil_gas': True
            }
        ]
        
        for rfp_data in sample_rfps:
            rfp = RFP(**rfp_data)
            db.session.add(rfp)
        
        # Create system config
        configs = [
            ('app_name', 'SCADA RFP Finder', 'Application name'),
            ('scraper_frequency', 'daily', 'How often to run scrapers'),
            ('notification_from_email', 'noreply@scadarfpfinder.com', 'From email for notifications'),
            ('notification_from_name', 'SCADA RFP Finder', 'From name for notifications')
        ]
        
        for key, value, description in configs:
            config = SystemConfig(key=key, value=value, description=description)
            db.session.add(config)
        
        # Commit changes
        db.session.commit()
        print("Test data created successfully!")

if __name__ == '__main__':
    create_test_data()
EOF

echo "Created test data script at: $TEST_DATA"

# Create test runner
TEST_RUNNER="$TEST_DIR/run_tests.py"
cat > $TEST_RUNNER << EOF
import os
import sys
import unittest
from flask import Flask
from webapp import create_app, db

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'SECRET_KEY': 'test_secret_key',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///$TEST_DB',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'TESTING': True,
            'WTF_CSRF_ENABLED': False
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_home_page(self):
        """Test that the home page loads"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SCADA RFP Finder', response.data)
    
    def test_login_page(self):
        """Test that the login page loads"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Log In', response.data)
    
    def test_register_page(self):
        """Test that the register page loads"""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)
    
    def test_about_page(self):
        """Test that the about page loads"""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About', response.data)
    
    def test_registration(self):
        """Test user registration"""
        response = self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'password_confirm': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
    
    def test_login(self):
        """Test user login"""
        # First register a user
        self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'password_confirm': 'testpassword'
        })
        
        # Then try to log in
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword',
            'remember_me': False
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
    
    def test_logout(self):
        """Test user logout"""
        # First register and log in
        self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'password_confirm': 'testpassword'
        })
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword',
            'remember_me': False
        })
        
        # Then log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)
    
    def test_protected_page(self):
        """Test that protected pages require login"""
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in to access this page', response.data)

if __name__ == '__main__':
    unittest.main()
EOF

echo "Created test runner at: $TEST_RUNNER"

echo
echo "Step 1: Installing required packages"
echo "-----------------------------------"
pip3 install flask-testing

echo
echo "Step 2: Creating test database and data"
echo "-------------------------------------"
python3 $TEST_DATA

echo
echo "Step 3: Running unit tests"
echo "------------------------"
python3 $TEST_RUNNER

echo
echo "Step 4: Starting test server"
echo "-------------------------"
echo "To start the test server, run:"
echo "python3 $TEST_APP"
echo
echo "Then access the application at: http://localhost:5000"
echo
echo "Test credentials:"
echo "Admin: admin@example.com / adminpassword"
echo "User: user@example.com / userpassword"
echo
echo "Test completed!"
echo "Results are in: $TEST_DIR"
