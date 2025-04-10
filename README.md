# SCADA RFP Finder - User Guide

## Overview

SCADA RFP Finder is a custom solution for finding SCADA-related RFPs (Request for Proposals) across multiple states without paying for subscription services like BidPrime. The application focuses on water/wastewater, mining, and oil/gas industries, automatically scraping state procurement websites, filtering for SCADA-relevant opportunities, and sending notifications when new RFPs are found.

## Features

- **Multi-State Coverage**: Currently supports Arizona and New Mexico, with easy extensibility to Utah, Idaho, Illinois, Missouri, Iowa, and Indiana
- **Industry-Specific Filtering**: Specialized for water/wastewater, mining, and oil/gas SCADA opportunities
- **Intelligent Relevance Scoring**: Uses weighted keyword matching to identify the most relevant opportunities
- **Email Notifications**: Sends daily digests or real-time alerts for new RFPs
- **Flexible Configuration**: Customizable settings for scraping frequency, notification preferences, and industry focus
- **Command-Line Interface**: Simple commands for scraping, filtering, and notification

## Installation

### Prerequisites

- Python 3.6 or higher
- SQLite3
- Internet connection

### Required Python Packages

```bash
pip3 install beautifulsoup4 requests
```

### Setup

1. Clone or download the SCADA RFP Finder repository
2. Navigate to the project directory
3. Edit the `config.json` file to customize your settings (see Configuration section)
4. Run the test script to verify everything is working:

```bash
chmod +x test.sh
./test.sh
```

## Usage

SCADA RFP Finder provides a command-line interface with three main commands:

### 1. Scraping RFPs

To scrape RFPs from all configured states:

```bash
python3 cli.py scrape
```

To scrape RFPs from a specific state:

```bash
python3 cli.py scrape --state AZ
```

Additional options:
- `--db`: Specify the database file path (default: `rfps.db`)
- `--output`: Specify the directory to store RFP documents (default: `rfp_documents`)

### 2. Filtering RFPs

To process unfiltered RFPs and calculate their SCADA relevance:

```bash
python3 cli.py filter
```

Additional options:
- `--db`: Specify the database file path (default: `rfps.db`)
- `--keywords`: Specify a custom keywords file (JSON format)
- `--min-score`: Minimum relevance score to display (0-100, default: 50)

### 3. Sending Notifications

To send notifications for new RFPs:

```bash
python3 cli.py notify --email your@email.com
```

To send a daily digest:

```bash
python3 cli.py notify --email your@email.com --digest
```

Additional options:
- `--db`: Specify the database file path (default: `rfps.db`)
- `--config`: Specify a custom notification config file (JSON format)
- `--min-score`: Minimum relevance score for notifications (0-100, default: 50)

## Configuration

The `config.json` file contains all the configuration options for SCADA RFP Finder:

### Email Configuration

```json
"email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "your-email@gmail.com",
    "smtp_password": "your-app-password",
    "from_email": "your-email@gmail.com",
    "from_name": "SCADA RFP Finder",
    "recipients": ["recipient@example.com"]
}
```

For Gmail, you'll need to use an App Password instead of your regular password. See [Google's documentation](https://support.google.com/accounts/answer/185833) for details.

### Notification Configuration

```json
"notification": {
    "min_relevance_score": 50,
    "notification_frequency": "daily",
    "include_low_relevance": false
}
```

- `min_relevance_score`: Minimum score (0-100) for an RFP to trigger a notification
- `notification_frequency`: "daily" for daily digests or "realtime" for immediate notifications
- `include_low_relevance`: Whether to include low-relevance RFPs in notifications

### Scraping Configuration

```json
"scraping": {
    "states": ["AZ", "NM", "UT", "ID", "IL", "MO", "IA", "IN"],
    "frequency": "daily",
    "output_dir": "rfp_documents"
}
```

- `states`: List of state codes to scrape
- `frequency`: How often to run the scraper
- `output_dir`: Directory to store downloaded RFP documents

### Filtering Configuration

```json
"filtering": {
    "industry_focus": {
        "water_wastewater": true,
        "mining": true,
        "oil_gas": true
    },
    "keyword_weights": {
        "core_scada": 10,
        "water_wastewater": 5,
        "mining": 5,
        "oil_gas": 5,
        "communication": 3,
        "integration": 3,
        "project_types": 2,
        "service_types": 2
    }
}
```

- `industry_focus`: Enable/disable specific industries
- `keyword_weights`: Adjust the importance of different keyword categories

## Automation

To automate the RFP finding process, you can set up cron jobs to run the scraper and notification system regularly:

### Example Cron Jobs

Add these lines to your crontab (`crontab -e`):

```
# Run scraper daily at 6 AM
0 6 * * * cd /path/to/rfp_project && python3 cli.py scrape

# Run filter after scraper completes
30 6 * * * cd /path/to/rfp_project && python3 cli.py filter

# Send daily digest at 8 AM
0 8 * * * cd /path/to/rfp_project && python3 cli.py notify --email your@email.com --digest
```

## Extending the System

### Adding New States

To add support for additional states:

1. Create a new scraper class in the `scraper/scrapers` directory
2. Inherit from the `BaseScraper` class
3. Implement the required methods
4. Register the scraper in `scraper/scrapers/__init__.py`
5. Update the main.py file to import and register the new scraper

### Customizing Keywords

To customize the SCADA keywords:

1. Create a JSON file with your custom keywords
2. Use the `--keywords` option with the filter command

## Troubleshooting

### Common Issues

1. **No RFPs Found**: 
   - Check internet connection
   - Verify the state procurement websites are accessible
   - The website structure may have changed, requiring scraper updates

2. **Email Notifications Not Sending**:
   - Check SMTP server settings
   - Verify email credentials
   - For Gmail, ensure you're using an App Password

3. **Low Relevance Scores**:
   - Adjust keyword weights in the configuration
   - Add additional industry-specific keywords

### Logs

The application logs are stored in:
- `rfp_scraper.log` for the scraper
- `scada_rfp_finder.log` for the CLI

## Database Schema

The SQLite database (`rfps.db`) contains a single table with the following schema:

```sql
CREATE TABLE RFPs (
    id TEXT PRIMARY KEY,
    state TEXT,
    title TEXT,
    description TEXT,
    publication_date DATE,
    due_date DATE,
    category TEXT,
    agency TEXT,
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    url TEXT,
    document_urls TEXT,
    scada_relevance_score INTEGER,
    is_water_wastewater BOOLEAN,
    is_mining BOOLEAN,
    is_oil_gas BOOLEAN,
    processed BOOLEAN,
    notified BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

You can query the database directly using SQLite:

```bash
sqlite3 rfps.db 'SELECT id, state, title, scada_relevance_score FROM RFPs ORDER BY scada_relevance_score DESC;'
```

## Support and Contributions

For support or to contribute to the project, please contact the developer.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
