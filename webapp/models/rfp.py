from webapp import db
from datetime import datetime, date
from sqlalchemy.ext.hybrid import hybrid_property

class RFP(db.Model):
    """Request for Proposal model"""
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    state = db.Column(db.String(2), nullable=False)
    agency = db.Column(db.String(255))
    publication_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    url = db.Column(db.String(500))
    requirements = db.Column(db.Text)
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # SCADA relevance fields
    scada_relevance_score = db.Column(db.Integer, default=0)  # 0-100
    is_water_wastewater = db.Column(db.Boolean, default=False)
    is_mining = db.Column(db.Boolean, default=False)
    is_oil_gas = db.Column(db.Boolean, default=False)
    is_hvac = db.Column(db.Boolean, default=False)  # Added HVAC category
    
    # Relationships
    favorites = db.relationship('Favorite', backref='rfp', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='rfp', lazy='dynamic', cascade='all, delete-orphan')
    
    @hybrid_property
    def days_until_due(self):
        if not self.due_date:
            return None
        
        today = date.today()
        delta = self.due_date - today
        return delta.days
    
    def __repr__(self):
        return f'<RFP {self.id}: {self.title}>'

class State(db.Model):
    """State model for tracking enabled states"""
    code = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<State {self.code}: {self.name}>'

class ScraperLog(db.Model):
    """Log of scraper runs"""
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(2), nullable=False)
    municipality = db.Column(db.String(100), nullable=True)  # Added municipality field
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    success = db.Column(db.Boolean, default=False)
    rfps_found = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    duration = db.Column(db.Float)  # Added explicit duration column
    
    def __repr__(self):
        return f'<ScraperLog {self.id}: {self.state} at {self.start_time}>'

class SystemConfig(db.Model):
    """System configuration settings"""
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(500))
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'
