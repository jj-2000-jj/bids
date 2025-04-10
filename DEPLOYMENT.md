# SCADA RFP Finder - Deployment Guide

This guide provides instructions for deploying the SCADA RFP Finder application locally.

## System Requirements

- Python 3.8 or higher
- PostgreSQL 12 or higher (or SQLite for development)
- Modern web browser (Chrome, Firefox, Edge)
- Internet connection for scraping RFPs

## Installation Steps

1. **Clone the repository**

   ```bash
   git clone <your-repository-url>
   cd rfp_project
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database**

   Edit `config.json` to set your database connection:

   ```json
   {
     "DATABASE_URI": "sqlite:///rfp_finder.db",
     "SECRET_KEY": "your-secret-key",
     "DEBUG": true
   }
   ```

   For PostgreSQL:
   ```json
   {
     "DATABASE_URI": "postgresql://username:password@localhost/rfp_finder",
     "SECRET_KEY": "your-secret-key",
     "DEBUG": false
   }
   ```

5. **Initialize the database**

   ```bash
   python -c "from webapp import create_app, db; app = create_app(); with app.app_context(): db.create_all()"
   ```

6. **Run database migrations**

   ```bash
   python run_migrations.py
   ```

7. **Initialize states**

   ```bash
   python init_states.py
   ```

8. **Run the application**

   ```bash
   python run.py
   ```

   The application will be available at http://localhost:5000

## Docker Deployment (Optional)

1. **Build the Docker image**

   ```bash
   docker build -t scada-rfp-finder .
   ```

2. **Run with Docker Compose**

   ```bash
   docker-compose up -d
   ```

   The application will be available at http://localhost:5000

## Key Features and Improvements

1. **Enhanced Keyword Matching System**
   - Added HVAC-specific terms
   - Created a new HVAC category
   - Lowered relevance threshold for better detection
   - Special handling for RFPs with "SCADA" in the title

2. **Improved Utah Bonfirehub Scraper**
   - More robust HTML parsing
   - Fallback methods for different page structures
   - Pagination support for multiple pages
   - Special handling for specific RFPs

3. **Municipality Scrapers from CSV**
   - Support for 1,882 municipalities across target states
   - State code conversion for different formats
   - Configurable maximum municipalities to scrape

4. **New "Start Scraping Now" Button**
   - Allows any authenticated user to start scraping
   - Real-time progress tracking
   - Status updates during scraping process

## Usage Guide

1. **Register an account**
   - The first registered user will be an admin
   - Admin can manage users, RFPs, and scraper settings

2. **Run scrapers**
   - Use the "Start Scraping Now" button on the home page
   - Or use the admin interface for more control

3. **View and filter RFPs**
   - Browse all RFPs or filter by state, industry, etc.
   - Mark favorites for later reference
   - Export RFPs to CSV

4. **Configure notifications**
   - Set up email notifications for new RFPs
   - Customize notification preferences

## Troubleshooting

1. **Database connection issues**
   - Verify database credentials in config.json
   - Ensure database server is running

2. **Scraper errors**
   - Check internet connection
   - Some websites may block scrapers or change their structure
   - Review logs for specific errors

3. **Application not starting**
   - Check for port conflicts (default: 5000)
   - Verify all dependencies are installed

## Support

For questions or issues, please contact your system administrator or refer to the project documentation.
