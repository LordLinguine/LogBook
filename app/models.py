from . import db
from datetime import datetime
from flask_login import UserMixin

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) #Unique user id
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) 
    profile_image = db.Column(db.String(200), nullable=False, default="default.jpg")
    cover_image = db.Column(db.String(150), nullable=False, default="default_cover.jpg")
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    entries = db.relationship('Entry', backref='author', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"
    
# Log entry model
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.Column(db.String(100))

    def __repr__(self):
        return f"<Entry {self.title}>"
    
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    start_value = db.Column(db.Float, nullable=True)   # make optional
    target_value = db.Column(db.Float, nullable=True)  # make optional
    unit = db.Column(db.String(50), nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    progresses = db.relationship('GoalProgress', backref='goal', lazy=True)



class GoalProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("goal.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    value = db.Column(db.Float, nullable=True)  # allow optional
    note = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(120), nullable=True)

 


