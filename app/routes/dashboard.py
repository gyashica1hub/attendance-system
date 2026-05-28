from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models import db, Class, Student, Attendance, School
from datetime import datetime, date

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    today = date.today()
    
    today_count = Attendance.query.filter_by(date=today).join(
        Class, Attendance.class_id == Class.id
    ).filter(Class.teacher_id == current_user.id).count()
    
    total_students = Student.query.join(Class).filter(
        Class.teacher_id == current_user.id, Student.is_active == True
    ).count()
    
    return render_template('dashboard/index.html',
        classes=classes,
        teacher_name=current_user.full_name or current_user.username,
        today_count=today_count,
        total_students=total_students,
        today=today.strftime('%Y-%m-%d')
    )

@bp.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    if request.method == 'POST':
        new_class = Class(
            class_name=request.form['class_name'],
            subject=request.form['subject'],
            section=request.form.get('section', 'A'),
            academic_year=request.form.get('academic_year', '2024-25'),
            teacher_id=current_user.id,
            school_id=current_user.school_id
        )
        db.session.add(new_class)
        db.session.commit()
        flash(f'Class created successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('dashboard/create_class.html')

@bp.route('/register_student', methods=['GET', 'POST'])
@login_required
def register_student():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        class_id = request.form['class_id']
        
        if Student.query.filter_by(roll_no=roll_no, class_id=class_id).first():
            flash('Roll number already exists in this class!', 'danger')
            return render_template('dashboard/register_student.html', classes=classes)
        
        student = Student(
            student_name=request.form['student_name'],
            roll_no=roll_no,
            class_id=class_id,
            school_id=current_user.school_id,
            parent_name=request.form.get('parent_name'),
            parent_phone=request.form.get('parent_phone'),
            parent_email=request.form.get('parent_email')
        )
        
        db.session.add(student)
        db.session.commit()
        flash('Student registered successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('dashboard/register_student.html', classes=classes)

@bp.route('/view_students/<int:class_id>')
@login_required
def view_students(class_id):
    class_obj = Class.query.filter_by(id=class_id, teacher_id=current_user.id).first_or_404()
    students = Student.query.filter_by(class_id=class_id, is_active=True).all()
    return render_template('dashboard/view_students.html', 
        students=students, class_info=class_obj, class_id=class_id)

@bp.route('/delete_class/<int:id>')
@login_required
def delete_class(id):
    class_obj = Class.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    Student.query.filter_by(class_id=id).delete()
    Attendance.query.filter_by(class_id=id).delete()
    db.session.delete(class_obj)
    db.session.commit()
    flash('Class deleted!', 'success')
    return redirect(url_for('dashboard.index'))

@bp.route('/delete_student/<int:id>')
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    if student.class_.teacher_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('dashboard.index'))
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('dashboard.view_students', class_id=student.class_id))