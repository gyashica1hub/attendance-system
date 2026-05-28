import os
import cv2
import numpy as np
from flask import current_app

def get_face_detector():
    """Get Haar cascade face detector"""
    return cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

def detect_faces(image_gray):
    """Detect faces in grayscale image"""
    face_cascade = get_face_detector()
    return face_cascade.detectMultiScale(image_gray, 1.3, 5)

def preprocess_face(face_img, size=(200, 200)):
    """Preprocess face for recognition"""
    return cv2.resize(face_img, size)

def save_face_image(student_id, image_data, image_number):
    """Save face image to dataset"""
    dataset_path = current_app.config.get('DATASET_PATH', 'dataset')
    folder_path = os.path.join(dataset_path, str(student_id))
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, f"{image_number}.jpg")
    
    # Decode base64
    if "," in image_data:
        image_data = image_data.split(",")[1]
    
    import base64
    image_bytes = base64.b64decode(image_data)
    
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    
    return file_path