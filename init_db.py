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
        db.drop_all()
        db.create_all()
        print("Tables created successfully!")

        # ── DEPARTMENTS ────────────────────────────────────────────────────────
        depts = [
            Department(dept_name="General Medicine", icon_name="bi-heart-pulse"),
            Department(dept_name="Cardiology",       icon_name="bi-heart"),
            Department(dept_name="Pediatrics",       icon_name="bi-person-heart"),
            Department(dept_name="Orthopedics",      icon_name="bi-person-badge"),
            Department(dept_name="Dermatology",      icon_name="bi-emoji-smile"),
        ]
        db.session.add_all(depts)
        db.session.commit()

        # ── ADMIN ──────────────────────────────────────────────────────────────
        admin = User(
            full_name="System Admin",
            phone_number="8801700000000",
            password_hash=bcrypt.hashpw(b'Admin@1234', bcrypt.gensalt(12)).decode('utf-8'),
            role="admin", carrier="Grameenphone", is_active=True
        )
        db.session.add(admin)

        # ── PATIENT ────────────────────────────────────────────────────────────
        patient = User(
            full_name="Mohammad Rahim",
            phone_number="8801711111111",
            password_hash=bcrypt.hashpw(b'Patient@1234', bcrypt.gensalt(12)).decode('utf-8'),
            role="patient", carrier="Robi", is_active=True
        )
        db.session.add(patient)

        # ── DOCTOR USERS (15 Bangladeshi doctors, 3 per department) ───────────
        doctor_data = [
            # General Medicine
            ("Farhan Hossain",  "8801722222201", "Grameenphone"),
            ("Nasrin Akter",    "8801722222202", "Robi"),
            ("Tariq Rahman",    "8801722222203", "Banglalink"),
            # Cardiology
            ("Imran Chowdhury","8801722222204", "Grameenphone"),
            ("Sultana Begum",  "8801722222205", "Robi"),
            ("Rakib Uddin",    "8801722222206", "Teletalk"),
            # Pediatrics
            ("Maliha Islam",   "8801722222207", "Grameenphone"),
            ("Zahir Ahmed",    "8801722222208", "Banglalink"),
            ("Roksana Khanam", "8801722222209", "Robi"),
            # Orthopedics
            ("Shafiq Molla",   "8801722222210", "Grameenphone"),
            ("Parveen Noor",   "8801722222211", "Teletalk"),
            ("Kamal Hasan",    "8801722222212", "Robi"),
            # Dermatology
            ("Tasnim Zaman",   "8801722222213", "Banglalink"),
            ("Arif Billah",    "8801722222214", "Grameenphone"),
            ("Sumaiya Parvin", "8801722222215", "Robi"),
        ]

        specialties = [
            "General Physician", "Internal Medicine", "Family Medicine",
            "Cardiologist", "Interventional Cardiologist", "Cardiac Surgeon",
            "Pediatrician", "Neonatologist", "Child Specialist",
            "Orthopedic Surgeon", "Spine Specialist", "Joint Replacement Surgeon",
            "Dermatologist", "Cosmetologist", "Skin & Hair Specialist",
        ]

        fees = [500, 600, 550, 800, 900, 1000, 600, 700, 650,
                800, 850, 900, 600, 700, 650]

        bios = [
            "15+ years in general medicine and primary care.",
            "Specialist in internal medicine with 12 years experience.",
            "Family medicine expert with focus on preventive care.",
            "Leading cardiologist with 18 years of clinical experience.",
            "Expert in complex cardiac interventions and catheterization.",
            "Renowned cardiac surgeon at Dhaka Medical College.",
            "Experienced pediatrician caring for children since 2005.",
            "Neonatal specialist with expertise in premature infant care.",
            "Child health specialist at Shishu Hospital Dhaka.",
            "Senior orthopedic surgeon with 200+ successful surgeries.",
            "Spine and disc disorder expert trained in Germany.",
            "Joint replacement specialist with advanced arthroscopy skills.",
            "Board-certified dermatologist treating all skin conditions.",
            "Cosmetic dermatology expert in laser and anti-aging.",
            "Skin, hair, and nail specialist with 10 years experience.",
        ]

        ratings = [4.8, 4.6, 4.7, 4.9, 4.7, 4.8, 4.6, 4.5, 4.7,
                   4.8, 4.9, 4.7, 4.6, 4.8, 4.5]

        doctor_password = bcrypt.hashpw(b'Doctor@1234', bcrypt.gensalt(12)).decode('utf-8')
        doctor_users = []
        for name, phone, carrier in doctor_data:
            u = User(
                full_name=name, phone_number=phone,
                password_hash=doctor_password,
                role="doctor", carrier=carrier, is_active=True
            )
            db.session.add(u)
            doctor_users.append(u)

        db.session.commit()

        # ── DOCTOR PROFILES ───────────────────────────────────────────────────
        doctors = []
        dept_index = [0,0,0, 1,1,1, 2,2,2, 3,3,3, 4,4,4]
        for i, u in enumerate(doctor_users):
            d = Doctor(
                user_id=u.user_id,
                dept_id=depts[dept_index[i]].dept_id,
                specialty=specialties[i],
                consultation_fee=fees[i],
                bio=bios[i],
                avg_rating=ratings[i]
            )
            db.session.add(d)
            doctors.append(d)
        db.session.commit()

        # ── TIME SLOTS (next 7 days, 9 AM–4 PM, Mon–Sat) ─────────────────────
        today = datetime.now(tz).date()
        for doctor in doctors:
            for days_offset in range(7):
                slot_date = today + timedelta(days=days_offset)
                if slot_date.weekday() == 6:   # skip Sunday
                    continue
                for hour in range(9, 17):
                    db.session.add(TimeSlot(
                        doctor_id=doctor.doctor_id,
                        slot_date=slot_date,
                        slot_time=time(hour, 0),
                        is_available=True
                    ))

        # ── SYMPTOMS MAP ──────────────────────────────────────────────────────
        symptoms = [
            # General Medicine
            ("fever",       0), ("cough",         0), ("headache",      0),
            ("cold",        0), ("fatigue",        0), ("vomiting",      0),
            # Cardiology
            ("chest pain",  1), ("heart",          1), ("palpitation",   1),
            ("shortness",   1), ("blood pressure", 1), ("hypertension",  1),
            # Pediatrics
            ("child",       2), ("baby",           2), ("infant",        2),
            ("growth",      2), ("vaccination",    2), ("kid",           2),
            # Orthopedics
            ("joint pain",  3), ("bone",           3), ("fracture",      3),
            ("back pain",   3), ("knee",           3), ("spine",         3),
            # Dermatology
            ("skin rash",   4), ("acne",           4), ("eczema",        4),
            ("itching",     4), ("hair loss",      4), ("allergy",       4),
        ]
        for keyword, di in symptoms:
            db.session.add(SymptomsMap(keyword=keyword, dept_id=depts[di].dept_id))

        db.session.commit()

        print("\n✅ Database initialized successfully!")
        print("=" * 50)
        print("TEST ACCOUNTS")
        print("=" * 50)
        print("ADMIN   → Phone: 8801700000000  | Password: Admin@1234")
        print("PATIENT → Phone: 8801711111111  | Password: Patient@1234")
        print("DOCTOR  → Phone: 8801722222201  | Password: Doctor@1234")
        print("=" * 50)
        print(f"15 doctors added across 5 departments (3 per dept)")
        print(f"Time slots created for next 7 days")


if __name__ == '__main__':
    init_db()
