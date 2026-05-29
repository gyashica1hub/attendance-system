from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Teacher(UserMixin, db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='teacher')  # teacher, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    classes = db.relationship('Class', backref='teacher', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'


class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    students = db.relationship('Student', backref='class_', lazy=True)
    attendance_records = db.relationship('Attendance', backref='class_', lazy=True)


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(500))
    photo_path = db.Column(db.String(255))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    face_encoding = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    
    def get_photo_url(self):
        if self.photo_path:
            return f'/static/uploads/students/{self.photo_path}'
        return '/static/img/default-avatar.png'
    
    def attendance_percentage(self):
        total = len(self.attendance_records)
        if total == 0:
            return 0
        present = sum(1 for a in self.attendance_records if a.status == 'present')
        return round((present / total) * 100, 1)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='present')
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    marked_by = db.Column(db.String(50), default='manual')  # manual, face, qr
    qr_code = db.Column(db.String(100))


class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20))
    notification_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)