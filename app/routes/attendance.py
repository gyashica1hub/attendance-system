import os
import cv2
import numpy as np
import base64
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from app.models import db, Class, Student, Attendance, FaceData

bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@bp.route('/take/<int:class_id>')
@login_required
def take_attendance(class_id):
    class_obj = Class.query.filter_by(id=class_id, teacher_id=current_user.id).first_or_404()
    students = Student.query.filter_by(class_id=class_id, is_active=True).all()
    
    today = date.today()
    already_marked = [a.student_id for a in Attendance.query.filter_by(
        date=today, class_id=class_id
    ).all()]
    
    return render_template('attendance/take_attendance.html',
        class_id=class_id,
        students=students,
        class_info=class_obj,
        already_marked=already_marked,
        today=today.strftime('%Y-%m-%d')
    )

@bp.route('/register_face/<int:student_id>')
@login_required
def register_face_page(student_id):
    student = Student.query.get_or_404(student_id)
    if student.class_.teacher_id != current_user.id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('dashboard.index'))
    return render_template('attendance/register_face.html', student=student)

@bp.route('/save_face', methods=['POST'])
@login_required
def save_face():
    try:
        student_id = request.form['student_id']
        image_data = request.form['image']
        image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        
        student = Student.query.get_or_404(student_id)
        
        # Save to dataset folder
        dataset_path = current_app.config.get('DATASET_PATH', 'dataset')
        folder_path = os.path.join(dataset_path, str(student_id))
        os.makedirs(folder_path, exist_ok=True)
        
        image_number = len(os.listdir(folder_path)) + 1
        file_path = os.path.join(folder_path, f"{image_number}.jpg")
        
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        
        # Save to database
        face_data = FaceData(
            student_id=student_id,
            image_path=file_path,
            image_number=image_number
        )
        db.session.add(face_data)
        
        # Mark face as registered
        student.face_registered = True
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": f"Face {image_number} saved!",
            "count": image_number
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@bp.route('/train_model')
@login_required
def train_model():
    dataset_path = current_app.config.get('DATASET_PATH', 'dataset')
    
    if not os.path.exists(dataset_path):
        return jsonify({"status": "error", "message": "Dataset folder missing"})
    
    faces = []
    labels = []
    label_map = {}
    current_label = 0
    
    for student_id in os.listdir(dataset_path):
        student_folder = os.path.join(dataset_path, student_id)
        if not os.path.isdir(student_folder):
            continue
        
        try:
            student_id_int = int(student_id)
            student = Student.query.get(student_id_int)
            if not student:
                continue
            
            label_map[current_label] = student.student_name
            
            for image_name in os.listdir(student_folder):
                img_path = os.path.join(student_folder, image_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                img = cv2.resize(img, (200, 200))
                faces.append(img)
                labels.append(current_label)
            
            current_label += 1
        except ValueError:
            continue
    
    if len(faces) == 0:
        return "No face images found!"
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    
    model_path = os.path.join(current_app.root_path, '..', 'face_model.yml')
    recognizer.save(model_path)
    
    labels_path = os.path.join(current_app.root_path, '..', 'labels.txt')
    with open(labels_path, "w") as f:
        for label, name in label_map.items():
            f.write(f"{label},{name}\n")
    
    return f"Model trained with {len(faces)} images for {current_label} students!"

@bp.route('/scan', methods=['POST'])
@login_required
def scan_attendance():
    try:
        data = request.get_json(force=True)
        image_data = data.get('image', '')
        class_id = int(data.get('class_id', 0))
        
        if not image_data:
            return jsonify({"status": "error", "message": "No image received"})
        
        # Decode image
        if "," in image_data:
            image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            return jsonify({"status": "error", "message": "Could not decode image"})
        
        # Load model
        model_path = os.path.join(current_app.root_path, '..', 'face_model.yml')
        labels_path = os.path.join(current_app.root_path, '..', 'labels.txt')
        
        if not os.path.exists(model_path) or not os.path.exists(labels_path):
            return jsonify({
                "status": "error", 
                "message": "AI model not trained! Go to Dashboard → Train AI Model"
            })
        
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(model_path)
        
        labels = {}
        with open(labels_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "," in line:
                    label, name = line.split(",", 1)
                    labels[int(label)] = name
        
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        faces_detected = face_cascade.detectMultiScale(img, 1.3, 5)
        
        if len(faces_detected) == 0:
            return jsonify({
                "status": "no_face", 
                "message": "No face detected. Look at camera."
            })
        
        # Get class students
        class_students = Student.query.filter_by(class_id=class_id, is_active=True).all()
        class_student_names = {s.student_name: s for s in class_students}
        
        now = datetime.now()
        today = now.date()
        time_now = now.time()
        
        results = []
        marked_count = 0
        
        for (x, y, w, h) in faces_detected:
            face = img[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))
            label, confidence = recognizer.predict(face)
            
            if confidence < current_app.config.get('FACE_CONFIDENCE_THRESHOLD', 70):
                name = labels.get(label, "Unknown")
                
                if name in class_student_names:
                    student = class_student_names[name]
                    
                    # Check if already marked
                    existing = Attendance.query.filter_by(
                        student_id=student.id, date=today
                    ).first()
                    
                    if existing:
                        results.append({
                            "name": name, 
                            "status": "already_marked", 
                            "confidence": round(confidence, 1)
                        })
                    else:
                        attendance = Attendance(
                            student_id=student.id,
                            class_id=class_id,
                            date=today,
                            time=time_now,
                            status="Present",
                            method="face",
                            confidence=round(confidence, 1),
                            marked_by=current_user.id
                        )
                        db.session.add(attendance)
                        marked_count += 1
                        results.append({
                            "name": name, 
                            "status": "marked", 
                            "confidence": round(confidence, 1)
                        })
                else:
                    results.append({
                        "name": name, 
                        "status": "not_in_class", 
                        "confidence": round(confidence, 1)
                    })
            else:
                results.append({
                    "name": "Unknown", 
                    "status": "low_confidence", 
                    "confidence": round(confidence, 1)
                })
        
        db.session.commit()
        
        # Build response
        if marked_count > 0:
            names = [r['name'] for r in results if r['status'] == 'marked']
            return jsonify({
                "status": "success",
                "message": f"{', '.join(names)} — Attendance Marked!",
                "results": results,
                "marked": marked_count
            })
        
        if results:
            r = results[0]
            if r['status'] == 'already_marked':
                return jsonify({
                    "status": "already_marked",
                    "message": f"{r['name']} already marked today!",
                    "results": results
                })
            elif r['status'] == 'not_in_class':
                return jsonify({
                    "status": "warning",
                    "message": f"{r['name']} not in this class!",
                    "results": results
                })
        
        return jsonify({
            "status": "error",
            "message": "Face not recognized. Try better lighting."
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

@bp.route('/mark_manual', methods=['POST'])
@login_required
def mark_manual():
    try:
        student_id = request.form.get('student_id')
        class_id = request.form.get('class_id')
        status = request.form.get('status', 'Present')
        
        if not student_id:
            return jsonify({"status": "error", "message": "Student ID missing"})
        
        student = Student.query.get_or_404(student_id)
        today = date.today()
        
        existing = Attendance.query.filter_by(
            student_id=student_id, date=today
        ).first()
        
        if existing:
            return jsonify({
                "status": "already_marked",
                "message": f"{student.student_name} already marked today"
            })
        
        attendance = Attendance(
            student_id=student_id,
            class_id=class_id,
            date=today,
            time=datetime.now().time(),
            status=status,
            method='manual',
            marked_by=current_user.id
        )
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"{student.student_name} marked as {status}"
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})