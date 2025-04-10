"""
Base Scraper Class - Abstract base class for state-specific scrapers

This module defines the BaseScraper abstract class that all state-specific
scrapers must inherit from to ensure consistent interface and functionality.
"""

import os
import logging
import sqlite3
import datetime
import requests
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger("rfp_scraper.base")

class BaseScraper(ABC):
    """Abstract base class for all state-specific RFP scrapers."""
    
    def __init__(self, db_connection, output_dir):
        """
        Initialize the base scraper.
        
        Args:
            db_connection: SQLite database connection
            output_dir (str): Directory to store downloaded RFP documents
        """
        self.conn = db_connection
        self.output_dir = output_dir
        self.state_dir = os.path.join(output_dir, self.state_code)
        
        # Ensure state-specific output directory exists
        os.makedirs(self.state_dir, exist_ok=True)
        
        # Set up requests session with appropriate headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
    
    @property
    @abstractmethod
    def state_code(self):
        """Return the two-letter state code (e.g., 'AZ', 'NM')."""
        pass
    
    @property
    @abstractmethod
    def state_name(self):
        """Return the full state name (e.g., 'Arizona', 'New Mexico')."""
        pass
    
    @property
    @abstractmethod
    def base_url(self):
        """Return the base URL for the state's procurement website."""
        pass
    
    @abstractmethod
    def scrape(self):
        """
        Scrape the state's procurement website for RFPs.
        
        Returns:
            int: Number of new RFPs found
        """
        pass
    
    def save_rfp(self, rfp_data):
        """
        Save RFP data to the database.
        
        Args:
            rfp_data (dict): Dictionary containing RFP data
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if RFP already exists
            cursor.execute('SELECT id FROM RFPs WHERE id = ?', (rfp_data['id'],))
            existing = cursor.fetchone()
            
            now = datetime.datetime.now().isoformat()
            
            if existing:
                # Update existing RFP
                fields = []
                values = []
                
                for key, value in rfp_data.items():
                    if key != 'id':
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                fields.append("updated_at = ?")
                values.append(now)
                values.append(rfp_data['id'])
                
                query = f"UPDATE RFPs SET {', '.join(fields)} WHERE id = ?"
                cursor.execute(query, values)
                
                logger.info(f"Updated RFP {rfp_data['id']} in database")
                
            else:
                # Insert new RFP
                rfp_data['created_at'] = now
                rfp_data['updated_at'] = now
                
                fields = ', '.join(rfp_data.keys())
                placeholders = ', '.join(['?'] * len(rfp_data))
                
                query = f"INSERT INTO RFPs ({fields}) VALUES ({placeholders})"
                cursor.execute(query, list(rfp_data.values()))
                
                logger.info(f"Inserted new RFP {rfp_data['id']} into database")
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Database error saving RFP {rfp_data.get('id', 'unknown')}: {e}")
            return False
    
    def download_document(self, url, filename):
        """
        Download an RFP document and save it to the output directory.
        
        Args:
            url (str): URL of the document to download
            filename (str): Filename to save the document as
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Determine file extension based on content type
            content_type = response.headers.get('Content-Type', '')
            ext = self._get_extension_from_content_type(content_type)
            
            if not filename.endswith(ext):
                filename = f"{filename}{ext}"
            
            file_path = os.path.join(self.state_dir, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded document from {url} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading document from {url}: {e}")
            return None
    
    def _get_extension_from_content_type(self, content_type):
        """
        Determine file extension based on content type.
        
        Args:
            content_type (str): HTTP Content-Type header
            
        Returns:
            str: File extension including the dot
        """
        content_type = content_type.lower()
        
        if 'application/pdf' in content_type:
            return '.pdf'
        elif 'application/msword' in content_type:
            return '.doc'
        elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
            return '.docx'
        elif 'application/vnd.ms-excel' in content_type:
            return '.xls'
        elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
            return '.xlsx'
        elif 'text/plain' in content_type:
            return '.txt'
        elif 'text/html' in content_type:
            return '.html'
        else:
            return '.bin'
    
    def calculate_scada_relevance(self, title, description):
        """
        Calculate SCADA relevance score based on keyword matching.
        
        Args:
            title (str): RFP title
            description (str): RFP description
            
        Returns:
            tuple: (score, is_water_wastewater, is_mining, is_oil_gas)
        """
        # This is a simplified implementation
        # A more sophisticated version would use the SCADA keywords list
        # and apply different weights to different categories
        
        text = f"{title} {description}".lower()
        
        # Core SCADA keywords
        core_keywords = [
            'scada', 'supervisory control', 'data acquisition', 
            'plc', 'programmable logic controller',
            'rtu', 'remote terminal unit',
            'hmi', 'human machine interface',
            'automation', 'control system'
        ]
        
        # Water/wastewater keywords
        water_keywords = [
            'water treatment', 'wastewater', 'pump station', 'lift station',
            'flow meter', 'level sensor', 'pressure sensor', 'filtration'
        ]
        
        # Mining keywords
        mining_keywords = [
            'mining', 'mine', 'extraction', 'crusher', 'conveyor',
            'beneficiation', 'flotation', 'leaching'
        ]
        
        # Oil and gas keywords
        oil_gas_keywords = [
            'oil', 'gas', 'pipeline', 'wellhead', 'separator',
            'compressor', 'metering', 'custody transfer'
        ]
        
        # Count keyword matches
        core_matches = sum(1 for keyword in core_keywords if keyword in text)
        water_matches = sum(1 for keyword in water_keywords if keyword in text)
        mining_matches = sum(1 for keyword in mining_keywords if keyword in text)
        oil_gas_matches = sum(1 for keyword in oil_gas_keywords if keyword in text)
        
        # Calculate industry flags
        is_water_wastewater = water_matches > 0
        is_mining = mining_matches > 0
        is_oil_gas = oil_gas_matches > 0
        
        # Calculate overall score (0-100)
        # Core keywords are weighted more heavily
        score = min(100, (core_matches * 10) + (water_matches + mining_matches + oil_gas_matches) * 5)
        
        return (score, is_water_wastewater, is_mining, is_oil_gas)
