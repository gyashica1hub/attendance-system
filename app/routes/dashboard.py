from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import Class, Student, Attendance
from datetime import datetime, date

bp = Blueprint('dashboard', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
@login_required
def index():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('dashboard/index.html', classes=classes)


@bp.route('/create-class', methods=['GET', 'POST'])
@login_required
def create_class():
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        
        if not name:
            flash('Class number is required!', 'danger')
            return redirect(url_for('dashboard.create_class'))
        
        try:
            class_num = int(name)
            if class_num < 1 or class_num > 12:
                flash('Class number must be between 1 and 12!', 'danger')
                return redirect(url_for('dashboard.create_class'))
        except ValueError:
            flash('Only numbers (1-12) allowed!', 'danger')
            return redirect(url_for('dashboard.create_class'))
        
        class_name = f"Class {class_num}"
        
        new_class = Class(name=class_name, subject=subject, teacher_id=current_user.id)
        db.session.add(new_class)
        db.session.commit()
        
        flash(f'Class "{class_name}" created successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('dashboard/create_class.html')


@bp.route('/register-student', methods=['GET', 'POST'])
@login_required
def register_student():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    
    if request.method == 'POST':
        roll_number = request.form.get('roll_number')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        class_id = request.form.get('class_id')
        
        if not roll_number or not name or not class_id:
            flash('Roll number, name and class are required!', 'danger')
            return redirect(url_for('dashboard.register_student'))
        
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already exists!', 'danger')
            return redirect(url_for('dashboard.register_student'))
        
        # ✅ Handle photo upload
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{roll_number}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'students')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                photo_path = filename
        
        student = Student(
            roll_number=roll_number,
            name=name,
            email=email,
            phone=phone,
            address=address,
            photo_path=photo_path,
            class_id=class_id
        )
        db.session.add(student)
        db.session.commit()
        
        flash(f'Student "{name}" registered successfully!', 'success')
        return redirect(url_for('dashboard.view_students'))
    
    return render_template('dashboard/register_student.html', classes=classes)


@bp.route('/students')
@login_required
def view_students():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    class_id = request.args.get('class_id', type=int)
    
    students = []
    class_info = None
    
    if class_id:
        students = Student.query.filter_by(class_id=class_id).all()
        class_info = Class.query.get(class_id)
    
    return render_template('dashboard/view_students.html', 
                         classes=classes, 
                         students=students, 
                         selected_class=class_id,
                         class_info=class_info)


# ✅ NEW: Student Profile Route
@bp.route('/student/<int:student_id>')
@login_required
def student_profile(student_id):
    student = Student.query.get_or_404(student_id)
    
    # Security check
    if student.class_.teacher_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Attendance history
    attendance_history = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).all()
    
    # Monthly stats
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_present = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.status == 'present',
        db.extract('month', Attendance.date) == current_month,
        db.extract('year', Attendance.date) == current_year
    ).count()
    
    monthly_total = Attendance.query.filter(
        Attendance.student_id == student_id,
        db.extract('month', Attendance.date) == current_month,
        db.extract('year', Attendance.date) == current_year
    ).count()
    
    monthly_percentage = (monthly_present / monthly_total * 100) if monthly_total > 0 else 0
    
    # Overall stats
    total_days = len(attendance_history)
    present_days = sum(1 for a in attendance_history if a.status == 'present')
    overall_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return render_template('dashboard/student_profile.html',
                         student=student,
                         attendance_history=attendance_history,
                         monthly_present=monthly_present,
                         monthly_total=monthly_total,
                         monthly_percentage=round(monthly_percentage, 1),
                         total_days=total_days,
                         present_days=present_days,
                         overall_percentage=round(overall_percentage, 1))


# ✅ NEW: Edit Student
@bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if student.class_.teacher_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.email = request.form.get('email')
        student.phone = request.form.get('phone')
        student.address = request.form.get('address')
        
        # Handle new photo
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{student.roll_number}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'students')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                student.photo_path = filename
        
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('dashboard.student_profile', student_id=student.id))
    
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('dashboard/edit_student.html', student=student, classes=classes)


# ✅ NEW: Delete Student
@bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if student.class_.teacher_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Delete photo if exists
    if student.photo_path:
        photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'students', student.photo_path)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('dashboard.view_students'))