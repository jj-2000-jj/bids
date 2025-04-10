"""
SCADA RFP Finder - Command Line Interface

This module provides a command-line interface for the SCADA RFP Finder application.
"""

import os
import sys
import logging
import argparse
import sqlite3
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.main import RFPScraperFramework
from scraper.scrapers import ArizonaScraper, NewMexicoScraper
from scraper.keyword_filter import KeywordFilter
from scraper.notification import NotificationSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scada_rfp_finder.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("scada_rfp_finder")

def setup_database(db_path):
    """
    Set up the SQLite database.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create RFPs table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS RFPs (
        id TEXT PRIMARY KEY,
        state TEXT,
        title TEXT,
        description TEXT,
        publication_date DATE,
        due_date DATE,
        category TEXT,
        agency TEXT,
        contact_name TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        url TEXT,
        document_urls TEXT,
        scada_relevance_score INTEGER,
        is_water_wastewater BOOLEAN,
        is_mining BOOLEAN,
        is_oil_gas BOOLEAN,
        processed BOOLEAN,
        notified BOOLEAN,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rfps_state ON RFPs(state)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rfps_relevance ON RFPs(scada_relevance_score)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rfps_notified ON RFPs(notified)')
    
    conn.commit()
    return conn

def run_scraper(args):
    """
    Run the RFP scraper.
    
    Args:
        args: Command-line arguments
    """
    # Set up database
    conn = setup_database(args.db)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Create scraper framework
    framework = RFPScraperFramework(args.db, args.output)
    
    # Register scrapers
    framework.register_scraper('AZ', ArizonaScraper)
    framework.register_scraper('NM', NewMexicoScraper)
    
    try:
        # Run scrapers
        if args.state:
            logger.info(f"Running scraper for {args.state}")
            count = framework.run_scraper(args.state)
            print(f"Found {count} new RFPs for {args.state}")
        else:
            logger.info("Running scrapers for all states")
            results = framework.run_all_scrapers()
            total = sum(results.values())
            print(f"Found {total} new RFPs across all states")
            for state, count in results.items():
                print(f"  {state}: {count} new RFPs")
    
    finally:
        # Clean up
        framework.close()
        conn.close()

def filter_rfps(args):
    """
    Filter RFPs by relevance score.
    
    Args:
        args: Command-line arguments
    """
    # Set up database
    conn = setup_database(args.db)
    
    try:
        # Create keyword filter
        keyword_filter = KeywordFilter(args.keywords)
        
        # Query database for unprocessed RFPs
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description FROM RFPs WHERE processed = 0")
        unprocessed = cursor.fetchall()
        
        if not unprocessed:
            print("No unprocessed RFPs found")
            return
        
        print(f"Processing {len(unprocessed)} RFPs")
        
        # Process each RFP
        for rfp_id, title, description in unprocessed:
            # Combine title and description for analysis
            text = f"{title} {description}"
            
            # Calculate relevance
            score, is_water, is_mining, is_oil_gas = keyword_filter.calculate_relevance(text)
            
            # Update database
            cursor.execute('''
            UPDATE RFPs SET 
                scada_relevance_score = ?,
                is_water_wastewater = ?,
                is_mining = ?,
                is_oil_gas = ?,
                processed = 1,
                updated_at = ?
            WHERE id = ?
            ''', (score, is_water, is_mining, is_oil_gas, datetime.now().isoformat(), rfp_id))
        
        conn.commit()
        print(f"Processed {len(unprocessed)} RFPs")
        
        # Show high-relevance RFPs
        cursor.execute('''
        SELECT id, state, title, scada_relevance_score 
        FROM RFPs 
        WHERE processed = 1 AND scada_relevance_score >= ? 
        ORDER BY scada_relevance_score DESC
        ''', (args.min_score,))
        
        relevant = cursor.fetchall()
        
        if relevant:
            print(f"\nFound {len(relevant)} RFPs with relevance score >= {args.min_score}:")
            for rfp_id, state, title, score in relevant:
                print(f"  [{state}] {title} (Score: {score})")
        else:
            print(f"\nNo RFPs found with relevance score >= {args.min_score}")
    
    finally:
        conn.close()

def send_notifications(args):
    """
    Send notifications for new RFPs.
    
    Args:
        args: Command-line arguments
    """
    # Set up database
    conn = setup_database(args.db)
    
    try:
        # Load notification config
        config = {}
        if args.config:
            with open(args.config, 'r') as f:
                config = json.load(f)
        
        # Create notification system
        notification_system = NotificationSystem(conn, config)
        
        # Send notifications
        if args.email:
            print(f"Sending notifications to {args.email}")
            
            if args.digest:
                # Send daily digest
                result = notification_system.send_daily_digest(args.email)
                if result:
                    print("Daily digest sent successfully")
                else:
                    print("Failed to send daily digest")
            else:
                # Get new RFPs
                rfps = notification_system.get_new_rfps(args.min_score)
                
                if not rfps:
                    print("No new RFPs to notify about")
                    return
                
                # Send notification
                subject = f"SCADA RFP Finder - {len(rfps)} new RFPs found"
                result = notification_system.send_notification_email(args.email, subject, rfps)
                
                if result:
                    # Mark RFPs as notified
                    rfp_ids = [rfp['id'] for rfp in rfps]
                    notification_system.mark_rfps_as_notified(rfp_ids)
                    print(f"Notification sent successfully for {len(rfps)} RFPs")
                else:
                    print("Failed to send notification")
        else:
            print("No email address specified, use --email to send notifications")
    
    finally:
        conn.close()

def main():
    """Main entry point for the SCADA RFP Finder CLI."""
    parser = argparse.ArgumentParser(description='SCADA RFP Finder')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--db', default='rfps.db', help='Path to SQLite database')
    
    # Scraper command
    scraper_parser = subparsers.add_parser('scrape', parents=[common_parser], help='Run RFP scrapers')
    scraper_parser.add_argument('--state', help='State to scrape (e.g., AZ, NM)')
    scraper_parser.add_argument('--output', default='rfp_documents', help='Directory to store RFP documents')
    
    # Filter command
    filter_parser = subparsers.add_parser('filter', parents=[common_parser], help='Filter RFPs by relevance')
    filter_parser.add_argument('--keywords', help='Path to JSON file containing keywords')
    filter_parser.add_argument('--min-score', type=int, default=50, help='Minimum relevance score (0-100)')
    
    # Notify command
    notify_parser = subparsers.add_parser('notify', parents=[common_parser], help='Send notifications for new RFPs')
    notify_parser.add_argument('--email', help='Email address to send notifications to')
    notify_parser.add_argument('--config', help='Path to JSON file containing notification config')
    notify_parser.add_argument('--min-score', type=int, default=50, help='Minimum relevance score (0-100)')
    notify_parser.add_argument('--digest', action='store_true', help='Send daily digest')
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        run_scraper(args)
    elif args.command == 'filter':
        filter_rfps(args)
    elif args.command == 'notify':
        send_notifications(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
