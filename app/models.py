from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()

class School(db.Model):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    subscription_plan = db.Column(db.String(50), default='free')
    subscription_expiry = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    teachers = db.relationship('Teacher', backref='school', lazy=True)
    classes = db.relationship('Class', backref='school', lazy=True)
    students = db.relationship('Student', backref='school', lazy=True)

class Teacher(db.Model, UserMixin):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    
    classes = db.relationship('Class', backref='teacher', lazy=True)
    attendances_marked = db.relationship('Attendance', backref='marked_by_teacher', 
                                        foreign_keys='Attendance.marked_by', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)

class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    section = db.Column(db.String(20), default='A')
    academic_year = db.Column(db.String(20), default='2024-25')
    
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    
    students = db.relationship('Student', backref='class_', lazy=True)
    attendances = db.relationship('Attendance', backref='class_', lazy=True)
    
    @property
    def display_name(self):
        return f"{self.class_name} - {self.subject} ({self.section})"

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    parent_name = db.Column(db.String(100))
    parent_phone = db.Column(db.String(20))
    parent_email = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    face_registered = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    face_images = db.relationship('FaceData', backref='student', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('roll_no', 'class_id', name='unique_roll_per_class'),)
    
    @property
    def attendance_percentage(self):
        total_days = Attendance.query.filter_by(student_id=self.id).count()
        if total_days == 0:
            return 0
        present_days = Attendance.query.filter_by(student_id=self.id, status='Present').count()
        return round((present_days / total_days) * 100, 2)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time = db.Column(db.Time, nullable=False, default=datetime.utcnow().time)
    status = db.Column(db.String(20), default='Present')
    method = db.Column(db.String(20), default='manual')  # face, manual
    confidence = db.Column(db.Float)
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'date', 'class_id', name='unique_daily_attendance'),)

class FaceData(db.Model):
    __tablename__ = 'face_data'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    image_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)