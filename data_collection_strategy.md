# Data Collection Strategy for SCADA RFP Finder

## Overview
This document outlines the strategy for collecting RFP data from the eight target states (Arizona, New Mexico, Utah, Idaho, Illinois, Missouri, Iowa, and Indiana) to identify SCADA-related opportunities in water/wastewater, mining, and oil/gas industries.

## State-by-State Collection Approach

### Arizona
- **Primary Source**: Arizona State Procurement Office (https://spo.az.gov/contracts/upcoming-bids)
- **Collection Method**: Web scraping with pagination handling
- **Data Structure**: 
  - RFP ID
  - Title
  - Description
  - Publication Date
  - Due Date
  - Category
  - Agency
  - Contact Information
  - Document URLs
- **Special Considerations**: 
  - Requires search by keywords
  - Has filtering capabilities that can be leveraged
  - Documents are typically in PDF format

### New Mexico
- **Primary Sources**: 
  - General Services Department (https://www.generalservices.state.nm.us/state-purchasing/active-itbs-and-rfps/active-procurements/)
  - New Mexico Procurement Portal (https://biz.nm.gov/procurement-opportunities/)
  - Department of Transportation (https://www.dot.nm.gov/business-support/procurement-services/request-for-proposals-rfp/)
- **Collection Method**: Multi-source scraping with consolidation
- **Data Structure**: Same as Arizona
- **Special Considerations**:
  - Multiple sources need to be checked
  - Different formats across agencies
  - May require more complex parsing

### Utah
- **Primary Source**: Utah Division of Purchasing (https://purchasing.utah.gov/)
- **Collection Method**: Web scraping with authentication
- **Data Structure**: Same as Arizona
- **Special Considerations**:
  - May require account creation for full access
  - Has a structured data format that can be leveraged

### Idaho
- **Primary Source**: Idaho Division of Purchasing (https://purchasing.idaho.gov/)
- **Collection Method**: Web scraping with session management
- **Data Structure**: Same as Arizona
- **Special Considerations**:
  - Uses session cookies for navigation
  - Has a well-structured table format

### Illinois
- **Primary Source**: Illinois BidBuy (https://www.bidbuy.illinois.gov)
- **Collection Method**: Web scraping with advanced pagination
- **Data Structure**: Same as Arizona
- **Special Considerations**:
  - Complex site structure
  - May require handling of AJAX requests
  - Has advanced search capabilities

### Missouri
- **Primary Source**: MissouriBUYS (https://missouribuys.mo.gov/)
- **Collection Method**: Web scraping with authentication
- **Data Structure**: Same as Arizona
- **Special Considerations**:
  - Requires account creation
  - Has structured data export options

### Iowa
- **Primary Source**: Iowa Bid Opportunities (https://bidopportunities.iowa.gov/)
- **Collection Method**: Simple web scraping
- **Data Structure**: Same as Arizona
- **Special Considerations**:
  - Straightforward structure
  - Has search functionality that can be leveraged

### Indiana
- **Primary Source**: Indiana Department of Administration (https://www.in.gov/idoa/procurement/current-business-opportunities/)
- **Collection Method**: Web scraping with table parsing
- **Data Structure**: Same as Arizona
- **Special Considerations**:
  - Table-based layout
  - May require handling of document downloads

## Technical Implementation

### Scraping Framework
- **Primary Language**: Python
- **Libraries**:
  - BeautifulSoup/lxml for HTML parsing
  - Requests for basic HTTP requests
  - Selenium for JavaScript-heavy sites
  - PyPDF2 for PDF parsing
- **Architecture**: Modular design with state-specific modules

### Scraping Frequency
- **Standard Frequency**: Daily (overnight batch process)
- **High-Priority States**: Twice daily (morning and evening)
- **Considerations**:
  - Most procurement sites update on business days only
  - Updates typically occur during business hours
  - Some sites have scheduled maintenance windows

### Data Storage
- **Database**: SQLite (for simplicity and portability)
- **Schema**:
  ```
  RFPs (
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
- **Document Storage**: Local file system with organized directory structure by state/date

### Error Handling
- **Retry Logic**: Exponential backoff for failed requests
- **Logging**: Comprehensive logging of all operations
- **Monitoring**: Daily status reports
- **Failure Recovery**: Ability to resume from last successful operation

## Data Processing Pipeline

### 1. Collection
- Scheduled scraping jobs for each state
- Raw HTML/PDF storage for archival purposes
- Initial extraction of structured data

### 2. Normalization
- Standardize field formats across states
- Clean and normalize text fields
- Extract key information from descriptions
- Resolve agency names to standard forms

### 3. SCADA Relevance Filtering
- Apply keyword matching using SCADA keyword list
- Calculate relevance score based on keyword matches
- Categorize by industry (water/wastewater, mining, oil/gas)
- Flag high-priority opportunities

### 4. Deduplication
- Identify and merge duplicate entries
- Handle updates to existing opportunities
- Track changes to existing opportunities

### 5. Storage
- Store processed data in database
- Archive original documents
- Index for efficient searching

### 6. Notification
- Generate alerts for new relevant opportunities
- Format notifications with key details
- Deliver via preferred channel (email, dashboard, etc.)

## Challenges and Mitigations

### Site Structure Changes
- **Challenge**: Procurement sites may change structure without notice
- **Mitigation**: 
  - Implement robust error detection
  - Design scrapers to be resilient to minor changes
  - Set up monitoring to detect structural changes
  - Maintain contact information for manual intervention

### Access Restrictions
- **Challenge**: Some sites may implement anti-scraping measures
- **Mitigation**:
  - Respect robots.txt
  - Implement polite scraping with delays
  - Use rotating user agents
  - Consider API access where available

### Document Format Variations
- **Challenge**: RFP documents may be in various formats (PDF, Word, Excel)
- **Mitigation**:
  - Implement handlers for common document types
  - Extract text from PDFs using OCR when necessary
  - Fall back to metadata when full text extraction fails

### Data Quality
- **Challenge**: Inconsistent data quality across sources
- **Mitigation**:
  - Implement data validation rules
  - Flag suspicious entries for review
  - Continuously improve normalization rules

## Performance Considerations

### Scalability
- Design to handle growth to additional states
- Optimize database queries for larger datasets
- Implement caching for frequently accessed data

### Resource Usage
- Minimize bandwidth usage with conditional requests
- Schedule intensive operations during off-hours
- Implement resource throttling

### Response Time
- Prioritize processing of new opportunities
- Optimize notification pipeline for timely alerts
- Pre-compute common queries

## Next Steps

1. Develop proof-of-concept scrapers for two representative states
2. Implement core database schema
3. Create basic keyword matching algorithm
4. Test end-to-end pipeline with sample data
5. Refine and expand to all eight states
6. Implement notification system
7. Develop user interface for viewing and managing opportunities
