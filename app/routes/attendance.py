from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models import Class, Student, Attendance

bp = Blueprint('attendance', __name__)

import qrcode
import io
import base64
from datetime import date


@bp.route('/qr/<int:class_id>')
@login_required
def generate_qr(class_id):
    class_info = Class.query.get_or_404(class_id)
    
    if class_info.teacher_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Generate QR code with class info
    qr_data = f"ATTENDANCE:{class_id}:{date.today().isoformat()}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('attendance/qr_code.html',
                         class_info=class_info,
                         qr_base64=qr_base64,
                         qr_data=qr_data)


@bp.route('/scan-qr', methods=['POST'])
def scan_qr():
    qr_data = request.json.get('qr_data')
    
    try:
        prefix, class_id, qr_date = qr_data.split(':')
        class_id = int(class_id)
        qr_date = datetime.strptime(qr_date, '%Y-%m-%d').date()
        
        if qr_date != date.today():
            return jsonify({'status': 'error', 'message': 'QR code expired!'})
        
        # Mark attendance (student must be logged in)
        # Implementation depends on student login system
        
        return jsonify({'status': 'success', 'message': 'Attendance marked!'})
    except:
        return jsonify({'status': 'error', 'message': 'Invalid QR code!'})

@bp.route('/take')
@login_required
def take_attendance():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('attendance/take_attendance.html', classes=classes)


@bp.route('/take/<int:class_id>')
@login_required
def take_attendance_class(class_id):
    class_info = Class.query.get_or_404(class_id)
    
    # Sirf apni classes
    if class_info.teacher_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('dashboard.index'))
    
    students = Student.query.filter_by(class_id=class_id).all()
    
    # Aaj ki attendance check karo
    today = date.today()
    already_marked = {}
    for student in students:
        record = Attendance.query.filter_by(
            student_id=student.id,
            class_id=class_id,
            date=today
        ).first()
        if record:
            already_marked[student.id] = record.status
    
    return render_template('attendance/take_attendance.html', 
                         class_info=class_info,
                         students=students,
                         class_id=class_id,
                         today=today.strftime('%d %b %Y'),
                         already_marked=already_marked)


@bp.route('/mark-manual', methods=['POST'])
@login_required
def mark_manual():
    student_id = request.form.get('student_id')
    class_id = request.form.get('class_id')
    
    if not student_id or not class_id:
        return jsonify({'status': 'error', 'message': 'Missing data'})
    
    # Check if already marked today
    today = date.today()
    existing = Attendance.query.filter_by(
        student_id=student_id,
        class_id=class_id,
        date=today
    ).first()
    
    if existing:
        return jsonify({'status': 'already_marked', 'message': 'Already marked present today!'})
    
    # Mark attendance
    attendance = Attendance(
        student_id=student_id,
        class_id=class_id,
        date=today,
        status='present',
        marked_by='manual'
    )
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Attendance marked!'})


@bp.route('/register-face')
@login_required
def register_face():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('attendance/register_face.html', classes=classes)