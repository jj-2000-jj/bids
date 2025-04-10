"""
SCADA RFP Finder - Keyword Filtering Module

This module implements the keyword filtering functionality for identifying
SCADA-related RFPs across water/wastewater, mining, and oil/gas industries.
"""

import re
import logging
import json
from pathlib import Path

logger = logging.getLogger("rfp_scraper.keyword_filter")

class KeywordFilter:
    """
    Implements keyword-based filtering to identify SCADA-related RFPs
    and categorize them by industry.
    """
    
    def __init__(self, keywords_file=None):
        """
        Initialize the keyword filter.
        
        Args:
            keywords_file (str, optional): Path to JSON file containing keywords.
                If not provided, uses default keywords.
        """
        self.keywords = self._load_keywords(keywords_file)
        logger.info(f"Initialized keyword filter with {len(self.keywords)} keyword categories")
    
    def _load_keywords(self, keywords_file):
        """
        Load keywords from file or use default keywords.
        
        Args:
            keywords_file (str): Path to JSON file containing keywords
            
        Returns:
            dict: Dictionary of keyword categories and their weights
        """
        if keywords_file and Path(keywords_file).exists():
            try:
                with open(keywords_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading keywords file: {e}")
        
        # Default keywords if file not provided or loading fails
        return {
            "core_scada": {
                "weight": 10,
                "terms": [
                    "scada", "supervisory control", "data acquisition", 
                    "plc", "programmable logic controller",
                    "rtu", "remote terminal unit",
                    "hmi", "human machine interface",
                    "automation", "control system", "telemetry",
                    "distributed control system", "dcs"
                ]
            },
            "water_wastewater": {
                "weight": 5,
                "terms": [
                    "water treatment", "wastewater", "pump station", "lift station",
                    "flow meter", "level sensor", "pressure sensor", "filtration",
                    "aeration", "chlorination", "disinfection", "sedimentation",
                    "activated sludge", "clarifier", "reservoir", "distribution network"
                ]
            },
            "mining": {
                "weight": 5,
                "terms": [
                    "mining", "mine", "extraction", "crusher", "conveyor",
                    "beneficiation", "flotation", "leaching", "grinding",
                    "screening", "classification", "concentration", "tailings",
                    "dewatering", "ventilation", "hoisting", "drilling"
                ]
            },
            "oil_gas": {
                "weight": 5,
                "terms": [
                    "oil", "gas", "pipeline", "wellhead", "separator",
                    "compressor", "metering", "custody transfer", "drilling",
                    "production", "injection", "gathering", "processing",
                    "refining", "storage", "distribution", "flare"
                ]
            },
            "communication": {
                "weight": 3,
                "terms": [
                    "ethernet", "tcp/ip", "modbus", "dnp3", "opc ua",
                    "mqtt", "cellular", "radio", "satellite", "wireless",
                    "fiber optic", "network", "communication", "protocol"
                ]
            },
            "integration": {
                "weight": 3,
                "terms": [
                    "integration", "interface", "connect", "api", "data exchange",
                    "interoperability", "middleware", "enterprise", "erp",
                    "mes", "historian", "database", "cloud", "iot"
                ]
            },
            "project_types": {
                "weight": 2,
                "terms": [
                    "upgrade", "replacement", "expansion", "installation",
                    "modernization", "migration", "standardization", "consolidation",
                    "virtualization", "cybersecurity", "security"
                ]
            },
            "service_types": {
                "weight": 2,
                "terms": [
                    "design", "engineering", "installation", "configuration",
                    "programming", "integration", "testing", "commissioning",
                    "training", "support", "maintenance", "consulting"
                ]
            }
        }
    
    def calculate_relevance(self, text):
        """
        Calculate SCADA relevance score and industry categorization for text.
        
        Args:
            text (str): Text to analyze (typically RFP title + description)
            
        Returns:
            tuple: (score, is_water_wastewater, is_mining, is_oil_gas)
                score: 0-100 relevance score
                is_water_wastewater: Boolean indicating water/wastewater relevance
                is_mining: Boolean indicating mining relevance
                is_oil_gas: Boolean indicating oil/gas relevance
        """
        if not text:
            return 0, False, False, False
        
        text = text.lower()
        
        # Track matches by category
        matches = {category: 0 for category in self.keywords}
        
        # Count keyword matches in each category
        for category, data in self.keywords.items():
            for term in data["terms"]:
                # Use word boundary to match whole words
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text):
                    matches[category] += 1
        
        # Calculate weighted score
        total_score = 0
        max_possible_score = 0
        
        for category, data in self.keywords.items():
            weight = data["weight"]
            match_count = matches[category]
            total_terms = len(data["terms"])
            
            # Add to score based on matches and weight
            category_score = (match_count / total_terms) * weight * 100
            total_score += category_score
            
            # Track maximum possible score
            max_possible_score += weight * 100
        
        # Normalize score to 0-100 range
        normalized_score = min(100, int((total_score / max_possible_score) * 100))
        
        # Determine industry relevance
        is_water_wastewater = matches["water_wastewater"] > 0
        is_mining = matches["mining"] > 0
        is_oil_gas = matches["oil_gas"] > 0
        
        # If no specific industry is matched but core SCADA terms are present,
        # mark as potentially relevant to all industries
        if matches["core_scada"] > 0 and not any([is_water_wastewater, is_mining, is_oil_gas]):
            # Look for industry-adjacent terms
            if any(term in text for term in ["water", "utility", "municipal", "treatment"]):
                is_water_wastewater = True
            if any(term in text for term in ["mineral", "excavation", "quarry"]):
                is_mining = True
            if any(term in text for term in ["petroleum", "hydrocarbon", "fuel"]):
                is_oil_gas = True
        
        return normalized_score, is_water_wastewater, is_mining, is_oil_gas
    
    def get_matching_keywords(self, text):
        """
        Get list of matching keywords in the text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Dictionary of categories and their matching keywords
        """
        if not text:
            return {}
        
        text = text.lower()
        matches = {}
        
        for category, data in self.keywords.items():
            category_matches = []
            for term in data["terms"]:
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text):
                    category_matches.append(term)
            
            if category_matches:
                matches[category] = category_matches
        
        return matches
