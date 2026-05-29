from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import date, timedelta
from app.models import Class, Student, Attendance

bp = Blueprint('reports', __name__)


@bp.route('/')
@login_required
def index():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    
    # Stats
    total_students = Student.query.join(Class).filter(Class.teacher_id == current_user.id).count()
    
    today = date.today()
    today_attendance = Attendance.query.join(Class).filter(
        Class.teacher_id == current_user.id,
        Attendance.date == today
    ).count()
    
    # Last 7 days data
    last_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Attendance.query.join(Class).filter(
            Class.teacher_id == current_user.id,
            Attendance.date == day
        ).count()
        last_7_days.append({
            'date': day.strftime('%d %b'),
            'count': count
        })
    
    return render_template('reports/index.html',
                         classes=classes,
                         total_students=total_students,
                         today_attendance=today_attendance,
                         last_7_days=last_7_days)


@bp.route('/class/<int:class_id>')
@login_required
def class_report(class_id):
    class_info = Class.query.get_or_404(class_id)
    
    if class_info.teacher_id != current_user.id:
        return redirect(url_for('dashboard.index'))
    
    students = Student.query.filter_by(class_id=class_id).all()
    
    # Attendance summary for each student
    student_data = []
    for student in students:
        total_days = Attendance.query.filter_by(student_id=student.id).count()
        present_days = Attendance.query.filter_by(student_id=student.id, status='present').count()
        
        percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        student_data.append({
            'name': student.name,
            'roll_number': student.roll_number,
            'total_days': total_days,
            'present_days': present_days,
            'percentage': round(percentage, 1)
        })
    
    return render_template('reports/class_report.html',
                         class_info=class_info,
                         student_data=student_data)