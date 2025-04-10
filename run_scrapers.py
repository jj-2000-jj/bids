"""
Run Scrapers Script

This script runs all scrapers to find SCADA-related RFPs.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp import create_app, db
from webapp.scrapers.main import run_all_scrapers, get_rfp_stats

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run all scrapers and print results."""
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Print starting message
        logger.info("Starting SCADA RFP scrapers...")
        start_time = datetime.now()
        
        # Run all scrapers
        results = run_all_scrapers(max_municipalities=100)
        
        # Print results
        logger.info(f"Scraping completed in {datetime.now() - start_time}")
        logger.info(f"Total RFPs found: {results['total']}")
        logger.info(f"SAM.gov: {results['sam_gov']}")
        logger.info(f"Utah Bonfirehub: {results['utah_bonfirehub']}")
        logger.info(f"Municipalities: {results['municipalities']}")
        
        # Get and print stats
        stats = get_rfp_stats()
        logger.info(f"Total RFPs in database: {stats['total']}")
        logger.info(f"By state: {stats['by_state']}")
        logger.info(f"By industry: {stats['by_industry']}")
        logger.info(f"By relevance: {stats['by_relevance']}")

if __name__ == "__main__":
    main()
