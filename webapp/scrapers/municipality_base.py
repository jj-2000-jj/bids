"""
Municipality Base Scraper for SCADA RFPs

This module provides a base class for municipality scrapers.
"""

import requests
import logging
from datetime import datetime
import re
from bs4 import BeautifulSoup
import urllib.parse
import time
import random

from webapp import db
from webapp.models import RFP, ScraperLog
from webapp.scrapers.keyword_matcher import analyze_text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MunicipalityScraper:
    """Base class for municipality scrapers"""
    
    def __init__(self, state, name, website, procurement_url=None, rfp_url=None, bid_url=None):
        """
        Initialize the municipality scraper
        
        Args:
            state: State code (e.g., 'AZ')
            name: Municipality name
            website: Main website URL
            procurement_url: URL to procurement page (optional)
            rfp_url: URL to RFP page (optional)
            bid_url: URL to bid page (optional)
        """
        self.state = state
        self.name = name
        self.website = website
        self.procurement_url = procurement_url
        self.rfp_url = rfp_url
        self.bid_url = bid_url
        self.max_depth = 2  # Maximum depth for crawling
        self.visited_urls = set()  # Track visited URLs to avoid loops
        
        # Set up headers to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
        }
        
        # Initialize session
        self.session = requests.Session()
    
    def scrape(self):
        """
        Scrape the municipality website for SCADA-related RFPs
        
        Returns:
            Number of new SCADA-related RFPs found
        """
        rfps_found = 0
        start_time = datetime.utcnow()
        
        try:
            # Create scraper log entry
            scraper_log = ScraperLog(
                state=self.state,
                municipality=self.name,
                start_time=start_time,
                success=False,
                rfps_found=0
            )
            db.session.add(scraper_log)
            db.session.commit()
            
            # Determine which URLs to scrape
            urls_to_scrape = []
            
            if self.rfp_url:
                urls_to_scrape.append(('RFP', self.rfp_url))
            
            if self.bid_url and self.bid_url != self.rfp_url:
                urls_to_scrape.append(('Bid', self.bid_url))
            
            if self.procurement_url:
                urls_to_scrape.append(('Procurement', self.procurement_url))
            
            # If no specific URLs, try to find procurement page on main website
            if not urls_to_scrape:
                urls_to_scrape.append(('Main', self.website))
            
            # Scrape each URL
            for url_type, url in urls_to_scrape:
                try:
                    # Ensure URL is properly formatted
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    
                    # Reset visited URLs for each starting point
                    self.visited_urls = set()
                    
                    # Crawl the website starting from this URL
                    new_rfps = self._crawl_website(url, depth=0)
                    rfps_found += new_rfps
                    
                except Exception as e:
                    logger.error(f"Error scraping {url_type} URL for {self.name}: {str(e)}")
            
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
            logger.error(f"Error in municipality scraper for {self.name}: {str(e)}")
            
            # Update scraper log with error
            if 'scraper_log' in locals():
                scraper_log.end_time = datetime.utcnow()
                scraper_log.duration = (scraper_log.end_time - start_time).total_seconds()
                scraper_log.success = False
                scraper_log.error_message = str(e)
                db.session.commit()
            
            return rfps_found
    
    def _crawl_website(self, url, depth=0):
        """
        Crawl the website recursively to find RFPs
        
        Args:
            url: URL to crawl
            depth: Current depth of crawling
        
        Returns:
            Number of new SCADA-related RFPs found
        """
        # Check if we've reached the maximum depth or already visited this URL
        if depth > self.max_depth or url in self.visited_urls:
            return 0
        
        # Add URL to visited set
        self.visited_urls.add(url)
        
        # Add a small random delay to avoid overloading the server
        time.sleep(random.uniform(1.0, 3.0))
        
        rfps_found = 0
        
        try:
            # Get the page
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"Error accessing URL {url} for {self.name}: {response.status_code}")
                return 0
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find potential RFP links
            rfp_links = self._find_rfp_links(soup, url)
            
            # Process each potential RFP
            for link_text, link_url in rfp_links:
                try:
                    # Get the RFP page
                    absolute_url = urllib.parse.urljoin(url, link_url)
                    
                    # Skip if we've already visited this URL
                    if absolute_url in self.visited_urls:
                        continue
                    
                    # Add to visited URLs
                    self.visited_urls.add(absolute_url)
                    
                    # Add a small random delay
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    rfp_response = self.session.get(absolute_url, headers=self.headers, timeout=30)
                    
                    if rfp_response.status_code != 200:
                        continue
                    
                    # Parse the RFP page
                    rfp_soup = BeautifulSoup(rfp_response.text, 'html.parser')
                    
                    # Extract RFP details
                    title = link_text
                    description = self._extract_text(rfp_soup)
                    
                    # Extract dates if possible
                    publication_date = self._extract_date(rfp_soup, ['posted', 'published', 'issue', 'release'])
                    due_date = self._extract_date(rfp_soup, ['due', 'closing', 'deadline', 'submission'])
                    
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
                        rfp_id = f"{self.state}-{self.name.replace(' ', '')}-{hash(absolute_url) % 10000}"
                        
                        # Check if RFP already exists
                        existing_rfp = RFP.query.filter_by(id=rfp_id).first()
                        
                        if not existing_rfp:
                            # Create new RFP
                            rfp = RFP(
                                id=rfp_id,
                                title=title,
                                description=description[:1000],  # Limit description length
                                state=self.state,
                                agency=self.name,
                                publication_date=publication_date,
                                due_date=due_date,
                                url=absolute_url,
                                scada_relevance_score=relevance_score,
                                is_water_wastewater=is_water,
                                is_mining=is_mining,
                                is_oil_gas=is_oil_gas,
                                is_hvac=is_hvac,
                                created_at=datetime.utcnow()
                            )
                            
                            db.session.add(rfp)
                            rfps_found += 1
                            logger.info(f"Added new RFP from {self.name}: {title} (Score: {relevance_score})")
                
                except Exception as e:
                    logger.error(f"Error processing RFP link {link_url} for {self.name}: {str(e)}")
            
            # If we're not at max depth, find more links to crawl
            if depth < self.max_depth:
                # Find all links on the page
                all_links = []
                for link in soup.find_all('a', href=True):
                    link_url = link['href']
                    
                    # Skip empty links, javascript links, or external links
                    if not link_url or link_url.startswith(('javascript:', '#', 'mailto:', 'tel:')):
                        continue
                    
                    # Convert to absolute URL
                    absolute_url = urllib.parse.urljoin(url, link_url)
                    
                    # Only follow links to the same domain
                    if urllib.parse.urlparse(absolute_url).netloc == urllib.parse.urlparse(url).netloc:
                        all_links.append(absolute_url)
                
                # Prioritize links that might contain procurement information
                procurement_terms = ['bid', 'rfp', 'procurement', 'contract', 'solicitation', 'tender', 'proposal']
                priority_links = []
                other_links = []
                
                for link in all_links:
                    if any(term in link.lower() for term in procurement_terms):
                        priority_links.append(link)
                    else:
                        other_links.append(link)
                
                # Process priority links first, then others, up to a reasonable limit
                links_to_crawl = priority_links + other_links
                links_to_crawl = links_to_crawl[:10]  # Limit to 10 links per page
                
                # Crawl each link
                for link in links_to_crawl:
                    if link not in self.visited_urls:
                        rfps_found += self._crawl_website(link, depth + 1)
        
        except Exception as e:
            logger.error(f"Error crawling {url} for {self.name}: {str(e)}")
        
        return rfps_found
    
    def _find_rfp_links(self, soup, base_url):
        """
        Find potential RFP links in the page
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
        
        Returns:
            List of (link_text, link_url) tuples
        """
        rfp_links = []
        
        # Look for links containing RFP-related terms (expanded list)
        rfp_terms = [
            'rfp', 'request for proposal', 'bid', 'solicitation', 'procurement', 'tender',
            'contract', 'opportunity', 'project', 'proposal', 'quote', 'quotation',
            'vendor', 'supplier', 'contractor', 'service', 'purchase', 'acquisition',
            'bids', 'rfps', 'contracts', 'opportunities', 'projects', 'proposals',
            'quotes', 'quotations', 'vendors', 'suppliers', 'contractors', 'services',
            'purchases', 'acquisitions', 'bid opportunity', 'current bids', 'open bids',
            'current rfps', 'open rfps', 'current opportunities', 'open opportunities'
        ]
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().strip()
            link_url = link['href']
            
            # Skip empty links or javascript links
            if not link_url or link_url.startswith(('javascript:', '#', 'mailto:', 'tel:')):
                continue
            
            # Check if link text or URL contains RFP-related terms
            if any(term in link_text.lower() for term in rfp_terms) or any(term in link_url.lower() for term in rfp_terms):
                rfp_links.append((link_text, link_url))
            
            # Also look for links with certain patterns that might indicate RFPs
            elif re.search(r'\b\d{4}-\d{2,4}\b', link_text) or re.search(r'\b\d{4}-\d{2,4}\b', link_url):
                # Patterns like "2023-01" or "2023-0123" often used in RFP numbering
                rfp_links.append((link_text, link_url))
            elif re.search(r'\b(RFQ|ITB|RFI|IFB)\b', link_text, re.IGNORECASE) or re.search(r'\b(RFQ|ITB|RFI|IFB)\b', link_url, re.IGNORECASE):
                # Other procurement acronyms: Request for Quotation, Invitation to Bid, Request for Information, Invitation for Bid
                rfp_links.append((link_text, link_url))
        
        return rfp_links
    
    def _extract_text(self, soup):
        """
        Extract meaningful text from the page
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Extracted text
        """
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_date(self, soup, keywords):
        """
        Extract date from the page based on keywords
        
        Args:
            soup: BeautifulSoup object
            keywords: List of keywords to look for
        
        Returns:
            Extracted date or None
        """
        text = self._extract_text(soup)
        
        # Look for dates in various formats
        for keyword in keywords:
            # Look for "Keyword: MM/DD/YYYY" format
            pattern = rf"{keyword}[:\s]+(\d{{1,2}}/\d{{1,2}}/\d{{4}})"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return datetime.strptime(match.group(1), '%m/%d/%Y').date()
                except ValueError:
                    pass
            
            # Look for "Keyword: Month DD, YYYY" format
            pattern = rf"{keyword}[:\s]+([A-Za-z]+ \d{{1,2}}, \d{{4}})"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return datetime.strptime(match.group(1), '%B %d, %Y').date()
                except ValueError:
                    pass
            
            # Look for "Keyword: YYYY-MM-DD" format
            pattern = rf"{keyword}[:\s]+(\d{{4}}-\d{{1,2}}-\d{{1,2}})"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return datetime.strptime(match.group(1), '%Y-%m-%d').date()
                except ValueError:
                    pass
        
        return None
