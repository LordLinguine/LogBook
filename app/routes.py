from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask import jsonify, request, render_template
from . import db
from .models import Entry, Goal, GoalProgress
from app.models import Entry
from datetime import datetime, timedelta
from sqlalchemy import func
from .forms import EntryForm
from werkzeug.security import generate_password_hash
from .forms import ProfileForm
import os, secrets
from PIL import Image
from flask import current_app
import base64
from io import BytesIO


main = Blueprint("main", __name__)

UPLOAD_FOLDER = 'app/static/profile_pics'

def save_profile_image(form_image):
    # Generate random hex to avoid filename collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    # Resize image to 125x125
    output_size = (125, 125)
    i = Image.open(form_image)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def save_cover_image(form_image):
    """Save uploaded cover image and return filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/cover_pics', picture_fn)

    # Resize cover image (e.g., wide banner
    output_size = (1200, 300)
    i = Image.open(form_image)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@main.route("/")
def home():
    return render_template("home.html")

@main.route("/dashboard")
@login_required
def dashboard():
    tag = request.args.get('tag')
    date = request.args.get('date')
    search = request.args.get('q')  # <-- new search query
    page = 1  # always load first page for full dashboard

    query = Entry.query.filter_by(user_id=current_user.id)

    if tag:
        query = query.filter(func.lower(Entry.tags).contains(tag.lower()))
    if date:
        query = query.filter(db.func.date(Entry.date_posted) == date)
    if search:
        query = query.filter(
            (Entry.title.ilike(f"%{search}%")) | 
            (Entry.content.ilike(f"%{search}%"))
        )

    # Load first page only
    entries = query.order_by(Entry.date_posted.desc()).paginate(page=page, per_page=5)

    return render_template("dashboard.html", entries=entries, user=current_user)



@main.route("/add", methods=["GET", "POST"])
@login_required
def add_entry():
    form = EntryForm()
    
    if form.validate_on_submit():
        entry = Entry(
            title=form.title.data,
            content=form.content.data,
            tags=form.tags.data,
            author=current_user
        )
        db.session.add(entry)
        db.session.commit()
        flash("Entry added successfully!", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("add_entry.html", form=form)

@main.route("/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    if entry.author != current_user:
        flash("You don't have permission to edit this entry.")
        return redirect(url_for('main.dashboard'))

    form = EntryForm(obj=entry)

    if form.validate_on_submit():
        entry.title = form.title.data
        entry.content = form.content.data
        entry.tags = form.tags.data
        db.session.commit()
        flash("Entry updated successfully!", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("edit_entry.html", form=form, entry=entry)

@main.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)

    # Make sure the logged in user owns this entry
    if entry.user_id != current_user.id:
        flash("You don't have permission to delete this entry.")
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(entry)
    db.session.commit()
    flash("Entry deleted successfully!")
    return redirect(url_for('main.dashboard'))

@main.route("/entries_partial")
@login_required
def entries_partial():
    page = request.args.get("page", 1, type=int)
    tag_filter = request.args.get("tag")
    date_filter = request.args.get("date")

    query = Entry.query.filter_by(user_id=current_user.id)

    if tag_filter:
        query = query.filter(func.lower(Entry.tags).contains(tag_filter.lower()))
    if date_filter:
        query = query.filter(db.func.date(Entry.date_posted) == date_filter)

    # Paginate entries, 5 per page
    entries = query.order_by(Entry.date_posted.desc()).paginate(page=page, per_page=5, error_out=False)

    # Render partial template with only entries
    return render_template("partials/entries_list.html", entries=entries)

@main.route("/profile")
@login_required
def profile():
    # Give Recent 3 entries
    recent_entries = (
        Entry.query.filter_by(author=current_user)
        .order_by(Entry.date_posted.desc())
        .limit(3)
        .all()
    )

    # Stats
    total_entries = Entry.query.filter_by(author=current_user).count()

    # Most common tags (split by commas in case multiople tags in field)
    from collections import Counter
    all_tags = []
    for entry in current_user.entries:
        if entry.tags:
            all_tags.extend([tag.strip() for tag in entry.tags.split(",")])
    most_common_tags = [tag for tag, _ in Counter(all_tags).most_common(3)]

    return render_template(
        "profile.html",
        user=current_user,
        recent_entries=recent_entries,
        total_entries=total_entries,
        most_common_tags=most_common_tags
    )

@main.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        # Update username/email
        current_user.username = request.form["username"]
        current_user.email = request.form["email"]

        # Handle profile image upload
        if "profile_image" in request.files and request.files["profile_image"].filename != "":
            picture_file = save_profile_image(request.files["profile_image"])
            current_user.profile_image = picture_file

        # Handle cover image upload
        if "cover_image" in request.files and request.files["cover_image"].filename != "":
            cover_file = save_cover_image(request.files["cover_image"])
            current_user.cover_image = cover_file

        db.session.commit()
        flash("Your profile has been updated!", "success")
        return redirect(url_for("main.profile"))
    return render_template("edit_profile.html", user=current_user)

# List all goals for current user
@main.route("/goals")
@login_required
def list_goals():
    user_goals = Goal.query.filter_by(user_id=current_user.id).all()
    return render_template("goals/list.html", goals=user_goals)

# Add a new goal
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from . import db
from .models import Goal, GoalProgress

@main.route("/goals/add", methods=["GET", "POST"])
@login_required
def add_goal():
    if request.method == "POST":
        name = request.form.get("name").strip()
        unit = request.form.get("unit").strip() or None
        start_date = request.form.get("start_date")
        deadline = request.form.get("deadline")

        # Optional numeric fields
        start_value = request.form.get("start_value")
        start_value = float(start_value) if start_value else None
        target_value = request.form.get("target_value")
        target_value = float(target_value) if target_value else None

        # Dates
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.utcnow()
        deadline_obj = datetime.strptime(deadline, "%Y-%m-%d") if deadline else None

        # Create goal
        goal = Goal(
            user_id=current_user.id,
            name=name,
            start_value=start_value,
            target_value=target_value,
            unit=unit,
            start_date=start_date_obj,
            deadline=deadline_obj
        )
        db.session.add(goal)
        db.session.commit()

        # Automatically create first progress entry if start_value exists
        if start_value is not None:
            first_progress = GoalProgress(
                goal_id=goal.id,
                value=start_value,
                date=start_date_obj,
                note="Starting value"
            )
            db.session.add(first_progress)
            db.session.commit()

        flash("Goal created successfully!", "success")
        return redirect(url_for("main.goal_detail", goal_id=goal.id))

    current_date = datetime.today().strftime("%Y-%m-%d")
    return render_template("goals/add.html", current_date=current_date)


# Add progress to a goal
@main.route("/goals/<int:goal_id>/progress", methods=["POST"])
@login_required
def add_progress(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("Not authorized.", "danger")
        return redirect(url_for("main.list_goals"))

    value = request.form.get("value")
    note = request.form.get("note")

    new_progress = GoalProgress(
        goal_id=goal.id,
        value=float(value),
        note=note
    )
    db.session.add(new_progress)
    db.session.commit()
    flash("Progress added!", "success")
    return redirect(url_for("main.goal_detail", goal_id=goal.id))

# Goal detail page with stats + chart
# Goal detail page with stats + chart
@main.route("/goals/<int:goal_id>")
@login_required
def goal_detail(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("You don't have access to this goal.", "danger")
        return redirect(url_for("main.list_goals"))

    progresses = GoalProgress.query.filter_by(goal_id=goal.id).order_by(GoalProgress.date.asc()).all()

    # Dates and values for Chart.js
    dates = [p.date.strftime("%Y-%m-%d") for p in progresses]
    values = [p.value for p in progresses]

    # Include start_value as first point if exists
    if goal.start_value is not None:
        dates.insert(0, goal.start_date.strftime("%Y-%m-%d"))
        values.insert(0, goal.start_value)

    # --- ETA calculation (safe version) ---
    eta = None
    # Filter out None values
    numeric_values = [v for v in values if v is not None]
    numeric_progresses = [p for p in progresses if p.value is not None]

    # Only calculate ETA if we have numeric values and a target
    if len(numeric_values) >= 2 and goal.target_value is not None:
        days = [(numeric_progresses[i].date - numeric_progresses[i-1].date).days or 1 for i in range(1, len(numeric_progresses))]
        changes = [numeric_values[i] - numeric_values[i-1] for i in range(1, len(numeric_values))]

        total_days = sum(days)
        if total_days != 0:
            avg_daily_change = sum(changes) / total_days
            if avg_daily_change != 0:
                remaining = goal.target_value - numeric_values[-1]
                eta_days = int(remaining / avg_daily_change)
                last_date = numeric_progresses[-1].date
                eta_date = last_date + timedelta(days=eta_days)
                eta = eta_date.strftime("%Y-%m-%d")
    # --- End ETA calculation ---

    return render_template(
        "goals/detail.html",
        goal=goal,
        dates=dates,
        values=values,
        eta=eta,
        progress_entries=progresses
    )







# API endpoint for Chart.js
@main.route("/goals/<int:goal_id>/data")
@login_required
def goal_data(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        return jsonify({"error": "Not authorized"}), 403

    progresses = GoalProgress.query.filter_by(goal_id=goal.id).order_by(GoalProgress.date).all()
    return jsonify({
        "labels": [p.date.strftime("%Y-%m-%d") for p in progresses],
        "values": [p.value for p in progresses]
    })

@main.route("/goals/delete/<int:goal_id>", methods=["POST"])
@login_required
def delete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("You don't have permission to delete this goal.", "danger")
        return redirect(url_for("main.list_goals"))

    # Delete all related progress entries first
    GoalProgress.query.filter_by(goal_id=goal.id).delete()
    db.session.delete(goal)
    db.session.commit()
    flash("Goal deleted successfully!", "success")
    return redirect(url_for("main.list_goals"))

@main.route("/goals/<int:goal_id>/progress/add", methods=["GET", "POST"])
@login_required
def add_goal_progress(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if request.method == "POST":
        date_str = request.form.get("date")
        value = request.form.get("value")
        note = request.form.get("note")
        image_file = request.files.get("image")

        # Convert date and value safely
        entry_date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.utcnow()
        value = float(value) if value else None

        # Handle image
        filename = None
        if image_file and image_file.filename != "":
            image_folder = os.path.join(current_app.root_path, "static/progress_images")
            os.makedirs(image_folder, exist_ok=True)
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(image_file.filename)
            filename = random_hex + f_ext
            image_file.save(os.path.join(image_folder, filename))

        progress = GoalProgress(
            goal_id=goal.id,
            date=entry_date,
            value=value,
            note=note,
            image=filename
        )
        db.session.add(progress)
        db.session.commit()
        flash("Progress added!", "success")
        return redirect(url_for("main.goal_detail", goal_id=goal.id))

    return render_template("goals/add_progress.html", goal=goal)

@main.route("/edit_pictures_ajax", methods=["POST"])
@login_required
def edit_pictures_ajax():
    profile_image = request.files.get("profile_image")
    cover_image = request.files.get("cover_image")

    if profile_image:
        profile_filename = save_profile_image(profile_image)  # only 1 argument
        current_user.profile_image = profile_filename

    if cover_image:
        cover_filename = save_cover_image(cover_image)  # only 1 argument
        current_user.cover_image = cover_filename

    db.session.commit()

    return jsonify({
        "profile_image_url": url_for("static", filename="profile_pics/" + (current_user.profile_image or "default_profile.png")),
        "cover_image_url": url_for("static", filename="cover_pics/" + (current_user.cover_image or "default_cover.jpg")),
    })

@main.route("/upload_profile_image", methods=["POST"])
@login_required
def upload_profile_image():
    data = request.get_json()
    image_data = data["image"].split(",")[1]  # remove base64 prefix
    image_bytes = base64.b64decode(image_data)

    # Save to file system
    filename = f"profile_{current_user.id}.png"
    filepath = os.path.join(main.static_folder, "uploads", filename)

    img = Image.open(BytesIO(image_bytes))
    img.save(filepath, "PNG")

    # Update user profile
    current_user.profile_image = filename
    db.session.commit()

    return jsonify({"success": True})