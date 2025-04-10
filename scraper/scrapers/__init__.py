"""
__init__.py - Package initialization for scrapers

This file initializes the scrapers package and makes the scraper classes available.
"""

from .arizona import ArizonaScraper
from .new_mexico import NewMexicoScraper

# Export the scraper classes
__all__ = ['ArizonaScraper', 'NewMexicoScraper']
