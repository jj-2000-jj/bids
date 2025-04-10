import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from webapp import create_app, db
from webapp.models import RFP, State

# Create a more comprehensive list of SCADA keywords
SCADA_KEYWORDS = [
    # Core SCADA terms
    'scada', 'supervisory control', 'data acquisition', 'remote monitoring', 'control system',
    'automation system', 'industrial automation', 'process automation', 'automated control',
    
    # Controllers and hardware
    'plc', 'programmable logic controller', 'rtu', 'remote terminal unit', 'dcs',
    'distributed control system', 'hmi', 'human machine interface', 'human-machine interface',
    'control panel', 'control cabinet', 'i/o module', 'input/output module',
    
    # Communication and networking
    'telemetry', 'modbus', 'profibus', 'ethernet/ip', 'dnp3', 'opc', 'opc ua',
    'industrial network', 'fieldbus', 'wireless sensor', 'remote access', 'remote control',
    
    # Software and systems
    'control software', 'monitoring software', 'historian', 'data historian', 'trending',
    'alarm management', 'event management', 'reporting system', 'dashboard', 'visualization',
    
    # Industry-specific terms
    'flow control', 'level control', 'pressure control', 'temperature control',
    'pump control', 'motor control', 'valve control', 'actuator', 'vfd', 'variable frequency drive',
    
    # Integration terms
    'system integration', 'control integration', 'scada integration', 'plc integration',
    'automation integration', 'industrial integration', 'iot integration', 'iiot',
    
    # Services
    'control system upgrade', 'scada upgrade', 'plc upgrade', 'automation upgrade',
    'control system maintenance', 'scada maintenance', 'plc programming', 'hmi programming',
    'control system design', 'automation design', 'system implementation'
]

# Water/wastewater specific keywords
WATER_KEYWORDS = [
    # General water terms
    'water', 'wastewater', 'sewage', 'effluent', 'potable', 'non-potable', 'drinking water',
    'water utility', 'water district', 'water authority', 'water department', 'water resources',
    
    # Treatment processes
    'treatment plant', 'water treatment', 'wastewater treatment', 'sewage treatment',
    'filtration', 'disinfection', 'chlorination', 'dechlorination', 'uv treatment',
    'reverse osmosis', 'ro system', 'membrane filtration', 'activated sludge',
    
    # Infrastructure
    'pump station', 'lift station', 'booster station', 'distribution system',
    'collection system', 'water main', 'sewer main', 'force main', 'gravity main',
    'reservoir', 'water storage', 'tank', 'well', 'groundwater', 'surface water',
    
    # Equipment
    'water pump', 'submersible pump', 'chemical feed', 'chemical dosing', 'mixer',
    'aerator', 'blower', 'clarifier', 'sedimentation', 'flocculation', 'backwash',
    
    # Monitoring
    'flow meter', 'level sensor', 'pressure sensor', 'turbidity', 'ph monitoring',
    'conductivity', 'dissolved oxygen', 'chlorine analyzer', 'water quality',
    'leak detection', 'overflow monitoring', 'flood monitoring'
]

# Mining specific keywords
MINING_KEYWORDS = [
    # General mining terms
    'mining', 'mine', 'mineral', 'ore', 'extraction', 'excavation', 'quarry',
    'underground mining', 'surface mining', 'open pit', 'open cast', 'strip mining',
    
    # Mining processes
    'drilling', 'blasting', 'crushing', 'grinding', 'milling', 'screening',
    'conveying', 'hauling', 'loading', 'unloading', 'stockpile', 'tailings',
    'leaching', 'flotation', 'separation', 'beneficiation', 'concentration',
    
    # Mining equipment
    'excavator', 'loader', 'haul truck', 'drill rig', 'longwall', 'continuous miner',
    'crusher', 'mill', 'conveyor', 'hopper', 'feeder', 'classifier', 'cyclone',
    
    # Monitoring and safety
    'gas detection', 'methane monitoring', 'ventilation monitoring', 'dust monitoring',
    'slope monitoring', 'ground movement', 'subsidence', 'tailings monitoring',
    'water management', 'dewatering', 'acid mine drainage', 'reclamation'
]

# Oil and gas specific keywords
OIL_GAS_KEYWORDS = [
    # General oil and gas terms
    'oil', 'gas', 'petroleum', 'hydrocarbon', 'crude', 'natural gas', 'lng',
    'upstream', 'midstream', 'downstream', 'exploration', 'production', 'e&p',
    
    # Infrastructure
    'pipeline', 'gathering system', 'transmission line', 'distribution line',
    'compressor station', 'pump station', 'terminal', 'refinery', 'processing plant',
    'storage tank', 'tank farm', 'wellhead', 'wellsite', 'platform', 'offshore',
    
    # Processes
    'drilling', 'completion', 'fracking', 'fracturing', 'stimulation', 'workover',
    'production', 'separation', 'processing', 'treating', 'compression', 'liquefaction',
    'regasification', 'blending', 'cracking', 'reforming', 'distillation',
    
    # Equipment
    'wellhead', 'christmas tree', 'bop', 'blowout preventer', 'separator',
    'treater', 'heater', 'dehydrator', 'compressor', 'pump', 'valve', 'actuator',
    'meter', 'pig launcher', 'pig receiver', 'scraper', 'filter',
    
    # Monitoring
    'flow monitoring', 'pressure monitoring', 'temperature monitoring', 'level monitoring',
    'leak detection', 'corrosion monitoring', 'cathodic protection', 'pig tracking',
    'gas detection', 'h2s monitoring', 'emissions monitoring', 'flare monitoring'
]

def create_test_rfps():
    """Create test RFPs with SCADA-related content for testing"""
    app = create_app()
    
    with app.app_context():
        # Check if we already have RFPs
        if RFP.query.count() > 0:
            print(f"Database already contains {RFP.query.count()} RFPs. Skipping test data creation.")
            return
        
        print("Creating test SCADA RFPs for demonstration...")
        
        # Water/Wastewater SCADA RFPs
        water_rfps = [
            {
                "id": "AZ-20250401-0001",
                "title": "SCADA System Upgrade for Phoenix Water Treatment Plant",
                "description": "The City of Phoenix is seeking proposals for upgrading the existing SCADA system at the main water treatment plant. The project includes replacing PLCs, upgrading HMI software, implementing new RTUs for remote pump stations, and integrating flow monitoring and chemical dosing control systems.",
                "state": "AZ",
                "agency": "City of Phoenix Water Services Department",
                "publication_date": datetime.strptime("2025-04-01", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-05-15", "%Y-%m-%d").date(),
                "url": "https://example.com/phoenix-water-scada",
                "scada_relevance_score": 95,
                "is_water_wastewater": True,
                "is_mining": False,
                "is_oil_gas": False
            },
            {
                "id": "NM-20250402-0002",
                "title": "Wastewater Treatment Plant Automation and Control System",
                "description": "The City of Albuquerque is requesting proposals for the design and implementation of a comprehensive automation and control system for the Southside Wastewater Treatment Plant. The project includes PLC programming, SCADA system development, HMI design, and integration with existing telemetry systems for lift stations and pump controls.",
                "state": "NM",
                "agency": "Albuquerque Bernalillo County Water Utility Authority",
                "publication_date": datetime.strptime("2025-04-02", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-05-20", "%Y-%m-%d").date(),
                "url": "https://example.com/abq-wastewater-automation",
                "scada_relevance_score": 90,
                "is_water_wastewater": True,
                "is_mining": False,
                "is_oil_gas": False
            },
            {
                "id": "UT-20250403-0003",
                "title": "Water Distribution System Monitoring and Control",
                "description": "Salt Lake City Public Utilities is seeking qualified vendors to provide a supervisory control and data acquisition (SCADA) system for monitoring and controlling the city's water distribution network. The system must integrate with existing pressure sensors, flow meters, and valve actuators while providing real-time data visualization and alarm management.",
                "state": "UT",
                "agency": "Salt Lake City Public Utilities",
                "publication_date": datetime.strptime("2025-04-03", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-05-25", "%Y-%m-%d").date(),
                "url": "https://example.com/slc-water-distribution-scada",
                "scada_relevance_score": 85,
                "is_water_wastewater": True,
                "is_mining": False,
                "is_oil_gas": False
            }
        ]
        
        # Mining SCADA RFPs
        mining_rfps = [
            {
                "id": "AZ-20250404-0004",
                "title": "Copper Mine Process Control System Replacement",
                "description": "A major copper mining operation in Arizona is seeking proposals for replacing the existing distributed control system (DCS) with a modern PLC-based SCADA system. The project includes control system design, PLC programming, HMI development, and integration with crushing, grinding, flotation, and tailings management processes.",
                "state": "AZ",
                "agency": "Resolution Copper Mining LLC",
                "publication_date": datetime.strptime("2025-04-04", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-05-30", "%Y-%m-%d").date(),
                "url": "https://example.com/copper-mine-control-system",
                "scada_relevance_score": 88,
                "is_water_wastewater": False,
                "is_mining": True,
                "is_oil_gas": False
            },
            {
                "id": "ID-20250405-0005",
                "title": "Underground Mine Ventilation Monitoring System",
                "description": "Hecla Mining Company is requesting proposals for an automated ventilation monitoring and control system for the Lucky Friday Mine. The system must include gas detection, airflow monitoring, fan control, and integration with the mine's existing SCADA infrastructure. Real-time data collection and reporting capabilities are required.",
                "state": "ID",
                "agency": "Hecla Mining Company",
                "publication_date": datetime.strptime("2025-04-05", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-06-05", "%Y-%m-%d").date(),
                "url": "https://example.com/mine-ventilation-monitoring",
                "scada_relevance_score": 82,
                "is_water_wastewater": False,
                "is_mining": True,
                "is_oil_gas": False
            }
        ]
        
        # Oil and Gas SCADA RFPs
        oil_gas_rfps = [
            {
                "id": "NM-20250406-0006",
                "title": "Permian Basin Well Site Automation and Monitoring",
                "description": "A major oil and gas producer is seeking proposals for implementing remote monitoring and control systems for multiple well sites in the Permian Basin. The project includes RTU installation, wireless telemetry, integration with existing SCADA infrastructure, and development of mobile access capabilities for field operators.",
                "state": "NM",
                "agency": "Devon Energy Corporation",
                "publication_date": datetime.strptime("2025-04-06", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-06-10", "%Y-%m-%d").date(),
                "url": "https://example.com/permian-well-automation",
                "scada_relevance_score": 92,
                "is_water_wastewater": False,
                "is_mining": False,
                "is_oil_gas": True
            },
            {
                "id": "UT-20250407-0007",
                "title": "Natural Gas Compressor Station Control System",
                "description": "Dominion Energy is requesting proposals for upgrading the control systems at three natural gas compressor stations in Utah. The project includes PLC replacement, HMI development, integration with gas flow measurement, compressor control, and emissions monitoring systems. The solution must comply with API 1165 and other relevant industry standards.",
                "state": "UT",
                "agency": "Dominion Energy",
                "publication_date": datetime.strptime("2025-04-07", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-06-15", "%Y-%m-%d").date(),
                "url": "https://example.com/gas-compressor-control",
                "scada_relevance_score": 87,
                "is_water_wastewater": False,
                "is_mining": False,
                "is_oil_gas": True
            },
            {
                "id": "IL-20250408-0008",
                "title": "Pipeline SCADA System Modernization",
                "description": "Enbridge is seeking qualified vendors to modernize the SCADA system for a crude oil pipeline network in Illinois. The project includes upgrading RTUs, implementing leak detection algorithms, enhancing cybersecurity measures, and developing a new control center HMI. The system must comply with API 1168 and PHMSA requirements.",
                "state": "IL",
                "agency": "Enbridge Inc.",
                "publication_date": datetime.strptime("2025-04-08", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-06-20", "%Y-%m-%d").date(),
                "url": "https://example.com/pipeline-scada-modernization",
                "scada_relevance_score": 94,
                "is_water_wastewater": False,
                "is_mining": False,
                "is_oil_gas": True
            }
        ]
        
        # Multi-industry SCADA RFPs
        multi_industry_rfps = [
            {
                "id": "MO-20250409-0009",
                "title": "Industrial Control Systems Cybersecurity Assessment",
                "description": "The State of Missouri is seeking proposals for cybersecurity assessment services for industrial control systems and SCADA networks across multiple critical infrastructure sectors including water utilities, transportation, and energy. The assessment must include vulnerability scanning, penetration testing, and remediation recommendations.",
                "state": "MO",
                "agency": "Missouri Office of Administration",
                "publication_date": datetime.strptime("2025-04-09", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-06-25", "%Y-%m-%d").date(),
                "url": "https://example.com/ics-cybersecurity-assessment",
                "scada_relevance_score": 80,
                "is_water_wastewater": True,
                "is_mining": False,
                "is_oil_gas": True
            },
            {
                "id": "IA-20250410-0010",
                "title": "SCADA System Integration Services",
                "description": "The Iowa Department of Natural Resources is requesting proposals for SCADA system integration services to support various environmental monitoring and control applications. Projects may include water quality monitoring, wastewater treatment plant automation, and integration with the state's environmental database systems.",
                "state": "IA",
                "agency": "Iowa Department of Natural Resources",
                "publication_date": datetime.strptime("2025-04-10", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-06-30", "%Y-%m-%d").date(),
                "url": "https://example.com/iowa-scada-integration",
                "scada_relevance_score": 85,
                "is_water_wastewater": True,
                "is_mining": False,
                "is_oil_gas": False
            },
            {
                "id": "IN-20250411-0011",
                "title": "Industrial Automation and Control Systems Master Agreement",
                "description": "The State of Indiana is establishing a master agreement for industrial automation and control systems products and services. Categories include PLC hardware and programming, HMI development, SCADA software, network infrastructure, and system integration services for various state agencies and public utilities.",
                "state": "IN",
                "agency": "Indiana Department of Administration",
                "publication_date": datetime.strptime("2025-04-11", "%Y-%m-%d").date(),
                "due_date": datetime.strptime("2025-07-05", "%Y-%m-%d").date(),
                "url": "https://example.com/indiana-automation-master-agreement",
                "scada_relevance_score": 90,
                "is_water_wastewater": True,
                "is_mining": True,
                "is_oil_gas": True
            }
        ]
        
        # Combine all RFPs
        all_rfps = water_rfps + mining_rfps + oil_gas_rfps + multi_industry_rfps
        
        # Add RFPs to database
        for rfp_data in all_rfps:
            rfp = RFP(
                id=rfp_data["id"],
                title=rfp_data["title"],
                description=rfp_data["description"],
                state=rfp_data["state"],
                agency=rfp_data["agency"],
                publication_date=rfp_data["publication_date"],
                due_date=rfp_data["due_date"],
                url=rfp_data["url"],
                scada_relevance_score=rfp_data["scada_relevance_score"],
                is_water_wastewater=rfp_data["is_water_wastewater"],
                is_mining=rfp_data["is_mining"],
                is_oil_gas=rfp_data["is_oil_gas"],
                created_at=datetime.utcnow()
            )
            db.session.add(rfp)
        
        # Commit changes
        db.session.commit()
        
        print(f"Successfully created {len(all_rfps)} test SCADA RFPs.")

if __name__ == "__main__":
    create_test_rfps()
