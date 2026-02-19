
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask_mail import Mail, Message
from flask_jwt_extended import jwt_required, create_access_token
from .models import User, OAuth
from . import db, mail
import os

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.', 'danger')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)

    return redirect(url_for('main.profile'))


def send_otp_email(user, otp):
    msg = Message()
    msg.subject = "Login System: Password Reset OTP"
    msg.sender = os.getenv('MAIL_USERNAME', 'username@gmail.com')
    msg.recipients = [user.email]
    msg.html = render_template('reset_pwd.html', user=user, otp=otp)

    mail.send(msg)


@auth.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == "GET":
        return render_template('reset.html')

    if request.method == "POST":
        email = request.form.get('email')
        user = User.verify_email(email)

        if user:
            otp = ''.join(random.choices(string.digits, k=6))
            session['reset_otp'] = otp
            session['reset_email'] = email
            session['reset_expiry'] = (
                datetime.now() + timedelta(minutes=10)).isoformat()

            send_otp_email(user, otp)
            flash('An email has been sent with your verification code.', 'info')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Email not found.', 'danger')
            return redirect(url_for('auth.reset'))
            return redirect(url_for('auth.verify_otp'))


@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'GET':
        return render_template('verify_otp.html')

    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        stored_otp = session.get('reset_otp')
        expiry_str = session.get('reset_expiry')

        if not stored_otp or not expiry_str:
            flash('No active reset request found. Please try again.', 'warning')
            return redirect(url_for('auth.reset'))

        expiry = datetime.fromisoformat(expiry_str)
        if datetime.now() > expiry:
            flash('OTP has expired. Please request a new one.', 'warning')
            session.pop('reset_otp', None)
            session.pop('reset_expiry', None)
            return redirect(url_for('auth.reset'))

        if entered_otp == stored_otp:
            session['reset_verified'] = True
            session.pop('reset_otp', None)
            session.pop('reset_expiry', None)
            return redirect(url_for('auth.reset_password_final'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('auth.verify_otp'))


@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_final():
    if not session.get('reset_verified') or not session.get('reset_email'):
        flash('Please verify your email first.', 'warning')
        return redirect(url_for('auth.reset'))

    user = User.query.filter_by(email=session.get('reset_email')).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.reset'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('Please fill out both password fields.', 'warning')
            return redirect(url_for('auth.reset_password_final'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password_final'))

        if not any(char.isdigit() for char in password):
            flash('Password must contain at least one digit.', 'danger')
            return redirect(url_for('auth.reset_password_final'))

        if not any(char.isupper() for char in password):
            flash('Password must contain at least one uppercase letter.', 'danger')
            return redirect(url_for('auth.reset_password_final'))

        if len(password) != 8:
            flash('Password must be exactly 8 characters long.', 'danger')
            return redirect(url_for('auth.reset_password_final'))

        
        hashed_password = generate_password_hash(password)
        user.password = hashed_password
        db.session.commit()

        session.pop('reset_verified', None)
        session.pop('reset_email', None)

        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html')


@auth.route('/signup')
def signup():
    return render_template('signup.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not username or not email or not password or not confirm_password:
        flash('Please fill out all fields', 'warning')
        return redirect(url_for('auth.signup'))

    if '@' not in email or '.' not in email:
        flash('Please Enter a valid email address', 'warning')
        return redirect(url_for('auth.signup'))

    if password != confirm_password:
        flash('Passwords not matching', 'warning')
        return redirect(url_for('auth.signup'))

    elif not any(char.isdigit() for char in password):
        flash('Password must contain at least one digit', "warning")
        return redirect(url_for('auth.signup'))
    elif not any(char.isupper() for char in password):
        flash('Password must contain at least one uppercase letter', "warning")
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    new_user = User(username=username, email=email,
                    password=generate_password_hash(password))

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
