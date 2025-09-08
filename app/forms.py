from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from flask_login import current_user
from .models import User
from flask_wtf.file import FileField, FileAllowed

class EntryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    tags = StringField('Tags (comma-separated)')
    submit = SubmitField('Save')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_image = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    password = PasswordField('New Password', validators=[Length(min=6)], render_kw={"plceholder": "Leave blank to keep current"})
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Update')

    # Make sure username is unique
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('This username is already taken.')
            
    # Make sure email is unique
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email is already in use.')
            
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8),
        Regexp(
            r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$',
            message="Password must contain at least one uppercase letter, one number, and one special character."
        )
    ])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Sign Up")