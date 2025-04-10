"""
Run scrapers to verify RFP detection.
"""

from webapp import create_app, db
from webapp.scrapers.main import run_all_scrapers
from webapp.models.rfp import RFP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_scrapers_test():
    """Run scrapers and verify RFP detection."""
    app = create_app()
    
    with app.app_context():
        # Get initial RFP count
        initial_count = RFP.query.count()
        logger.info(f"Initial RFP count: {initial_count}")
        
        # Run scrapers with limited scope for testing
        logger.info("Starting scrapers...")
        results = run_all_scrapers(max_municipalities=5)
        logger.info(f"Scraping completed. Results: {results}")
        
        # Get final RFP count
        final_count = RFP.query.count()
        logger.info(f"Final RFP count: {final_count}")
        
        # Get newly added RFPs
        new_rfps = final_count - initial_count
        logger.info(f"Newly added RFPs: {new_rfps}")
        
        # Show some details of found RFPs
        if new_rfps > 0:
            logger.info("Sample of found RFPs:")
            rfps = RFP.query.order_by(RFP.created_at.desc()).limit(5).all()
            for rfp in rfps:
                logger.info(f"- {rfp.id}: {rfp.title} (Relevance: {rfp.scada_relevance_score}%)")
                logger.info(f"  State: {rfp.state}, Agency: {rfp.agency}")
                logger.info(f"  Categories: Water: {rfp.is_water_wastewater}, Mining: {rfp.is_mining}, Oil & Gas: {rfp.is_oil_gas}, HVAC: {rfp.is_hvac}")
                logger.info(f"  URL: {rfp.url}")
                logger.info("---")
        
        # Test Utah Bonfirehub scraper specifically for the example RFP
        from webapp.scrapers.utah_bonfirehub import process_opportunity
        import requests
        
        logger.info("Testing Utah Bonfirehub scraper for example RFP...")
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Delete existing RFP if it exists to ensure we can test detection
        example_rfp = RFP.query.filter_by(id="UTBF-176637").first()
        if example_rfp:
            logger.info(f"Deleting existing example RFP: {example_rfp.title}")
            db.session.delete(example_rfp)
            db.session.commit()
        
        # Process the example RFP
        example_result = process_opportunity(session, "176637", headers)
        logger.info(f"Example RFP processing result: {example_result}")
        
        # Check if the example RFP was found
        example_rfp = RFP.query.filter_by(id="UTBF-176637").first()
        if example_rfp:
            logger.info(f"Successfully found example RFP: {example_rfp.title}")
            logger.info(f"Relevance score: {example_rfp.scada_relevance_score}%")
            logger.info(f"Categories: Water: {example_rfp.is_water_wastewater}, Mining: {example_rfp.is_mining}, Oil & Gas: {example_rfp.is_oil_gas}, HVAC: {example_rfp.is_hvac}")
        else:
            logger.error("Failed to find example RFP")
        
        return {
            'initial_count': initial_count,
            'final_count': final_count,
            'new_rfps': new_rfps,
            'example_rfp_found': example_rfp is not None
        }

if __name__ == "__main__":
    run_scrapers_test()
