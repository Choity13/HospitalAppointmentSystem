from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user
from extensions import db
from models import User, Notification
from utils.notifications import notify_otp
from utils.date_utils import get_current_time, tz
from datetime import datetime, timedelta
import bcrypt
import secrets
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name').strip()
        phone_number = request.form.get('phone_number').strip()
        carrier = request.form.get('carrier')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate phone number
        if not re.match(r'^8801[3-9][0-9]{8}$', phone_number):
            flash('Invalid phone number! Must be in format 8801XXXXXXXXX', 'danger')
            return render_template('auth/register.html')
        
        # Validate password
        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            flash('Password must be at least 8 characters, include 1 uppercase letter, and 1 digit!', 'danger')
            return render_template('auth/register.html')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('auth/register.html')
        
        # Check if phone number already exists
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered!', 'danger')
            return render_template('auth/register.html')
        
        # Hash password with bcrypt cost factor 12
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
        
        # Create user
        user = User(
            full_name=full_name,
            phone_number=phone_number,
            password_hash=hashed,
            role='patient',
            carrier=carrier
        )
        db.session.add(user)
        db.session.commit()
        
        # Log welcome notification
        notification = Notification(
            user_id=user.user_id,
            notif_type='booking',
            message='Welcome to Bangladesh Hospital System!'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        full_name = request.form.get('full_name').strip()
        phone_number = request.form.get('phone_number').strip()
        password = request.form.get('password')
        
        # Find user by phone number and full name
        user = User.query.filter_by(phone_number=phone_number, full_name=full_name).first()
        
        if not user:
            flash('Invalid credentials!', 'danger')
            return render_template('auth/login.html')
        
        # Check if account is locked
        now = get_current_time()
        if user.is_locked and user.lock_until_aware and user.lock_until_aware > now:
            flash(f'Account is locked! Try again after {user.lock_until_aware.strftime("%H:%M:%S")}', 'danger')
            return render_template('auth/login.html')
        
        # Unlock if lock time expired
        if user.is_locked and user.lock_until_aware and user.lock_until_aware <= now:
            user.is_locked = False
            user.lock_until = None
            db.session.commit()
        
        # Verify password
        if not user.check_password(password):
            flash('Invalid credentials!', 'danger')
            return render_template('auth/login.html')
        
        # Generate OTP
        otp = secrets.randbelow(900000) + 100000
        user.otp_code = str(otp)
        user.otp_expires_at = now + timedelta(minutes=10)
        user.otp_verified = False
        db.session.commit()
        
        # Send OTP notification
        notify_otp(user, otp)
        
        # Store pending user ID in session
        session['pending_user_id'] = user.user_id
        
        return redirect(url_for('auth.verify_otp'))
    
    return render_template('auth/login.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['pending_user_id'])
    if not user:
        session.pop('pending_user_id', None)
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Collect OTP code from form
        code = request.form.get('otp_code', '')
        print(f"=== RECEIVED OTP CODE: '{code}' (length: {len(code)}) ===")
        
        # Verify OTP
        if user.verify_otp(code):
            # Login user
            login_user(user)
            
            # Clear OTP fields
            user.reset_otp()
            db.session.commit()
            
            # Clear session
            session.pop('pending_user_id', None)
            session.pop('failed_attempts', None)
            
            # Redirect by role
            if user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
        
        # Handle wrong OTP
        session['failed_attempts'] = session.get('failed_attempts', 0) + 1
        
        if session['failed_attempts'] >= 3:
            # Lock account
            user.is_locked = True
            user.lock_until = get_current_time() + timedelta(minutes=15)
            user.reset_otp()
            db.session.commit()
            
            session.pop('pending_user_id', None)
            session.pop('failed_attempts', None)
            
            flash('Too many failed attempts! Account locked for 15 minutes.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if expired
        now = get_current_time()
        if user.otp_expires_at_aware <= now:
            flash('OTP has expired! Please login again.', 'danger')
            session.pop('pending_user_id', None)
            return redirect(url_for('auth.login'))
        
        flash(f'Invalid OTP! {3 - session["failed_attempts"]} attempts remaining.', 'danger')
        return render_template('auth/verify_otp.html')
    
    return render_template('auth/verify_otp.html')

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'pending_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['pending_user_id'])
    if not user:
        session.pop('pending_user_id', None)
        return redirect(url_for('auth.login'))
    
    # Generate new OTP
    otp = secrets.randbelow(900000) + 100000
    user.otp_code = str(otp)
    user.otp_expires_at = get_current_time() + timedelta(minutes=10)
    user.otp_verified = False
    db.session.commit()
    
    # Resend OTP notification
    notify_otp(user, otp)
    
    flash('OTP resent successfully!', 'success')
    return redirect(url_for('auth.verify_otp'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('auth.login'))
