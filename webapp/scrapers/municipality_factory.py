"""
Municipality Factory for SCADA RFPs

This module provides functions to create and run municipality scrapers based on the provided CSV file.
"""

import csv
import logging
import os
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup

from webapp import db
from webapp.models import RFP, ScraperLog
from webapp.scrapers.municipality_base import MunicipalityScraper
from webapp.scrapers.keyword_matcher import analyze_text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the CSV file path - simplified to look in the current directory
def get_csv_file_path():
    """Find the CSV file in the current directory"""
    # Get the current file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for muni-sites.csv in the current directory
    muni_sites_path = os.path.join(current_dir, 'muni-sites.csv')
    
    if os.path.exists(muni_sites_path):
        logger.info(f"Found CSV file at: {muni_sites_path}")
        return muni_sites_path
    
    # If not found, log a clear error message
    logger.error(f"CSV file not found at: {muni_sites_path}")
    logger.error(f"Please ensure muni-sites.csv is in the same directory as municipality_factory.py")
    
    # Return the path anyway so the error is consistent
    return muni_sites_path

class MunicipalityScraperFactory:
    """Factory class to create and manage municipality scrapers"""
    
    def __init__(self, csv_file_path=None):
        self.csv_file_path = csv_file_path or get_csv_file_path()
        self.municipalities = []
        self.load_municipalities()
    
    def load_municipalities(self):
        """Load municipalities from the CSV file"""
        if not os.path.exists(self.csv_file_path):
            logger.error(f"CSV file not found: {self.csv_file_path}")
            return
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Check if the row has the required fields
                    if 'State' in row and 'Name' in row and 'Website' in row:
                        # Map CSV columns to expected fields
                        municipality = row.get('Name', '').strip()
                        state = row.get('State', '').strip()
                        website = row.get('Website', '').strip()
                        rfp_page = row.get('RFP Page', '').strip() or None
                        
                        # Skip rows with missing essential data
                        if not municipality or not state or not website:
                            continue
                            
                        # Convert state names to state codes if needed
                        state_code = self._get_state_code(state)
                        
                        self.municipalities.append({
                            'state': state_code,
                            'municipality': municipality,
                            'website': website,
                            'procurement_url': None,  # Not in CSV
                            'rfp_url': rfp_page,
                            'bid_url': rfp_page  # Use RFP Page as Bid URL too
                        })
            
            logger.info(f"Loaded {len(self.municipalities)} municipalities from CSV file")
        except Exception as e:
            logger.error(f"Error loading municipalities from CSV: {str(e)}")
    
    def _get_state_code(self, state_name):
        """Convert state name to state code if needed"""
        state_map = {
            'Arizona': 'AZ',
            'New Mexico': 'NM',
            'Utah': 'UT',
            'Idaho': 'ID',
            'Illinois': 'IL',
            'Missouri': 'MO',
            'Iowa': 'IA',
            'Indiana': 'IN',
            'Nevada': 'NV'  # Additional state in CSV
        }
        
        # If it's already a code, return it
        if len(state_name) <= 2:
            return state_name.upper()
            
        # Otherwise, try to map it
        return state_map.get(state_name, state_name)
    
    def get_municipalities_by_states(self, states):
        """
        Get municipalities filtered by states
        
        Args:
            states: List of state codes to filter by
        
        Returns:
            List of municipalities in the specified states
        """
        return [m for m in self.municipalities if m['state'] in states]
    
    def create_scraper(self, municipality_data):
        """
        Create a scraper for the specified municipality
        
        Args:
            municipality_data: Dictionary with municipality information
        
        Returns:
            MunicipalityScraper instance
        """
        return MunicipalityScraper(
            state=municipality_data['state'],
            name=municipality_data['municipality'],
            website=municipality_data['website'],
            procurement_url=municipality_data['procurement_url'],
            rfp_url=municipality_data['rfp_url'],
            bid_url=municipality_data['bid_url']
        )

def run_municipality_scrapers(states=None, max_municipalities=100):
    """
    Run scrapers for municipalities in the specified states
    
    Args:
        states: List of state codes to filter by (default: None, uses all target states)
        max_municipalities: Maximum number of municipalities to scrape (default: 100)
    
    Returns:
        Number of new SCADA-related RFPs found
    """
    if states is None:
        states = ['AZ', 'NM', 'UT', 'ID', 'IL', 'MO', 'IA', 'IN']
    
    rfps_found = 0
    start_time = datetime.utcnow()
    
    try:
        # Create scraper log entry
        scraper_log = ScraperLog(
            state="ALL",
            municipality="Municipalities",
            start_time=start_time,
            success=False,
            rfps_found=0
        )
        db.session.add(scraper_log)
        db.session.commit()
        
        # Create factory and get municipalities
        factory = MunicipalityScraperFactory()
        municipalities = factory.get_municipalities_by_states(states)
        
        logger.info(f"Found {len(factory.municipalities)} municipalities in CSV file")
        logger.info(f"Filtered to {len(municipalities)} municipalities in states {states}")
        
        # Limit the number of municipalities to scrape
        municipalities = municipalities[:max_municipalities]
        
        # Run scrapers for each municipality
        for i, municipality_data in enumerate(municipalities):
            try:
                logger.info(f"Scraping municipality {i+1}/{len(municipalities)}: {municipality_data['municipality']}, {municipality_data['state']}")
                scraper = factory.create_scraper(municipality_data)
                new_rfps = scraper.scrape()
                rfps_found += new_rfps
                
                # Pause between municipalities to avoid overloading servers
                if i < len(municipalities) - 1:
                    time.sleep(2)  # Increased pause to reduce server load
            
            except Exception as e:
                logger.error(f"Error scraping municipality {municipality_data['municipality']}: {str(e)}")
        
        logger.info(f"Ran {len(municipalities)} municipality scrapers, found {rfps_found} new SCADA-related RFPs")
        
        # Update scraper log
        scraper_log.end_time = datetime.utcnow()
        scraper_log.duration = (scraper_log.end_time - start_time).total_seconds()
        scraper_log.success = True
        scraper_log.rfps_found = rfps_found
        db.session.commit()
        
        return rfps_found
        
    except Exception as e:
        logger.error(f"Error in municipality scrapers: {str(e)}")
        
        # Update scraper log with error
        if 'scraper_log' in locals():
            scraper_log.end_time = datetime.utcnow()
            scraper_log.duration = (scraper_log.end_time - start_time).total_seconds()
            scraper_log.success = False
            scraper_log.error_message = str(e)
            db.session.commit()
        
        return rfps_found
