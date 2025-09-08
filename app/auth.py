from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from . import db
from .models import User
import re



auth = Blueprint("auth", __name__)

def is_password_strong(password):
    """ Check if password meets strength requirements. """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

# Register
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Chech if password matches
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for("auth.register"))
        
        # Validate password strength
        valid, message = is_password_strong(password)
        if not valid:
            flash(message, "error")
            return redirect(url_for("auth.register"))
        
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("register.html")

# Login
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")

# Logout
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))

