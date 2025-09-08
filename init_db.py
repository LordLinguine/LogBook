from app import create_app, db
from app.models import User, Entry

# Create the Flask app
app = create_app()

# Open an application context (needed for DB ops)
with app.app_context():
    db.create_all()
    print("Database Created (logbook.db)")