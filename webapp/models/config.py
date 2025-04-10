from .. import db

class State(db.Model):
    """Model for states covered by the application"""
    __tablename__ = 'states'
    
    code = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<State {self.code}: {self.name}>'


class UserStatePreference(db.Model):
    """Model for user state preferences"""
    __tablename__ = 'user_state_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    state_code = db.Column(db.String(2), db.ForeignKey('states.code'), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    
    # Relationships
    state = db.relationship('State')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'state_code', name='_user_state_uc'),)
    
    def __repr__(self):
        return f'<UserStatePreference User {self.user_id} - State {self.state_code}>'


class SystemConfig(db.Model):
    """Model for system configuration settings"""
    __tablename__ = 'system_config'
    
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'
