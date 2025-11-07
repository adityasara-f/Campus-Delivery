from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from app.models import User
import re

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('user', 'Student'), ('partner', 'Partner')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')
    
    def validate_password(self, password):
        pwd = password.data
        if len(pwd) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[0-9]', pwd):
            raise ValidationError('Password must contain at least one number.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
            raise ValidationError('Password must contain at least one special character.')
        if self.username.data and self.username.data.lower() in pwd.lower():
            raise ValidationError('Password cannot contain your username.')
        if self.email.data and self.email.data.lower() in pwd.lower():
            raise ValidationError('Password cannot contain your email.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ChangePasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
    
    def validate_new_password(self, new_password):
        pwd = new_password.data
        if len(pwd) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[0-9]', pwd):
            raise ValidationError('Password must contain at least one number.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
            raise ValidationError('Password must contain at least one special character.')
        if self.username.data and self.username.data.lower() in pwd.lower():
            raise ValidationError('Password cannot contain your username.')
        if self.email.data and self.email.data.lower() in pwd.lower():
            raise ValidationError('Password cannot contain your email.')
