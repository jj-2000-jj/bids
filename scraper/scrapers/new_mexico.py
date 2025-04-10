"""
New Mexico Scraper - Implementation of RFP scraper for New Mexico

This module implements the scraper for New Mexico's procurement websites.
"""

import re
import logging
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..base_scraper import BaseScraper

logger = logging.getLogger("rfp_scraper.new_mexico")

class NewMexicoScraper(BaseScraper):
    """Scraper for New Mexico's procurement websites."""
    
    @property
    def state_code(self):
        return "NM"
    
    @property
    def state_name(self):
        return "New Mexico"
    
    @property
    def base_url(self):
        return "https://www.generalservices.state.nm.us/state-purchasing/active-itbs-and-rfps/active-procurements/"
    
    def scrape(self):
        """
        Scrape New Mexico's procurement websites for RFPs.
        
        Returns:
            int: Number of new RFPs found
        """
        logger.info(f"Starting scrape of {self.state_name} procurement websites")
        
        new_rfps = 0
        
        # New Mexico has multiple procurement sources, so we'll scrape each one
        sources = [
            {
                'url': self.base_url,
                'parser': self._parse_gsd_page
            },
            {
                'url': "https://biz.nm.gov/procurement-opportunities/",
                'parser': self._parse_biz_nm_page
            },
            {
                'url': "https://www.dot.nm.gov/business-support/procurement-services/request-for-proposals-rfp/",
                'parser': self._parse_dot_page
            }
        ]
        
        for source in sources:
            try:
                logger.info(f"Scraping {source['url']}")
                
                # Get the page
                response = self.session.get(source['url'])
                response.raise_for_status()
                
                # Parse the page using the appropriate parser
                rfps = source['parser'](response.text, source['url'])
                
                # Process each RFP
                for rfp_data in rfps:
                    # Calculate SCADA relevance
                    title = rfp_data.get('title', '')
                    description = rfp_data.get('description', '')
                    relevance_score, is_water, is_mining, is_oil_gas = self.calculate_scada_relevance(title, description)
                    
                    rfp_data['scada_relevance_score'] = relevance_score
                    rfp_data['is_water_wastewater'] = is_water
                    rfp_data['is_mining'] = is_mining
                    rfp_data['is_oil_gas'] = is_oil_gas
                    rfp_data['processed'] = True
                    rfp_data['notified'] = False
                    
                    # Save to database
                    if self.save_rfp(rfp_data):
                        new_rfps += 1
                
            except Exception as e:
                logger.error(f"Error scraping {source['url']}: {e}")
                continue
        
        logger.info(f"Completed scrape of {self.state_name}, found {new_rfps} new RFPs")
        return new_rfps
    
    def _parse_gsd_page(self, html, base_url):
        """
        Parse the General Services Department procurement page.
        
        Args:
            html (str): HTML content of the page
            base_url (str): Base URL for resolving relative links
            
        Returns:
            list: List of RFP data dictionaries
        """
        rfps = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the table containing RFPs
        rfp_table = soup.find('table')
        
        if not rfp_table:
            logger.warning("Could not find RFP table on GSD procurement page")
            return rfps
        
        # Process each row in the table
        for row in rfp_table.find_all('tr')[1:]:  # Skip header row
            try:
                cells = row.find_all('td')
                
                if len(cells) < 5:
                    continue
                
                # Extract RFP ID and title
                title_cell = cells[0]
                title = title_cell.text.strip()
                
                # Extract RFP ID
                rfp_id_match = re.search(r'(\d{5,})', title)
                if rfp_id_match:
                    rfp_id = rfp_id_match.group(1)
                else:
                    # Generate a unique ID
                    rfp_id = f"{hash(title) % 10000000:07d}"
                
                # Extract URL if available
                rfp_url = base_url
                link = title_cell.find('a')
                if link and 'href' in link.attrs:
                    rfp_url = urljoin(base_url, link['href'])
                
                # Extract agency
                agency = cells[1].text.strip()
                
                # Extract description
                description = title
                
                # Extract dates
                pub_date_text = cells[2].text.strip()
                due_date_text = cells[3].text.strip()
                
                # Parse dates
                try:
                    pub_date = datetime.datetime.strptime(pub_date_text, '%m/%d/%Y').date().isoformat()
                except ValueError:
                    pub_date = None
                
                try:
                    due_date = datetime.datetime.strptime(due_date_text, '%m/%d/%Y').date().isoformat()
                except ValueError:
                    due_date = None
                
                # Extract contact information
                contact_info = cells[4].text.strip()
                contact_name = contact_info
                contact_email = None
                contact_phone = None
                
                # Extract email if present
                email_match = re.search(r'[\w\.-]+@[\w\.-]+', contact_info)
                if email_match:
                    contact_email = email_match.group(0)
                
                # Extract phone if present
                phone_match = re.search(r'\(\d{3}\)\s*\d{3}-\d{4}', contact_info)
                if phone_match:
                    contact_phone = phone_match.group(0)
                
                # Construct RFP data dictionary
                rfp_data = {
                    'id': f"NM-GSD-{rfp_id}",
                    'state': 'NM',
                    'title': title,
                    'description': description,
                    'publication_date': pub_date,
                    'due_date': due_date,
                    'category': None,
                    'agency': agency,
                    'contact_name': contact_name,
                    'contact_email': contact_email,
                    'contact_phone': contact_phone,
                    'url': rfp_url,
                    'document_urls': rfp_url
                }
                
                rfps.append(rfp_data)
                
            except Exception as e:
                logger.error(f"Error parsing GSD RFP row: {e}")
                continue
        
        return rfps
    
    def _parse_biz_nm_page(self, html, base_url):
        """
        Parse the Biz.NM.gov procurement page.
        
        Args:
            html (str): HTML content of the page
            base_url (str): Base URL for resolving relative links
            
        Returns:
            list: List of RFP data dictionaries
        """
        rfps = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the opportunities section
        opportunities = soup.find_all('div', class_='opportunity')
        
        if not opportunities:
            logger.warning("Could not find opportunities on Biz.NM.gov page")
            return rfps
        
        # Process each opportunity
        for opportunity in opportunities:
            try:
                # Extract title
                title_elem = opportunity.find('h3')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Extract RFP ID
                rfp_id_match = re.search(r'(\d{5,})', title)
                if rfp_id_match:
                    rfp_id = rfp_id_match.group(1)
                else:
                    # Generate a unique ID
                    rfp_id = f"{hash(title) % 10000000:07d}"
                
                # Extract URL if available
                rfp_url = base_url
                link = title_elem.find('a')
                if link and 'href' in link.attrs:
                    rfp_url = urljoin(base_url, link['href'])
                
                # Extract description
                description_elem = opportunity.find('p')
                description = title
                if description_elem:
                    description = description_elem.text.strip()
                
                # Extract agency
                agency_elem = opportunity.find('div', class_='agency')
                agency = "New Mexico"
                if agency_elem:
                    agency = agency_elem.text.strip()
                
                # Extract dates
                dates_elem = opportunity.find('div', class_='dates')
                pub_date = None
                due_date = None
                
                if dates_elem:
                    date_text = dates_elem.text.strip()
                    
                    # Extract publication date
                    pub_match = re.search(r'Posted:\s*(\d{2}/\d{2}/\d{4})', date_text)
                    if pub_match:
                        try:
                            pub_date = datetime.datetime.strptime(pub_match.group(1), '%m/%d/%Y').date().isoformat()
                        except ValueError:
                            pass
                    
                    # Extract due date
                    due_match = re.search(r'Due:\s*(\d{2}/\d{2}/\d{4})', date_text)
                    if due_match:
                        try:
                            due_date = datetime.datetime.strptime(due_match.group(1), '%m/%d/%Y').date().isoformat()
                        except ValueError:
                            pass
                
                # Extract contact information
                contact_elem = opportunity.find('div', class_='contact')
                contact_name = None
                contact_email = None
                contact_phone = None
                
                if contact_elem:
                    contact_info = contact_elem.text.strip()
                    contact_name = contact_info
                    
                    # Extract email if present
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+', contact_info)
                    if email_match:
                        contact_email = email_match.group(0)
                    
                    # Extract phone if present
                    phone_match = re.search(r'\(\d{3}\)\s*\d{3}-\d{4}', contact_info)
                    if phone_match:
                        contact_phone = phone_match.group(0)
                
                # Construct RFP data dictionary
                rfp_data = {
                    'id': f"NM-BIZ-{rfp_id}",
                    'state': 'NM',
                    'title': title,
                    'description': description,
                    'publication_date': pub_date,
                    'due_date': due_date,
                    'category': None,
                    'agency': agency,
                    'contact_name': contact_name,
                    'contact_email': contact_email,
                    'contact_phone': contact_phone,
                    'url': rfp_url,
                    'document_urls': rfp_url
                }
                
                rfps.append(rfp_data)
                
            except Exception as e:
                logger.error(f"Error parsing Biz.NM.gov opportunity: {e}")
                continue
        
        return rfps
    
    def _parse_dot_page(self, html, base_url):
        """
        Parse the Department of Transportation procurement page.
        
        Args:
            html (str): HTML content of the page
            base_url (str): Base URL for resolving relative links
            
        Returns:
            list: List of RFP data dictionaries
        """
        rfps = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the RFP listings
        rfp_listings = soup.find_all('div', class_='rfp-listing')
        
        if not rfp_listings:
            # Try alternative structure
            rfp_listings = soup.find_all('article', class_='post')
            
            if not rfp_listings:
                logger.warning("Could not find RFP listings on DOT procurement page")
                return rfps
        
        # Process each listing
        for listing in rfp_listings:
            try:
                # Extract title
                title_elem = listing.find(['h2', 'h3', 'h4'])
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Extract RFP ID
                rfp_id_match = re.search(r'(\d{5,})', title)
                if rfp_id_match:
                    rfp_id = rfp_id_match.group(1)
                else:
                    # Generate a unique ID
                    rfp_id = f"{hash(title) % 10000000:07d}"
                
                # Extract URL if available
                rfp_url = base_url
                link = title_elem.find('a')
                if link and 'href' in link.attrs:
                    rfp_url = urljoin(base_url, link['href'])
                
                # Extract description
                description_elem = listing.find('div', class_='description')
                description = title
                if description_elem:
                    description = description_elem.text.strip()
                
                # Extract dates
                dates_elem = listing.find('div', class_='dates')
                pub_date = None
                due_date = None
                
                if dates_elem:
                    date_text = dates_elem.text.strip()
                    
                    # Extract publication date
                    pub_match = re.search(r'Posted:\s*(\d{2}/\d{2}/\d{4})', date_text)
                    if pub_match:
                        try:
                            pub_date = datetime.datetime.strptime(pub_match.group(1), '%m/%d/%Y').date().isoformat()
                        except ValueError:
                            pass
                    
                    # Extract due date
                    due_match = re.search(r'Due:\s*(\d{2}/\d{2}/\d{4})', date_text)
                    if due_match:
                        try:
                            due_date = datetime.datetime.strptime(due_match.group(1), '%m/%d/%Y').date().isoformat()
                        except ValueError:
                            pass
                
                # Construct RFP data dictionary
                rfp_data = {
                    'id': f"NM-DOT-{rfp_id}",
                    'state': 'NM',
                    'title': title,
                    'description': description,
                    'publication_date': pub_date,
                    'due_date': due_date,
                    'category': None,
                    'agency': "New Mexico Department of Transportation",
                    'contact_name': None,
                    'contact_email': None,
                    'contact_phone': None,
                    'url': rfp_url,
                    'document_urls': rfp_url
                }
                
                rfps.append(rfp_data)
                
            except Exception as e:
                logger.error(f"Error parsing DOT RFP listing: {e}")
                continue
        
        return rfps
