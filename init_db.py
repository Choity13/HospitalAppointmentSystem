from app import create_app
from extensions import db
from models import User, Department, Doctor, TimeSlot, SymptomsMap
from datetime import datetime, time, timedelta
import pytz
import bcrypt

tz = pytz.timezone('Asia/Dhaka')


def init_db():
    app = create_app()
    with app.app_context():
        # Drop existing tables (for testing)
        db.drop_all()
        
        # Create tables
        db.create_all()
        
        print("Tables created successfully!")
        
        # Add sample departments
        depts = [
            Department(dept_name="General Medicine", icon_name="bi-heart-pulse"),
            Department(dept_name="Cardiology", icon_name="bi-heart"),
            Department(dept_name="Pediatrics", icon_name="bi-person-heart"),
            Department(dept_name="Orthopedics", icon_name="bi-person-badge"),
            Department(dept_name="Dermatology", icon_name="bi-emoji-smile")
        ]
        
        db.session.add_all(depts)
        db.session.commit()
        
        # Add sample users
        # Admin
        admin_password = bcrypt.hashpw(b'Admin123', bcrypt.gensalt(12)).decode('utf-8')
        admin = User(
            full_name="System Admin",
            phone_number="8801700000000",
            password_hash=admin_password,
            role="admin",
            carrier="Grameenphone",
            is_active=True
        )
        db.session.add(admin)
        
        # Patient
        patient_password = bcrypt.hashpw(b'Patient123', bcrypt.gensalt(12)).decode('utf-8')
        patient = User(
            full_name="John Doe",
            phone_number="8801711111111",
            password_hash=patient_password,
            role="patient",
            carrier="Robi",
            is_active=True
        )
        db.session.add(patient)
        
        # Doctor User
        doctor_password = bcrypt.hashpw(b'Doctor123', bcrypt.gensalt(12)).decode('utf-8')
        doctor_user = User(
            full_name="Alice Smith",
            phone_number="8801722222222",
            password_hash=doctor_password,
            role="doctor",
            carrier="Banglalink",
            is_active=True
        )
        db.session.add(doctor_user)
        
        db.session.commit()
        
        # Add Doctor Profile
        doctor = Doctor(
            user_id=doctor_user.user_id,
            dept_id=depts[0].dept_id,
            specialty="General Physician",
            consultation_fee=500,
            bio="10+ years of experience in general medicine",
            avg_rating=4.5
        )
        db.session.add(doctor)
        db.session.commit()
        
        # Add Sample Time Slots for Doctor
        today = datetime.now(tz).date()
        for days_offset in range(7):
            slot_date = today + timedelta(days=days_offset)
            # Skip Sundays?
            if slot_date.weekday() == 6:
                continue
                
            for hour in range(9, 17):  # 9 AM to 4 PM
                slot = TimeSlot(
                    doctor_id=doctor.doctor_id,
                    slot_date=slot_date,
                    slot_time=time(hour, 0),
                    is_available=True
                )
                db.session.add(slot)
        
        # Add Symptoms
        symptoms = [
            SymptomsMap(keyword="fever", dept_id=depts[0].dept_id),
            SymptomsMap(keyword="cough", dept_id=depts[0].dept_id),
            SymptomsMap(keyword="chest pain", dept_id=depts[1].dept_id),
            SymptomsMap(keyword="child fever", dept_id=depts[2].dept_id),
            SymptomsMap(keyword="joint pain", dept_id=depts[3].dept_id),
            SymptomsMap(keyword="skin rash", dept_id=depts[4].dept_id)
        ]
        db.session.add_all(symptoms)
        
        db.session.commit()
        
        print("Sample data added successfully!")
        print("\nTest Credentials:")
        print("Admin: Phone 8801700000000, Password Admin123")
        print("Patient: Phone 8801711111111, Password Patient123")
        print("Doctor: Phone 8801722222222, Password Doctor123")


if __name__ == '__main__':
    init_db()
