from flask_mail import Mail, Message
from flask import current_app

mail = Mail()


def init_mail(app):
    mail.init_app(app)


def send_attendance_notification(student_email, student_name, date, status):
    try:
        msg = Message(
            'Attendance Notification - Smart Attendance',
            sender=current_app.config.get('MAIL_USERNAME'),
            recipients=[student_email]
        )
        
        msg.body = f"""
        Hello {student_name},
        
        Your attendance for {date} has been marked as: {status.upper()}
        
        Regards,
        Smart Attendance System
        """
        
        msg.html = f"""
        <h3>Attendance Notification</h3>
        <p>Hello <b>{student_name}</b>,</p>
        <p>Your attendance for <b>{date}</b> has been marked as: 
           <span style="color: {'green' if status == 'present' else 'red'}; font-weight: bold;">
               {status.upper()}
           </span>
        </p>
        <br>
        <p>Regards,<br>Smart Attendance System</p>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False