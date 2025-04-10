from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from webapp import db
from webapp.models import User
from webapp.forms import LoginForm, RegistrationForm, ProfileForm
from datetime import datetime

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.verify_password(password):
            login_user(user, remember=remember)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        
        flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password=password,
            created_at=datetime.utcnow()
        )
        
        # Make first user an admin
        if User.query.count() == 0:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    form = ProfileForm(current_user)
    if request.method == 'GET':
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        email = form.email.data
        current_password = form.current_password.data
        new_password = form.new_password.data
        
        # Update email
        if email and email != current_user.email:
            current_user.email = email
            db.session.commit()
            flash('Email updated.', 'success')
        
        # Update password
        if current_password and new_password:
            if not current_user.verify_password(current_password):
                flash('Current password is incorrect.', 'danger')
            else:
                current_user.password = new_password
                db.session.commit()
                flash('Password updated.', 'success')
        
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)
