from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user
from app.models import db, Class, Student, Attendance
from datetime import datetime, date
import io
from openpyxl import Workbook

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_class = request.args.get('class_id', '')
    
    # Get teacher's classes
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    
    # Get unique dates
    dates_query = db.session.query(Attendance.date).distinct().order_by(Attendance.date.desc()).all()
    all_dates = [d[0].strftime('%Y-%m-%d') for d in dates_query]
    
    # Build query
    query = Student.query.join(Class).filter(
        Class.teacher_id == current_user.id,
        Student.is_active == True
    )
    
    if selected_class:
        query = query.filter(Student.class_id == selected_class)
    
    students = query.order_by(Class.class_name, Student.roll_no).all()
    
    # Get attendance for selected date
    attendance_today = {
        a.student_id: a for a in Attendance.query.filter_by(date=selected_date).all()
    }
    
    # Build report
    report_by_class = {}
    for student in students:
        class_name = student.class_.display_name
        if class_name not in report_by_class:
            report_by_class[class_name] = []
        
        att = attendance_today.get(student.id)
        report_by_class[class_name].append({
            'student_name': student.student_name,
            'roll_no': student.roll_no,
            'status': att.status if att else 'Absent',
            'time': att.time.strftime('%H:%M') if att else '-',
            'method': att.method if att else '-'
        })
    
    total_present = len([a for a in attendance_today.values() if a.status == 'Present'])
    total_students = len(students)
    total_absent = total_students - total_present
    
    return render_template('reports/index.html',
        report_by_class=report_by_class,
        selected_date=selected_date,
        all_dates=all_dates,
        classes=classes,
        selected_class=selected_class,
        total_present=total_present,
        total_absent=total_absent,
        total_students=total_students
    )

@bp.route('/export_excel')
@login_required
def export_excel():
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_class = request.args.get('class_id', '')
    
    query = Student.query.join(Class).filter(
        Class.teacher_id == current_user.id,
        Student.is_active == True
    )
    
    if selected_class:
        query = query.filter(Student.class_id == selected_class)
    
    students = query.order_by(Class.class_name, Student.roll_no).all()
    attendance_today = {
        a.student_id: a for a in Attendance.query.filter_by(date=selected_date).all()
    }
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    
    # Headers
    ws.append(['Class', 'Roll No', 'Student Name', 'Status', 'Time', 'Method'])
    
    for student in students:
        att = attendance_today.get(student.id)
        ws.append([
            student.class_.display_name,
            student.roll_no,
            student.student_name,
            att.status if att else 'Absent',
            att.time.strftime('%H:%M') if att else '-',
            att.method if att else '-'
        ])
    
    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'attendance_{selected_date}.xlsx'
    )

@bp.route('/student/<int:student_id>')
@login_required
def student_attendance(student_id):
    student = Student.query.get_or_404(student_id)
    
    # Verify ownership
    if student.class_.teacher_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('dashboard.index'))
    
    present_days = Attendance.query.filter_by(
        student_id=student_id, status='Present'
    ).count()
    
    total_days = db.session.query(Attendance.date).filter_by(
        student_id=student_id
    ).distinct().count()
    
    percentage = 0 if total_days == 0 else round((present_days / total_days) * 100, 2)
    
    history = Attendance.query.filter_by(student_id=student_id).order_by(
        Attendance.date.desc()
    ).all()
    
    return render_template('reports/student_attendance.html',
        student=student,
        present_days=present_days,
        total_days=total_days,
        percentage=percentage,
        history=history
    )