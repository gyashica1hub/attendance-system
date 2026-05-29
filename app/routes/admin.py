from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Teacher, Class, Student, Attendance
from datetime import date

bp = Blueprint('admin', __name__)


def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required!', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@bp.route('/')
@login_required
@admin_required
def index():
    total_teachers = Teacher.query.count()
    total_classes = Class.query.count()
    total_students = Student.query.count()
    today_attendance = Attendance.query.filter_by(date=date.today()).count()
    
    return render_template('admin/index.html',
                         total_teachers=total_teachers,
                         total_classes=total_classes,
                         total_students=total_students,
                         today_attendance=today_attendance)


@bp.route('/teachers')
@login_required
@admin_required
def teachers():
    all_teachers = Teacher.query.all()
    return render_template('admin/teachers.html', teachers=all_teachers)


@bp.route('/teachers/add', methods=['POST'])
@login_required
@admin_required
def add_teacher():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'teacher')
    
    if Teacher.query.filter_by(username=username).first():
        flash('Username already exists!', 'danger')
        return redirect(url_for('admin.teachers'))
    
    teacher = Teacher(username=username, email=email, role=role)
    teacher.set_password(password)
    db.session.add(teacher)
    db.session.commit()
    
    flash(f'Teacher "{username}" added successfully!', 'success')
    return redirect(url_for('admin.teachers'))


@bp.route('/teachers/toggle/<int:teacher_id>')
@login_required
@admin_required
def toggle_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    
    if teacher.id == current_user.id:
        flash('Cannot deactivate yourself!', 'danger')
        return redirect(url_for('admin.teachers'))
    
    teacher.is_active = not teacher.is_active
    db.session.commit()
    
    status = 'activated' if teacher.is_active else 'deactivated'
    flash(f'Teacher "{teacher.username}" {status}!', 'success')
    return redirect(url_for('admin.teachers'))