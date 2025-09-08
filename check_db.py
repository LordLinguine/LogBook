from app import create_app, db
from app.models import User, Entry

app = create_app()

with app.app_context():
    # Fetch all users
    users = User.query.all()
    print("\n=== USERS ===")
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Password: {u.password}")

    # Fetch all entries (will be empty for now)
    entries = Entry.query.all()
    print("\n=== Entries ===")
    for e in entries:
        print(f"ID: {e.id}, User ID: {e.user_id}, Title: {e.title}, Body: {e.content}, Date: {e.date_posted}, Tags: {e.tags}")