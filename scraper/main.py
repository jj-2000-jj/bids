"""
RFP Scraper Framework - Main Module

This is the main module for the RFP scraper framework that coordinates the scraping
of procurement websites across multiple states to find SCADA-related RFPs.
"""

import os
import sys
import logging
import sqlite3
import datetime
import argparse
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rfp_scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("rfp_scraper")

class RFPScraperFramework:
    """Main framework class for coordinating RFP scraping across multiple states."""
    
    def __init__(self, db_path, output_dir):
        """
        Initialize the RFP scraper framework.
        
        Args:
            db_path (str): Path to the SQLite database file
            output_dir (str): Directory to store downloaded RFP documents
        """
        self.db_path = db_path
        self.output_dir = output_dir
        self.conn = None
        self.scrapers = {}
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"RFP Scraper Framework initialized with database at {db_path}")
        logger.info(f"RFP documents will be stored in {output_dir}")
    
    def _init_database(self):
        """Initialize the SQLite database with the required schema."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
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
            
            # Create index on state for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rfps_state ON RFPs(state)')
            
            # Create index on scada_relevance_score for faster filtering
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rfps_relevance ON RFPs(scada_relevance_score)')
            
            self.conn.commit()
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def register_scraper(self, state, scraper_class):
        """
        Register a state-specific scraper.
        
        Args:
            state (str): State abbreviation (e.g., 'AZ', 'NM')
            scraper_class (class): Scraper class for the state
        """
        self.scrapers[state] = scraper_class
        logger.info(f"Registered scraper for {state}")
    
    def run_scraper(self, state):
        """
        Run the scraper for a specific state.
        
        Args:
            state (str): State abbreviation to run the scraper for
            
        Returns:
            int: Number of new RFPs found
        """
        if state not in self.scrapers:
            logger.error(f"No scraper registered for state {state}")
            return 0
        
        logger.info(f"Running scraper for {state}")
        
        try:
            # Instantiate the scraper
            scraper = self.scrapers[state](self.conn, self.output_dir)
            
            # Run the scraper
            new_rfps = scraper.scrape()
            
            logger.info(f"Scraper for {state} found {new_rfps} new RFPs")
            return new_rfps
            
        except Exception as e:
            logger.error(f"Error running scraper for {state}: {e}")
            return 0
    
    def run_all_scrapers(self):
        """
        Run scrapers for all registered states.
        
        Returns:
            dict: Dictionary with state as key and number of new RFPs as value
        """
        results = {}
        
        for state in self.scrapers:
            results[state] = self.run_scraper(state)
        
        return results
    
    def filter_rfps_by_relevance(self, min_score=50):
        """
        Filter RFPs by SCADA relevance score.
        
        Args:
            min_score (int): Minimum relevance score (0-100)
            
        Returns:
            list: List of RFP dictionaries that meet the minimum score
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT * FROM RFPs 
        WHERE scada_relevance_score >= ? 
        ORDER BY scada_relevance_score DESC, due_date ASC
        ''', (min_score,))
        
        columns = [col[0] for col in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def close(self):
        """Close database connection and perform cleanup."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """Main entry point for the RFP scraper framework."""
    parser = argparse.ArgumentParser(description='RFP Scraper Framework')
    parser.add_argument('--state', help='State to scrape (e.g., AZ, NM)')
    parser.add_argument('--all', action='store_true', help='Scrape all states')
    parser.add_argument('--db', default='rfps.db', help='Path to SQLite database')
    parser.add_argument('--output', default='rfp_documents', help='Directory to store RFP documents')
    
    args = parser.parse_args()
    
    # Create framework instance
    framework = RFPScraperFramework(args.db, args.output)
    
    try:
        # Import state-specific scrapers
        from scrapers.arizona import ArizonaScraper
        from scrapers.new_mexico import NewMexicoScraper
        
        # Register scrapers
        framework.register_scraper('AZ', ArizonaScraper)
        framework.register_scraper('NM', NewMexicoScraper)
        
        # Run scrapers based on command line arguments
        if args.all:
            results = framework.run_all_scrapers()
            for state, count in results.items():
                print(f"{state}: {count} new RFPs")
        elif args.state:
            count = framework.run_scraper(args.state)
            print(f"{args.state}: {count} new RFPs")
        else:
            parser.print_help()
    
    finally:
        # Clean up
        framework.close()

if __name__ == "__main__":
    main()
