from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app import mongo

class RegistrationForm(FlaskForm):
    """Form for users to create a new account."""
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                             validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        """Check if the username is already in the database."""
        user = mongo.db.users.find_one({'username': username.data})
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        """Check if the email is already in the database."""
        user = mongo.db.users.find_one({'email': email.data})
        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    """Form for users to login."""
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    """Form for users to update their optional account details."""
    tradier_api_key = StringField('Tradier API Key', validators=[Optional(), Length(max=100)])
    tradier_account_number = StringField('Tradier Account Number', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Update Details')