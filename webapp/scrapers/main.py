"""
Main module for SCADA RFP scrapers

This module provides functions to run all scrapers and process the results.
"""

import logging
from datetime import datetime, timedelta

from webapp import db
from webapp.models import RFP, ScraperLog
from webapp.scrapers.sam_gov import run_sam_gov_scraper
from webapp.scrapers.utah_bonfirehub import run_utah_bonfirehub_scraper
from webapp.scrapers.municipality_factory import run_municipality_scrapers

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_all_scrapers(target_states=None, max_municipalities=2000):
    """
    Run all scrapers to find SCADA-related RFPs
    
    Args:
        target_states: List of state codes to filter by (default: None, uses all target states)
        max_municipalities: Maximum number of municipalities to scrape (default: 100)
    
    Returns:
        Dictionary with scraper results
    """
    if target_states is None:
        target_states = ['AZ', 'NM', 'UT', 'ID', 'IL', 'MO', 'IA', 'IN']
    
    results = {
        'sam_gov': 0,
        'utah_bonfirehub': 0,
        'municipalities': 0,
        'total': 0
    }
    
    start_time = datetime.utcnow()
    
    try:
        # Create scraper log entry
        scraper_log = ScraperLog(
            state="ALL",
            municipality="ALL",
            start_time=start_time,
            success=False,
            rfps_found=0
        )
        db.session.add(scraper_log)
        db.session.commit()
        
        # Run SAM.gov scraper
        logger.info("Running SAM.gov scraper...")
        try:
            sam_gov_rfps = run_sam_gov_scraper()
            results['sam_gov'] = sam_gov_rfps
            results['total'] += sam_gov_rfps
            logger.info(f"SAM.gov scraper found {sam_gov_rfps} new SCADA-related RFPs")
        except Exception as e:
            logger.error(f"Error running SAM.gov scraper: {str(e)}")
        
        # Run Utah Bonfirehub scraper
        logger.info("Running Utah Bonfirehub scraper...")
        try:
            utah_bonfirehub_rfps = run_utah_bonfirehub_scraper()
            results['utah_bonfirehub'] = utah_bonfirehub_rfps
            results['total'] += utah_bonfirehub_rfps
            logger.info(f"Utah Bonfirehub scraper found {utah_bonfirehub_rfps} new SCADA-related RFPs")
        except Exception as e:
            logger.error(f"Error running Utah Bonfirehub scraper: {str(e)}")
        
        # Run municipality scrapers
        logger.info(f"Running municipality scrapers (max {max_municipalities})...")
        try:
            municipality_rfps = run_municipality_scrapers(states=target_states, max_municipalities=max_municipalities)
            results['municipalities'] = municipality_rfps
            results['total'] += municipality_rfps
            logger.info(f"Municipality scrapers found {municipality_rfps} new SCADA-related RFPs")
        except Exception as e:
            logger.error(f"Error running municipality scrapers: {str(e)}")
        
        # Update scraper log
        scraper_log.end_time = datetime.utcnow()
        scraper_log.duration = (scraper_log.end_time - start_time).total_seconds()
        scraper_log.success = True
        scraper_log.rfps_found = results['total']
        db.session.commit()
        
        return results
        
    except Exception as e:
        logger.error(f"Error running scrapers: {str(e)}")
        
        # Update scraper log with error
        if 'scraper_log' in locals():
            scraper_log.end_time = datetime.utcnow()
            scraper_log.duration = (scraper_log.end_time - start_time).total_seconds()
            scraper_log.success = False
            scraper_log.error_message = str(e)
            db.session.commit()
        
        return results

def run_state_scraper(state_code):
    """
    Run scrapers for a specific state
    
    Args:
        state_code: State code to scrape (e.g., 'AZ')
    
    Returns:
        Number of new SCADA-related RFPs found
    """
    results = {
        'sam_gov': 0,
        'utah_bonfirehub': 0,
        'municipalities': 0,
        'total': 0
    }
    
    # Run SAM.gov scraper (filtered by state if possible)
    if state_code == 'US':
        results['sam_gov'] = run_sam_gov_scraper()
        results['total'] += results['sam_gov']
    
    # Run Utah Bonfirehub scraper (only for Utah)
    if state_code == 'UT':
        results['utah_bonfirehub'] = run_utah_bonfirehub_scraper()
        results['total'] += results['utah_bonfirehub']
    
    # Run municipality scrapers for the state
    results['municipalities'] = run_municipality_scrapers(states=[state_code])
    results['total'] += results['municipalities']
    
    return results['total']

def get_rfp_stats():
    """
    Get statistics about RFPs in the database
    
    Returns:
        Dictionary with RFP statistics
    """
    stats = {
        'total': 0,
        'by_state': {},
        'by_industry': {
            'water_wastewater': 0,
            'mining': 0,
            'oil_gas': 0,
            'hvac': 0,
            'other': 0
        },
        'by_relevance': {
            'high': 0,
            'medium': 0,
            'low': 0
        }
    }
    
    # Get total RFPs
    stats['total'] = RFP.query.count()
    
    # Get RFPs by state
    state_counts = db.session.query(RFP.state, db.func.count(RFP.id)).group_by(RFP.state).all()
    for state, count in state_counts:
        stats['by_state'][state] = count
    
    # Get RFPs by industry
    stats['by_industry']['water_wastewater'] = RFP.query.filter_by(is_water_wastewater=True).count()
    stats['by_industry']['mining'] = RFP.query.filter_by(is_mining=True).count()
    stats['by_industry']['oil_gas'] = RFP.query.filter_by(is_oil_gas=True).count()
    
    # Get HVAC RFPs if the field exists
    try:
        stats['by_industry']['hvac'] = RFP.query.filter_by(is_hvac=True).count()
    except:
        logger.warning("is_hvac field not available in RFP model")
        stats['by_industry']['hvac'] = 0
    
    # Calculate 'other' category (RFPs that don't fit into any specific industry)
    try:
        other_count = RFP.query.filter(
            ~RFP.is_water_wastewater & ~RFP.is_mining & ~RFP.is_oil_gas & ~RFP.is_hvac
        ).count()
    except:
        # If is_hvac field doesn't exist
        other_count = RFP.query.filter(
            ~RFP.is_water_wastewater & ~RFP.is_mining & ~RFP.is_oil_gas
        ).count()
    
    stats['by_industry']['other'] = other_count
    
    # Get RFPs by relevance
    stats['by_relevance']['high'] = RFP.query.filter(RFP.scada_relevance_score >= 70).count()
    stats['by_relevance']['medium'] = RFP.query.filter(
        (RFP.scada_relevance_score >= 40) & (RFP.scada_relevance_score < 70)
    ).count()
    stats['by_relevance']['low'] = RFP.query.filter(RFP.scada_relevance_score < 40).count()
    
    return stats
