from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import Student, Attendance, Class
from datetime import date

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/students/<int:class_id>')
@login_required
def get_students(class_id):
    """Get students for a class (for AJAX)"""
    class_obj = Class.query.filter_by(id=class_id, teacher_id=current_user.id).first_or_404()
    students = Student.query.filter_by(class_id=class_id, is_active=True).all()
    
    return jsonify({
        'students': [
            {
                'id': s.id,
                'name': s.student_name,
                'roll_no': s.roll_no,
                'face_registered': s.face_registered
            }
            for s in students
        ]
    })

@bp.route('/today_stats')
@login_required
def today_stats():
    """Get today's attendance stats"""
    today = date.today()
    
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    stats = []
    
    for cls in classes:
        total = Student.query.filter_by(class_id=cls.id, is_active=True).count()
        present = Attendance.query.filter_by(
            class_id=cls.id, date=today, status='Present'
        ).count()
        
        stats.append({
            'class_name': cls.display_name,
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': round((present / total * 100), 1) if total > 0 else 0
        })
    
    return jsonify({'stats': stats})