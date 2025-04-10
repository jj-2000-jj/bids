from webapp import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    """User model for authentication and preferences"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Notification preferences
    notification_enabled = db.Column(db.Boolean, default=True)
    notification_frequency = db.Column(db.String(20), default='daily')  # immediate, daily, weekly
    min_relevance_score = db.Column(db.Integer, default=50)
    water_wastewater_enabled = db.Column(db.Boolean, default=True)
    mining_enabled = db.Column(db.Boolean, default=True)
    oil_gas_enabled = db.Column(db.Boolean, default=True)
    
    # Relationships
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Favorite(db.Model):
    """User's favorite RFPs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rfp_id = db.Column(db.String(50), db.ForeignKey('rfp.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'rfp_id', name='_user_rfp_uc'),)
    
    def __repr__(self):
        return f'<Favorite {self.user_id}:{self.rfp_id}>'

class Notification(db.Model):
    """Notifications for users about new RFPs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rfp_id = db.Column(db.String(50), db.ForeignKey('rfp.id'), nullable=False)
    read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.user_id}:{self.rfp_id}>'
