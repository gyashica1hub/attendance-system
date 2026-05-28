from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Teacher, School

bp = Blueprint('auth', __name__)

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        school_name = request.form.get('school_name')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'danger')
            return render_template('auth/register.html')
        
        if Teacher.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('auth/register.html')
        
        # Create school if provided
        school = None
        if school_name:
            school = School(school_name=school_name, contact_email=email)
            db.session.add(school)
            db.session.flush()
        
        # Create teacher
        teacher = Teacher(
            username=username,
            email=email,
            full_name=username,
            school_id=school.id if school else None,
            is_admin=bool(school),
            is_super_admin=False
        )
        teacher.set_password(password)
        
        db.session.add(teacher)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        teacher = Teacher.query.filter_by(email=email).first()
        
        if teacher and teacher.check_password(password):
            if not teacher.is_active:
                flash('Account is deactivated! Contact admin.', 'danger')
                return render_template('auth/login.html')
            
            login_user(teacher)
            session['teacher_name'] = teacher.full_name or teacher.username
            session['school_id'] = teacher.school_id
            session['is_admin'] = teacher.is_admin
            session['is_super_admin'] = teacher.is_super_admin
            
            flash(f'Welcome back, {teacher.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        
        flash('Invalid email or password!', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.home'))