import traceback
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Teacher

bp = Blueprint('auth', __name__)


@bp.route('/home')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.register'))
        
        if Teacher.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('auth.register'))
        
        if Teacher.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('auth.register'))
        
        teacher = Teacher(username=username, email=email)
        teacher.set_password(password)
        db.session.add(teacher)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


# @bp.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('dashboard.index'))
    
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
        
#         if not username or not password:
#             flash('Please enter username and password!', 'danger')
#             return redirect(url_for('auth.login'))
        
#         teacher = Teacher.query.filter_by(username=username).first()
        
#         if teacher and teacher.check_password(password):
#             login_user(teacher)
#             flash(f'Welcome back, {teacher.username}!', 'success')
#             return redirect(url_for('dashboard.index'))
        
#         flash('Invalid username or password!', 'danger')
    
#     return render_template('auth/login.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            teacher = Teacher.query.filter_by(username=username).first()

            # if teacher and teacher.check_password(password):
            #     login_user(teacher)
            #     return redirect(url_for('dashboard.index'))

            if teacher and teacher.check_password(password):
                login_user(teacher)
                return "LOGIN SUCCESS"

            flash('Invalid username or password!', 'danger')

        return render_template('auth/login.html')

    except Exception:
        print("LOGIN ERROR")
        traceback.print_exc()
        raise

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))