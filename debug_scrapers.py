"""
Debug script for SCADA RFP Finder scrapers
This script helps identify issues with the scraping process
"""

import os
import sys
import logging
import time
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("scraper_debug")

def debug_scrapers():
    """Run scrapers in debug mode with detailed logging"""
    logger.info("Starting scraper debugging process")
    
    # Add the project directory to the path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # Import required modules
    try:
        from webapp import create_app, db
        from webapp.scrapers.main import run_all_scrapers
        from webapp.scrapers.municipality_factory import MunicipalityScraperFactory
        logger.info("Successfully imported required modules")
    except Exception as e:
        logger.error(f"Failed to import required modules: {str(e)}")
        return
    
    # Check for CSV file
    csv_paths = [
        os.path.join(project_dir, "upload", "website-info-modified copy.csv"),
        os.path.join(project_dir, "website-info-modified copy.csv"),
        os.path.join(os.path.dirname(project_dir), "upload", "website-info-modified copy.csv")
    ]
    
    csv_found = False
    for path in csv_paths:
        if os.path.exists(path):
            logger.info(f"Found CSV file at: {path}")
            csv_found = True
            break
    
    if not csv_found:
        logger.error("CSV file not found. Please ensure the file exists in one of these locations:")
        for path in csv_paths:
            logger.error(f"- {path}")
        return
    
    # Check municipality factory
    try:
        factory = MunicipalityScraperFactory()
        municipalities = factory.get_municipalities()
        logger.info(f"Municipality factory loaded {len(municipalities)} municipalities")
        
        # Show sample of municipalities
        logger.info("Sample municipalities:")
        for i, muni in enumerate(municipalities[:5]):
            logger.info(f"  {i+1}. {muni.name}, {muni.state} - URL: {muni.url}")
    except Exception as e:
        logger.error(f"Error loading municipalities: {str(e)}")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Test a single municipality scraper
        logger.info("Testing a single municipality scraper...")
        try:
            from webapp.scrapers.municipality_base import MunicipalityScraper
            
            if municipalities:
                test_muni = municipalities[0]
                logger.info(f"Testing scraper for {test_muni.name}, {test_muni.state}")
                
                scraper = MunicipalityScraper(test_muni)
                start_time = time.time()
                rfps = scraper.scrape()
                end_time = time.time()
                
                logger.info(f"Scraper completed in {end_time - start_time:.2f} seconds")
                logger.info(f"Found {len(rfps)} potential RFPs")
                
                for i, rfp in enumerate(rfps[:3]):
                    logger.info(f"  RFP {i+1}: {rfp.get('title', 'No Title')} - {rfp.get('url', 'No URL')}")
            else:
                logger.error("No municipalities available for testing")
        except Exception as e:
            logger.error(f"Error testing municipality scraper: {str(e)}")
        
        # Test Utah Bonfirehub scraper
        logger.info("Testing Utah Bonfirehub scraper...")
        try:
            from webapp.scrapers.utah_bonfirehub import UtahBonfireHubScraper
            
            scraper = UtahBonfireHubScraper()
            start_time = time.time()
            rfps = scraper.scrape()
            end_time = time.time()
            
            logger.info(f"Utah Bonfirehub scraper completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Found {len(rfps)} potential RFPs")
            
            # Test specific opportunity
            logger.info("Testing specific Utah Bonfirehub opportunity (176637)...")
            from webapp.scrapers.utah_bonfirehub import process_opportunity
            import requests
            
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            start_time = time.time()
            result = process_opportunity(session, "176637", headers)
            end_time = time.time()
            
            logger.info(f"Process opportunity completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Result: {result}")
            
        except Exception as e:
            logger.error(f"Error testing Utah Bonfirehub scraper: {str(e)}")
        
        # Test SAM.gov scraper
        logger.info("Testing SAM.gov scraper...")
        try:
            from webapp.scrapers.sam_gov import SamGovScraper
            
            scraper = SamGovScraper()
            start_time = time.time()
            rfps = scraper.scrape()
            end_time = time.time()
            
            logger.info(f"SAM.gov scraper completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Found {len(rfps)} potential RFPs")
        except Exception as e:
            logger.error(f"Error testing SAM.gov scraper: {str(e)}")
        
        # Run all scrapers with increased municipality limit
        logger.info("Running all scrapers with increased municipality limit (20)...")
        try:
            start_time = time.time()
            results = run_all_scrapers(max_municipalities=20)
            end_time = time.time()
            
            logger.info(f"All scrapers completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Results: {results}")
        except Exception as e:
            logger.error(f"Error running all scrapers: {str(e)}")
    
    logger.info("Scraper debugging completed")

if __name__ == "__main__":
    debug_scrapers()
