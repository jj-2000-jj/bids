"""
Arizona Scraper - Implementation of RFP scraper for Arizona

This module implements the scraper for Arizona's procurement website.
"""

import re
import logging
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..base_scraper import BaseScraper

logger = logging.getLogger("rfp_scraper.arizona")

class ArizonaScraper(BaseScraper):
    """Scraper for Arizona's procurement website."""
    
    @property
    def state_code(self):
        return "AZ"
    
    @property
    def state_name(self):
        return "Arizona"
    
    @property
    def base_url(self):
        return "https://spo.az.gov/contracts/upcoming-bids"
    
    def scrape(self):
        """
        Scrape Arizona's procurement website for RFPs.
        
        Returns:
            int: Number of new RFPs found
        """
        logger.info(f"Starting scrape of {self.state_name} procurement website")
        
        new_rfps = 0
        
        try:
            # Get the main page
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table containing RFPs
            rfp_table = soup.find('table', class_='views-table')
            
            if not rfp_table:
                logger.warning("Could not find RFP table on Arizona procurement website")
                return 0
            
            # Process each row in the table
            for row in rfp_table.find_all('tr')[1:]:  # Skip header row
                try:
                    rfp_data = self._parse_rfp_row(row)
                    
                    if rfp_data:
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
                    logger.error(f"Error processing RFP row: {e}")
                    continue
            
            logger.info(f"Completed scrape of {self.state_name}, found {new_rfps} new RFPs")
            return new_rfps
            
        except Exception as e:
            logger.error(f"Error scraping {self.state_name} procurement website: {e}")
            return 0
    
    def _parse_rfp_row(self, row):
        """
        Parse an RFP row from the table.
        
        Args:
            row: BeautifulSoup row element
            
        Returns:
            dict: Dictionary containing RFP data, or None if parsing failed
        """
        try:
            cells = row.find_all('td')
            
            if len(cells) < 5:
                return None
            
            # Extract RFP ID and title
            title_cell = cells[0]
            title_link = title_cell.find('a')
            
            if not title_link:
                return None
            
            title = title_link.text.strip()
            rfp_url = urljoin(self.base_url, title_link['href'])
            
            # Extract RFP ID from title or URL
            rfp_id_match = re.search(r'(\w+-\d+)', title)
            if rfp_id_match:
                rfp_id = rfp_id_match.group(1)
            else:
                # Use URL as fallback ID
                rfp_id = f"AZ-{hash(rfp_url) % 10000000:07d}"
            
            # Extract agency
            agency = cells[1].text.strip()
            
            # Extract description (may need to visit detail page)
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
                'id': f"AZ-{rfp_id}",
                'state': 'AZ',
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
            
            return rfp_data
            
        except Exception as e:
            logger.error(f"Error parsing RFP row: {e}")
            return None
