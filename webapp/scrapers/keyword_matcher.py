"""
Keyword Matcher for SCADA RFPs

This module provides functions to analyze text and determine if it's related to SCADA systems,
particularly for water/wastewater, mining, and oil/gas industries.
"""

import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SCADA-related keywords
SCADA_KEYWORDS = [
    # Core SCADA terms
    'scada', 'supervisory control and data acquisition', 'plc', 'programmable logic controller',
    'hmi', 'human machine interface', 'rtu', 'remote terminal unit', 'dcs', 'distributed control system',
    
    # Control system components
    'control system', 'automation system', 'industrial automation', 'process control',
    'i/o module', 'input/output module', 'telemetry', 'modbus', 'profibus',
    'ethernet/ip', 'dnp3', 'opc', 'opc ua', 'industrial network',
    'fieldbus', 'wireless sensor', 'remote access', 'remote control', 'control software',
    'monitoring software', 'historian', 'data historian', 'trending', 'alarm management',
    'event management', 'reporting system', 'dashboard', 'visualization', 'flow control',
    'level control', 'pressure control', 'temperature control', 'pump control', 'motor control',
    'valve control', 'actuator', 'vfd', 'variable frequency drive', 'system integration',
    'control integration', 'scada integration', 'plc integration', 'automation integration', 'industrial integration',
    'iot integration', 'iiot', 'control system upgrade', 'scada upgrade', 'plc upgrade',
    'automation upgrade', 'control system maintenance', 'scada maintenance', 'plc programming', 'hmi programming',
    
    # Additional SCADA terms
    'hvac system scada', 'hvac scada', 'building automation', 'building management system', 'bms',
    'facility management system', 'fms', 'energy management system', 'ems', 'smart building',
    'industrial control', 'industrial automation', 'automation project', 'control project',
    'instrumentation', 'sensors', 'controllers', 'remote monitoring', 'remote control',
    'data acquisition', 'data collection', 'data logging', 'data analysis', 'data visualization',
    'control panel', 'control cabinet', 'control room', 'control center', 'operations center',
    'automation software', 'control software', 'monitoring software', 'scada software', 'plc software',
    'hmi software', 'industrial software', 'industrial network', 'industrial communication',
    'industrial protocol', 'industrial ethernet', 'industrial wireless', 'industrial iot'
]

# Water/wastewater-specific keywords
WATER_WASTEWATER_KEYWORDS = [
    # Water treatment
    'water treatment', 'wastewater treatment', 'water plant', 'wastewater plant', 'sewage treatment',
    'potable water', 'drinking water', 'water distribution', 'water utility', 'water system',
    'water monitoring', 'water quality', 'water management', 'water control', 'water automation',
    
    # Wastewater treatment
    'sewage', 'effluent', 'influent', 'sludge', 'biosolids',
    'aeration', 'clarifier', 'digester', 'filtration', 'disinfection',
    'lift station', 'pump station', 'booster station', 'collection system', 'distribution system',
    
    # Water-specific equipment
    'flow meter', 'level sensor', 'pressure sensor', 'chlorine analyzer', 'turbidity meter',
    'ph sensor', 'conductivity sensor', 'dissolved oxygen', 'chemical dosing', 'chemical feed',
    'backwash', 'membrane', 'reverse osmosis', 'uv disinfection', 'ozone',
    
    # Water-specific processes
    'chlorination', 'dechlorination', 'coagulation', 'flocculation', 'sedimentation',
    'filtration', 'disinfection', 'softening', 'dewatering', 'thickening',
    'nitrification', 'denitrification', 'biological treatment', 'chemical treatment', 'physical treatment',
    
    # Water-specific regulations
    'clean water act', 'safe drinking water act', 'npdes', 'epa', 'compliance',
    'regulatory', 'permit', 'discharge', 'monitoring', 'reporting',
    
    # Additional water/wastewater terms
    'water resources', 'water conservation', 'water reuse', 'water reclamation', 'water recycling',
    'water infrastructure', 'water facilities', 'water operations', 'water maintenance', 'water engineering',
    'water project', 'wastewater project', 'water treatment project', 'wastewater treatment project',
    'water control system', 'water monitoring system', 'water management system', 'water scada',
    'wastewater scada', 'water plc', 'wastewater plc', 'water automation', 'wastewater automation'
]

# Mining-specific keywords
MINING_KEYWORDS = [
    # Mining operations
    'mining', 'mine', 'mineral', 'ore', 'extraction',
    'underground mining', 'surface mining', 'open pit', 'quarry', 'excavation',
    'drilling', 'blasting', 'crushing', 'grinding', 'milling',
    'beneficiation', 'concentration', 'leaching', 'flotation', 'smelting',
    
    # Mining equipment
    'conveyor', 'crusher', 'mill', 'screen', 'classifier',
    'thickener', 'filter', 'dryer', 'feeder', 'hopper',
    'loader', 'haul truck', 'excavator', 'dragline', 'shovel',
    'ventilation', 'dewatering', 'tailings', 'slurry', 'stockpile',
    
    # Mining-specific monitoring
    'slope monitoring', 'ground control', 'roof control', 'gas detection', 'dust monitoring',
    'ventilation monitoring', 'water management', 'tailings management', 'environmental monitoring', 'safety system',
    
    # Mining-specific processes
    'heap leaching', 'in-situ leaching', 'solvent extraction', 'electrowinning', 'carbon adsorption',
    'gravity separation', 'magnetic separation', 'electrostatic separation', 'froth flotation', 'dense media separation',
    
    # Mining-specific minerals
    'coal', 'gold', 'silver', 'copper', 'iron',
    'zinc', 'lead', 'nickel', 'uranium', 'bauxite',
    'phosphate', 'potash', 'limestone', 'sand', 'gravel',
    
    # Additional mining terms
    'mining automation', 'mine automation', 'mining control', 'mine control', 'mining scada',
    'mine scada', 'mining plc', 'mine plc', 'mining monitoring', 'mine monitoring',
    'mining operations', 'mine operations', 'mining management', 'mine management',
    'mining project', 'mine project', 'mining system', 'mine system', 'mining technology',
    'mine technology', 'mining equipment', 'mine equipment', 'mining infrastructure', 'mine infrastructure'
]

# Oil and gas-specific keywords
OIL_GAS_KEYWORDS = [
    # Oil and gas operations
    'oil', 'gas', 'petroleum', 'hydrocarbon', 'crude',
    'upstream', 'midstream', 'downstream', 'exploration', 'production',
    'drilling', 'well', 'reservoir', 'formation', 'completion',
    'workover', 'stimulation', 'fracturing', 'fracking', 'enhanced recovery',
    
    # Oil and gas equipment
    'wellhead', 'christmas tree', 'bop', 'blowout preventer', 'separator',
    'compressor', 'pump jack', 'artificial lift', 'pipeline', 'gathering system',
    'processing plant', 'refinery', 'storage tank', 'terminal', 'lng',
    
    # Oil and gas-specific monitoring
    'well monitoring', 'production monitoring', 'pipeline monitoring', 'leak detection', 'cathodic protection',
    'flow measurement', 'pressure monitoring', 'temperature monitoring', 'tank level', 'gas detection',
    
    # Oil and gas-specific processes
    'separation', 'dehydration', 'sweetening', 'stabilization', 'fractionation',
    'cracking', 'reforming', 'alkylation', 'isomerization', 'polymerization',
    
    # Oil and gas-specific products
    'crude oil', 'natural gas', 'condensate', 'ngl', 'lpg',
    'gasoline', 'diesel', 'jet fuel', 'kerosene', 'lubricant',
    
    # Additional oil and gas terms
    'oil and gas automation', 'petroleum automation', 'oil and gas control', 'petroleum control',
    'oil and gas scada', 'petroleum scada', 'oil and gas plc', 'petroleum plc',
    'oil and gas monitoring', 'petroleum monitoring', 'oil and gas operations', 'petroleum operations',
    'oil and gas management', 'petroleum management', 'oil and gas project', 'petroleum project',
    'oil and gas system', 'petroleum system', 'oil and gas technology', 'petroleum technology',
    'oil and gas equipment', 'petroleum equipment', 'oil and gas infrastructure', 'petroleum infrastructure'
]

# HVAC and building automation keywords
HVAC_KEYWORDS = [
    'hvac', 'heating', 'ventilation', 'air conditioning', 'building automation',
    'building management', 'bms', 'building control', 'facility management', 'energy management',
    'temperature control', 'humidity control', 'air quality', 'climate control', 'environmental control',
    'smart building', 'intelligent building', 'building system', 'building technology', 'building infrastructure',
    'hvac control', 'hvac monitoring', 'hvac automation', 'hvac management', 'hvac project',
    'hvac system', 'hvac technology', 'hvac equipment', 'hvac infrastructure', 'hvac scada'
]

def analyze_text(title, description=''):
    """
    Analyze text to determine if it's related to SCADA systems and which industry it belongs to
    
    Args:
        title: Title of the RFP
        description: Description of the RFP (optional)
    
    Returns:
        Dictionary with analysis results
    """
    # Combine title and description for analysis
    text = (title + ' ' + description).lower()
    
    # Count occurrences of SCADA-related keywords
    scada_count = 0
    for keyword in SCADA_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        matches = re.findall(pattern, text)
        scada_count += len(matches)
    
    # Count occurrences of industry-specific keywords
    water_count = 0
    for keyword in WATER_WASTEWATER_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        matches = re.findall(pattern, text)
        water_count += len(matches)
    
    mining_count = 0
    for keyword in MINING_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        matches = re.findall(pattern, text)
        mining_count += len(matches)
    
    oil_gas_count = 0
    for keyword in OIL_GAS_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        matches = re.findall(pattern, text)
        oil_gas_count += len(matches)
        
    hvac_count = 0
    for keyword in HVAC_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        matches = re.findall(pattern, text)
        hvac_count += len(matches)
    
    # Calculate relevance score (0-100)
    # Base score from SCADA keywords
    relevance_score = min(100, scada_count * 10)
    
    # Boost score if industry-specific keywords are found
    industry_count = water_count + mining_count + oil_gas_count + hvac_count
    industry_boost = min(50, industry_count * 5)
    relevance_score = min(100, relevance_score + industry_boost)
    
    # Special case: If "SCADA" appears explicitly in the title, ensure it's marked as related
    if re.search(r'\bscada\b', title.lower()):
        relevance_score = max(relevance_score, 50)
    
    # Lower the threshold for determining if SCADA-related
    is_scada_related = relevance_score >= 20  # Reduced from 30 to 20
    
    # Determine industry
    is_water_wastewater = water_count >= 1  # Reduced from 2 to 1
    is_mining = mining_count >= 1  # Reduced from 2 to 1
    is_oil_gas = oil_gas_count >= 1  # Reduced from 2 to 1
    is_hvac = hvac_count >= 1  # New category
    
    # Return analysis results
    return {
        'is_scada_related': is_scada_related,
        'relevance_score': relevance_score,
        'is_water_wastewater': is_water_wastewater,
        'is_mining': is_mining,
        'is_oil_gas': is_oil_gas,
        'is_hvac': is_hvac,
        'scada_count': scada_count,
        'water_count': water_count,
        'mining_count': mining_count,
        'oil_gas_count': oil_gas_count,
        'hvac_count': hvac_count
    }
