"""
SAM.gov Scraper for SCADA RFPs - Web Scraping Version

This module provides functions to scrape SAM.gov for SCADA-related RFPs using web scraping
instead of API access to overcome 405 Method Not Allowed errors.
"""

import requests
import logging
from datetime import datetime
import time
import json
import re
from bs4 import BeautifulSoup
import random
import urllib.parse

from webapp import db
from webapp.models import RFP, ScraperLog
from webapp.scrapers.keyword_matcher import analyze_text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SAMGovScraper:
    """Scraper for SAM.gov using web scraping approach"""
    
    def __init__(self):
        """Initialize the SAM.gov scraper"""
        # Set up headers to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Chromium";v="122", "Google Chrome";v="122", "Not(A:Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        
        # Initialize session
        self.session = requests.Session()
        
        # Base URL for SAM.gov
        self.base_url = "https://sam.gov"
        self.search_url = "https://sam.gov/search/results"
        
        # Keywords to search for
        self.keywords = [
            "scada", 
            "plc", 
            "hmi", 
            "rtu", 
            "dcs", 
            "automation", 
            "control system",
            "water scada",
            "wastewater scada",
            "supervisory control",
            "remote monitoring",
            "building automation",
            "hvac control"
        ]
    
    def scrape(self):
        """
        Scrape SAM.gov for SCADA-related RFPs
        
        Returns:
            Number of new SCADA-related RFPs found
        """
        rfps_found = 0
        start_time = datetime.utcnow()
        
        try:
            # Create scraper log entry
            scraper_log = ScraperLog(
                state="US",
                municipality="SAM.gov",
                start_time=start_time,
                success=False,
                rfps_found=0
            )
            db.session.add(scraper_log)
            db.session.commit()
            
            # Search for each keyword
            for keyword in self.keywords:
                try:
                    logger.info(f"Searching SAM.gov with keyword: {keyword}")
                    
                    # Search for opportunities
                    opportunities = self._search_opportunities(keyword)
                    
                    if not opportunities:
                        logger.info(f"No opportunities found for keyword: {keyword}")
                        continue
                    
                    logger.info(f"Found {len(opportunities)} opportunities for keyword: {keyword}")
                    
                    # Process each opportunity
                    for opportunity in opportunities:
                        try:
                            # Extract opportunity details
                            title = opportunity.get('title', '')
                            description = opportunity.get('description', '')
                            notice_id = opportunity.get('notice_id', '')
                            
                            if not title or not notice_id:
                                continue
                            
                            # Get the opportunity URL
                            opportunity_url = f"{self.base_url}/opportunity/view?opp={notice_id}"
                            
                            # Check if SCADA-related
                            analysis = analyze_text(title, description)
                            is_related = analysis['is_scada_related']
                            relevance_score = analysis['relevance_score']
                            is_water = analysis['is_water_wastewater']
                            is_mining = analysis['is_mining']
                            is_oil_gas = analysis['is_oil_gas']
                            is_hvac = analysis['is_hvac']
                            
                            if is_related:
                                # Generate unique ID
                                rfp_id = f"US-SAM-{notice_id}"
                                
                                # Check if RFP already exists
                                existing_rfp = RFP.query.filter_by(id=rfp_id).first()
                                
                                if not existing_rfp:
                                    # Create new RFP
                                    rfp = RFP(
                                        id=rfp_id,
                                        title=title,
                                        description=description[:1000],  # Limit description length
                                        state="US",
                                        agency=opportunity.get('agency', 'Federal Government'),
                                        publication_date=self._parse_date(opportunity.get('posted_date')),
                                        due_date=self._parse_date(opportunity.get('due_date')),
                                        url=opportunity_url,
                                        scada_relevance_score=relevance_score,
                                        is_water_wastewater=is_water,
                                        is_mining=is_mining,
                                        is_oil_gas=is_oil_gas,
                                        is_hvac=is_hvac,
                                        created_at=datetime.utcnow()
                                    )
                                    
                                    db.session.add(rfp)
                                    rfps_found += 1
                                    logger.info(f"Added new RFP from SAM.gov: {title}")
                        
                        except Exception as e:
                            logger.error(f"Error processing opportunity: {str(e)}")
                    
                    # Add a delay between keyword searches
                    time.sleep(random.uniform(2.0, 4.0))
                    
                except Exception as e:
                    logger.error(f"Error searching SAM.gov with keyword {keyword}: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            
            # Update scraper log
            scraper_log.end_time = datetime.utcnow()
            scraper_log.duration = (scraper_log.end_time - start_time).total_seconds()
            scraper_log.success = True
            scraper_log.rfps_found = rfps_found
            db.session.commit()
            
            return rfps_found
            
        except Exception as e:
            logger.error(f"Error in SAM.gov scraper: {str(e)}")
            
            # Update scraper log with error
            if 'scraper_log' in locals():
                scraper_log.end_time = datetime.utcnow()
                scraper_log.duration = (scraper_log.end_time - start_time).total_seconds()
                scraper_log.success = False
                scraper_log.error_message = str(e)
                db.session.commit()
            
            return rfps_found
    
    def _search_opportunities(self, keyword):
        """
        Search for opportunities on SAM.gov
        
        Args:
            keyword: Keyword to search for
        
        Returns:
            List of opportunities
        """
        # Construct the search URL with keyword
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"{self.search_url}?keywords={encoded_keyword}&index=opp&is_active=true&sort=-relevance&page=1&size=25"
        
        try:
            # Make request with multiple retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Add a delay between retries
                    if attempt > 0:
                        time.sleep(random.uniform(3.0, 5.0))
                    
                    # Make request
                    response = self.session.get(
                        url,
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        break
                    
                    logger.warning(f"Error accessing SAM.gov search: {response.status_code} (Attempt {attempt+1}/{max_retries})")
                
                except Exception as e:
                    logger.warning(f"Error accessing SAM.gov search: {str(e)} (Attempt {attempt+1}/{max_retries})")
            
            if response.status_code != 200:
                logger.error(f"Error accessing SAM.gov search: {response.status_code}")
                return []
            
            # Parse HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract opportunities from the page
            opportunities = []
            
            # Look for opportunity cards or results
            opportunity_elements = soup.select('.opportunity-result, .search-result, .result-item')
            
            if not opportunity_elements:
                # Try alternative selectors if the expected ones aren't found
                opportunity_elements = soup.select('div[class*="opportunity"], div[class*="result"]')
            
            if not opportunity_elements:
                logger.info(f"No opportunity elements found for keyword: {keyword}")
                
                # Try to extract any links that might be opportunities
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if '/opportunity/' in href or '/opp/' in href:
                        # Extract notice ID from the URL
                        match = re.search(r'opp(?:ortunity)?[=/]([^&?/]+)', href)
                        if match:
                            notice_id = match.group(1)
                            title = link.get_text().strip()
                            if title and notice_id:
                                opportunities.append({
                                    'title': title,
                                    'description': '',
                                    'notice_id': notice_id,
                                    'agency': 'Federal Government',
                                    'posted_date': '',
                                    'due_date': ''
                                })
                
                return opportunities
            
            # Process each opportunity element
            for element in opportunity_elements:
                try:
                    # Extract title and notice ID
                    title = ''
                    notice_id = ''
                    
                    # Try to find title and link
                    title_elem = element.select_one('h3, .title, [class*="title"]')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        
                        # Try to find link with notice ID
                        link = title_elem.find('a', href=True) or element.find('a', href=True)
                        if link:
                            href = link['href']
                            match = re.search(r'opp(?:ortunity)?[=/]([^&?/]+)', href)
                            if match:
                                notice_id = match.group(1)
                    
                    # If we couldn't find the notice ID, try to extract it from any link
                    if not notice_id:
                        links = element.find_all('a', href=True)
                        for link in links:
                            href = link['href']
                            match = re.search(r'opp(?:ortunity)?[=/]([^&?/]+)', href)
                            if match:
                                notice_id = match.group(1)
                                break
                    
                    # Extract description
                    description = ''
                    description_elem = element.select_one('.description, [class*="description"], p')
                    if description_elem:
                        description = description_elem.get_text().strip()
                    
                    # Extract agency
                    agency = 'Federal Government'
                    agency_elem = element.select_one('.agency, [class*="agency"], [class*="organization"]')
                    if agency_elem:
                        agency = agency_elem.get_text().strip()
                    
                    # Extract dates
                    posted_date = ''
                    due_date = ''
                    
                    date_elements = element.select('[class*="date"]')
                    for date_elem in date_elements:
                        text = date_elem.get_text().strip().lower()
                        if 'post' in text or 'publish' in text:
                            # Extract date part
                            date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2}, \d{4}', text)
                            if date_match:
                                posted_date = date_match.group(0)
                        elif 'due' in text or 'close' in text or 'end' in text:
                            # Extract date part
                            date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2}, \d{4}', text)
                            if date_match:
                                due_date = date_match.group(0)
                    
                    # Add opportunity to list if we have at least a title and notice ID
                    if title and notice_id:
                        opportunities.append({
                            'title': title,
                            'description': description,
                            'notice_id': notice_id,
                            'agency': agency,
                            'posted_date': posted_date,
                            'due_date': due_date
                        })
                
                except Exception as e:
                    logger.error(f"Error extracting opportunity details: {str(e)}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error searching SAM.gov with keyword {keyword}: {str(e)}")
            return []
    
    def _parse_date(self, date_str):
        """
        Parse date string to datetime object
        
        Args:
            date_str: Date string
        
        Returns:
            Datetime object or None
        """
        if not date_str:
            return None
        
        try:
            # Try various date formats
            formats = [
                '%m/%d/%Y',  # MM/DD/YYYY
                '%B %d, %Y',  # Month DD, YYYY
                '%Y-%m-%d',   # YYYY-MM-DD
                '%d %b %Y',   # DD Mon YYYY
                '%d-%b-%Y',   # DD-Mon-YYYY
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {str(e)}")
        
        return None

def run_sam_gov_scraper():
    """
    Run the SAM.gov scraper
    
    Returns:
        Number of new SCADA-related RFPs found
    """
    scraper = SAMGovScraper()
    return scraper.scrape()
