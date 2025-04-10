from webapp import db
from webapp.models import State

# Initialize states
states = [
    {"code": "AZ", "name": "Arizona", "enabled": True},
    {"code": "NM", "name": "New Mexico", "enabled": True},
    {"code": "UT", "name": "Utah", "enabled": False},
    {"code": "ID", "name": "Idaho", "enabled": False},
    {"code": "IL", "name": "Illinois", "enabled": False},
    {"code": "MO", "name": "Missouri", "enabled": False},
    {"code": "IA", "name": "Iowa", "enabled": False},
    {"code": "IN", "name": "Indiana", "enabled": False}
]

# Add states to database
for state_data in states:
    state = State.query.get(state_data["code"])
    if not state:
        state = State(
            code=state_data["code"],
            name=state_data["name"],
            enabled=state_data["enabled"]
        )
        db.session.add(state)

# Commit changes
db.session.commit()

print("States initialized successfully.")
