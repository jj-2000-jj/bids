"""
Run database migrations to update the RFP model with new fields.
"""

from webapp import create_app, db
from webapp.models.rfp import RFP
import sqlalchemy as sa
from sqlalchemy.sql import text

def run_migrations():
    """Run database migrations to add new fields to the RFP model."""
    app = create_app()
    
    with app.app_context():
        # Check if is_hvac column exists
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('rfp')]
        
        if 'is_hvac' not in columns:
            print("Adding is_hvac column to RFP table...")
            # Add is_hvac column
            db.session.execute(text('ALTER TABLE rfp ADD COLUMN is_hvac BOOLEAN DEFAULT FALSE'))
            db.session.commit()
            print("is_hvac column added successfully.")
        else:
            print("is_hvac column already exists.")
        
        print("Database migration completed successfully.")

if __name__ == "__main__":
    run_migrations()
