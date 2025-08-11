from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user
from app import mongo, bcrypt
from app.models import User
from app.auth.forms import RegistrationForm, LoginForm

# Create a Blueprint for authentication routes
auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password and create the user document
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mongo.db.users.insert_one({
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_password
        })
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='Register', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Find user by email in the database
        user_data = mongo.db.users.find_one({'email': form.email.data})
        
        # Check if user exists and password is correct
        if user_data and bcrypt.check_password_hash(user_data['password'], form.password.data):
            user_obj = User(user_data)
            login_user(user_obj) # Log the user in
            
            # Redirect to the page they were trying to access, or dashboard
            next_page = request.args.get('next')
            flash('Login Successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
            
    return render_template('auth/login.html', title='Login', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))