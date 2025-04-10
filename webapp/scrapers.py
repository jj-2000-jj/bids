import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta
from webapp.models import RFP, State, ScraperLog
from webapp import db

class ArizonaScraper:
    """Scraper for Arizona state procurement website"""
    
    def __init__(self):
        self.base_url = "https://spo.az.gov/contracts/upcoming-bids"
        self.state_code = "AZ"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # SCADA-related keywords
        self.scada_keywords = [
            'scada', 'supervisory control', 'data acquisition', 'plc', 'programmable logic controller',
            'hmi', 'human machine interface', 'rtu', 'remote terminal unit', 'telemetry',
            'automation', 'control system', 'industrial control', 'distributed control',
            'instrumentation', 'sensor', 'monitoring system', 'process control'
        ]
        
        # Water/wastewater keywords
        self.water_keywords = [
            'water', 'wastewater', 'sewage', 'treatment plant', 'utility', 'utilities',
            'pump station', 'lift station', 'distribution system', 'collection system',
            'drinking water', 'potable water', 'effluent', 'filtration', 'disinfection'
        ]
        
        # Mining keywords
        self.mining_keywords = [
            'mining', 'mine', 'mineral', 'extraction', 'excavation', 'ore', 'coal',
            'metals', 'quarry', 'pit', 'underground', 'surface mining', 'drill'
        ]
        
        # Oil and gas keywords
        self.oil_gas_keywords = [
            'oil', 'gas', 'petroleum', 'pipeline', 'refinery', 'wellhead', 'drilling',
            'upstream', 'midstream', 'downstream', 'hydrocarbon', 'natural gas',
            'compressor', 'lng', 'production'
        ]
    
    def scrape(self):
        """Scrape Arizona procurement website for RFPs"""
        # Create log entry
        log = ScraperLog(
            state=self.state_code,
            start_time=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        rfps_found = 0
        
        try:
            # Get the main page
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table with RFPs
            rfp_table = soup.find('table', class_='views-table')
            
            if rfp_table:
                # Process each row in the table
                for row in rfp_table.find_all('tr')[1:]:  # Skip header row
                    cells = row.find_all('td')
                    
                    if len(cells) >= 5:
                        # Extract RFP information
                        title = cells[0].get_text(strip=True)
                        agency = cells[1].get_text(strip=True)
                        
                        # Extract publication date
                        pub_date_text = cells[2].get_text(strip=True)
                        pub_date = None
                        try:
                            pub_date = datetime.strptime(pub_date_text, '%m/%d/%Y').date()
                        except ValueError:
                            pass
                        
                        # Extract due date
                        due_date_text = cells[3].get_text(strip=True)
                        due_date = None
                        try:
                            due_date = datetime.strptime(due_date_text, '%m/%d/%Y').date()
                        except ValueError:
                            pass
                        
                        # Extract URL if available
                        url = None
                        link = cells[0].find('a')
                        if link and 'href' in link.attrs:
                            url = link['href']
                            if not url.startswith('http'):
                                url = f"https://spo.az.gov{url}"
                        
                        # Get description if available
                        description = ""
                        if url:
                            try:
                                detail_response = requests.get(url, headers=self.headers)
                                detail_response.raise_for_status()
                                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                                
                                # Look for description in the detail page
                                description_div = detail_soup.find('div', class_='field-name-body')
                                if description_div:
                                    description = description_div.get_text(strip=True)
                            except Exception as e:
                                print(f"Error fetching detail page: {e}")
                        
                        # Combine title and description for keyword matching
                        full_text = f"{title} {description}".lower()
                        
                        # Check if RFP is SCADA-related
                        is_scada_related = any(keyword in full_text for keyword in self.scada_keywords)
                        
                        if is_scada_related:
                            # Calculate relevance score
                            scada_matches = sum(1 for keyword in self.scada_keywords if keyword in full_text)
                            
                            # Check industry relevance
                            is_water = any(keyword in full_text for keyword in self.water_keywords)
                            is_mining = any(keyword in full_text for keyword in self.mining_keywords)
                            is_oil_gas = any(keyword in full_text for keyword in self.oil_gas_keywords)
                            
                            # Calculate overall relevance score (0-100)
                            relevance_score = min(100, int((scada_matches / len(self.scada_keywords)) * 100))
                            
                            # Generate a unique ID
                            rfp_id = f"AZ-{pub_date.strftime('%Y%m%d') if pub_date else datetime.now().strftime('%Y%m%d')}-{hash(title) % 10000:04d}"
                            
                            # Check if RFP already exists
                            existing_rfp = RFP.query.get(rfp_id)
                            if not existing_rfp:
                                # Create new RFP
                                rfp = RFP(
                                    id=rfp_id,
                                    title=title,
                                    description=description,
                                    state=self.state_code,
                                    agency=agency,
                                    publication_date=pub_date,
                                    due_date=due_date,
                                    url=url,
                                    scada_relevance_score=relevance_score,
                                    is_water_wastewater=is_water,
                                    is_mining=is_mining,
                                    is_oil_gas=is_oil_gas,
                                    created_at=datetime.utcnow()
                                )
                                
                                db.session.add(rfp)
                                rfps_found += 1
                            
                            # Commit every 10 RFPs to avoid large transactions
                            if rfps_found % 10 == 0:
                                db.session.commit()
            
            # Final commit
            db.session.commit()
            
            # Update log entry
            log.end_time = datetime.utcnow()
            log.success = True
            log.rfps_found = rfps_found
            db.session.commit()
            
            return rfps_found
            
        except Exception as e:
            # Update log entry with error
            log.end_time = datetime.utcnow()
            log.success = False
            log.error_message = str(e)
            db.session.commit()
            
            raise e

class NewMexicoScraper:
    """Scraper for New Mexico state procurement website"""
    
    def __init__(self):
        self.base_url = "https://www.generalservices.state.nm.us/state-purchasing/active-itbs-and-rfps/active-procurements/"
        self.state_code = "NM"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # SCADA-related keywords
        self.scada_keywords = [
            'scada', 'supervisory control', 'data acquisition', 'plc', 'programmable logic controller',
            'hmi', 'human machine interface', 'rtu', 'remote terminal unit', 'telemetry',
            'automation', 'control system', 'industrial control', 'distributed control',
            'instrumentation', 'sensor', 'monitoring system', 'process control'
        ]
        
        # Water/wastewater keywords
        self.water_keywords = [
            'water', 'wastewater', 'sewage', 'treatment plant', 'utility', 'utilities',
            'pump station', 'lift station', 'distribution system', 'collection system',
            'drinking water', 'potable water', 'effluent', 'filtration', 'disinfection'
        ]
        
        # Mining keywords
        self.mining_keywords = [
            'mining', 'mine', 'mineral', 'extraction', 'excavation', 'ore', 'coal',
            'metals', 'quarry', 'pit', 'underground', 'surface mining', 'drill'
        ]
        
        # Oil and gas keywords
        self.oil_gas_keywords = [
            'oil', 'gas', 'petroleum', 'pipeline', 'refinery', 'wellhead', 'drilling',
            'upstream', 'midstream', 'downstream', 'hydrocarbon', 'natural gas',
            'compressor', 'lng', 'production'
        ]
    
    def scrape(self):
        """Scrape New Mexico procurement website for RFPs"""
        # Create log entry
        log = ScraperLog(
            state=self.state_code,
            start_time=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        rfps_found = 0
        
        try:
            # Get the main page
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table with RFPs
            rfp_table = soup.find('table')
            
            if rfp_table:
                # Process each row in the table
                for row in rfp_table.find_all('tr')[1:]:  # Skip header row
                    cells = row.find_all('td')
                    
                    if len(cells) >= 4:
                        # Extract RFP information
                        title = cells[0].get_text(strip=True)
                        agency = cells[1].get_text(strip=True)
                        
                        # Extract due date
                        due_date_text = cells[2].get_text(strip=True)
                        due_date = None
                        try:
                            due_date = datetime.strptime(due_date_text, '%m/%d/%Y').date()
                        except ValueError:
                            pass
                        
                        # Extract URL if available
                        url = None
                        link = cells[3].find('a')
                        if link and 'href' in link.attrs:
                            url = link['href']
                        
                        # Get description if available
                        description = ""
                        if url:
                            try:
                                detail_response = requests.get(url, headers=self.headers)
                                detail_response.raise_for_status()
                                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                                
                                # Look for description in the detail page
                                description_div = detail_soup.find('div', class_='description')
                                if description_div:
                                    description = description_div.get_text(strip=True)
                                else:
                                    # Try to get text from the main content area
                                    content_div = detail_soup.find('div', class_='content')
                                    if content_div:
                                        description = content_div.get_text(strip=True)
                            except Exception as e:
                                print(f"Error fetching detail page: {e}")
                        
                        # Combine title and description for keyword matching
                        full_text = f"{title} {description}".lower()
                        
                        # Check if RFP is SCADA-related
                        is_scada_related = any(keyword in full_text for keyword in self.scada_keywords)
                        
                        if is_scada_related:
                            # Calculate relevance score
                            scada_matches = sum(1 for keyword in self.scada_keywords if keyword in full_text)
                            
                            # Check industry relevance
                            is_water = any(keyword in full_text for keyword in self.water_keywords)
                            is_mining = any(keyword in full_text for keyword in self.mining_keywords)
                            is_oil_gas = any(keyword in full_text for keyword in self.oil_gas_keywords)
                            
                            # Calculate overall relevance score (0-100)
                            relevance_score = min(100, int((scada_matches / len(self.scada_keywords)) * 100))
                            
                            # Generate a unique ID
                            rfp_id = f"NM-{due_date.strftime('%Y%m%d') if due_date else datetime.now().strftime('%Y%m%d')}-{hash(title) % 10000:04d}"
                            
                            # Check if RFP already exists
                            existing_rfp = RFP.query.get(rfp_id)
                            if not existing_rfp:
                                # Create new RFP
                                rfp = RFP(
                                    id=rfp_id,
                                    title=title,
                                    description=description,
                                    state=self.state_code,
                                    agency=agency,
                                    publication_date=datetime.now().date(),  # Use current date as publication date
                                    due_date=due_date,
                                    url=url,
                                    scada_relevance_score=relevance_score,
                                    is_water_wastewater=is_water,
                                    is_mining=is_mining,
                                    is_oil_gas=is_oil_gas,
                                    created_at=datetime.utcnow()
                                )
                                
                                db.session.add(rfp)
                                rfps_found += 1
                            
                            # Commit every 10 RFPs to avoid large transactions
                            if rfps_found % 10 == 0:
                                db.session.commit()
            
            # Final commit
            db.session.commit()
            
            # Update log entry
            log.end_time = datetime.utcnow()
            log.success = True
            log.rfps_found = rfps_found
            db.session.commit()
            
            return rfps_found
            
        except Exception as e:
            # Update log entry with error
            log.end_time = datetime.utcnow()
            log.success = False
            log.error_message = str(e)
            db.session.commit()
            
            raise e

def run_all_scrapers():
    """Run all state scrapers"""
    results = {}
    
    # Get enabled states
    states = State.query.filter_by(enabled=True).all()
    
    for state in states:
        if state.code == "AZ":
            scraper = ArizonaScraper()
            try:
                rfps_found = scraper.scrape()
                results["AZ"] = f"Success: {rfps_found} RFPs found"
            except Exception as e:
                results["AZ"] = f"Error: {str(e)}"
        
        elif state.code == "NM":
            scraper = NewMexicoScraper()
            try:
                rfps_found = scraper.scrape()
                results["NM"] = f"Success: {rfps_found} RFPs found"
            except Exception as e:
                results["NM"] = f"Error: {str(e)}"
    
    return results

def run_state_scraper(state_code):
    """Run scraper for a specific state"""
    if state_code == "AZ":
        scraper = ArizonaScraper()
        return scraper.scrape()
    
    elif state_code == "NM":
        scraper = NewMexicoScraper()
        return scraper.scrape()
    
    return 0
