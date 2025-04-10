#!/bin/bash
# Test script for SCADA RFP Finder

echo "SCADA RFP Finder - Test Script"
echo "============================="
echo

# Create test directory
TEST_DIR="test_run_$(date +%Y%m%d_%H%M%S)"
mkdir -p $TEST_DIR
echo "Created test directory: $TEST_DIR"

# Create test database
TEST_DB="$TEST_DIR/test_rfps.db"
echo "Using test database: $TEST_DB"

# Create test output directory
TEST_OUTPUT="$TEST_DIR/rfp_documents"
mkdir -p $TEST_OUTPUT
echo "Created test output directory: $TEST_OUTPUT"

echo
echo "Step 1: Testing Arizona scraper"
echo "------------------------------"
python3 cli.py scrape --state AZ --db $TEST_DB --output $TEST_OUTPUT

echo
echo "Step 2: Testing New Mexico scraper"
echo "--------------------------------"
python3 cli.py scrape --state NM --db $TEST_DB --output $TEST_OUTPUT

echo
echo "Step 3: Testing keyword filtering"
echo "------------------------------"
python3 cli.py filter --db $TEST_DB --min-score 30

echo
echo "Step 4: Testing notification system (dry run)"
echo "-----------------------------------------"
echo "This will not actually send emails but will show what would be sent"
python3 cli.py notify --db $TEST_DB --email test@example.com --min-score 30

echo
echo "Test completed successfully!"
echo "Results are in: $TEST_DIR"
echo
echo "To view the database contents, run:"
echo "sqlite3 $TEST_DB 'SELECT id, state, title, scada_relevance_score FROM RFPs ORDER BY scada_relevance_score DESC;'"
