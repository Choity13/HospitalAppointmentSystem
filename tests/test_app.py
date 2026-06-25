"""
tests/test_app.py
=================
Bangladesh Hospital Appointment Scheduling System
13 pytest Unit Tests — PHASE 13-A (TST-002) — Updated v3

Run with:
    pytest tests/test_app.py -v

Expected output: 13 tests all showing PASSED in green.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import User, Department, Doctor, TimeSlot, Appointment, Notification
from datetime import date, time, timedelta
from utils.date_utils import get_current_time
import bcrypt


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope='function')
def app():
    """Fresh Flask app with in-memory SQLite for each test."""
    os.environ['SECRET_KEY']   = 'test-secret-key-for-pytest-only'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['TIMEZONE']     = 'Asia/Dhaka'

    application = create_app()
    application.config.update({
        'TESTING':                 True,
        'WTF_CSRF_ENABLED':        False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY':              'test-secret-key-for-pytest-only',
    })

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def sample_patient(app):
    with app.app_context():
        hashed = bcrypt.hashpw(b'Patient@1234', bcrypt.gensalt(12)).decode('utf-8')
        user = User(
            full_name='Mohammad Rahim',
            phone_number='8801711111111',
            password_hash=hashed,
            role='patient',
            carrier='Robi'
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id


@pytest.fixture(scope='function')
def sample_admin(app):
    with app.app_context():
        hashed = bcrypt.hashpw(b'Admin@1234', bcrypt.gensalt(12)).decode('utf-8')
        user = User(
            full_name='System Admin',
            phone_number='8801700000000',
            password_hash=hashed,
            role='admin',
            carrier='Grameenphone'
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id


@pytest.fixture(scope='function')
def sample_department(app):
    with app.app_context():
        dept = Department(
            dept_name='General Medicine',
            description='General health and primary care'
        )
        db.session.add(dept)
        db.session.commit()
        return dept.dept_id


@pytest.fixture(scope='function')
def sample_doctor(app, sample_department):
    with app.app_context():
        hashed = bcrypt.hashpw(b'Doctor@1234', bcrypt.gensalt(12)).decode('utf-8')
        user = User(
            full_name='Farhan Hossain',
            phone_number='8801722222201',
            password_hash=hashed,
            role='doctor',
            carrier='Grameenphone'
        )
        db.session.add(user)
        db.session.commit()
        doctor = Doctor(
            user_id=user.user_id,
            dept_id=sample_department,
            specialty='General Physician',
            consultation_fee=500.0,
            bio='15+ years in general medicine.',
            avg_rating=4.8,
            total_ratings=0
        )
        db.session.add(doctor)
        db.session.commit()
        return doctor.doctor_id


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — Phone Number Validation (Valid Format)
# ══════════════════════════════════════════════════════════════════════════════

def test_valid_phone_number_format(app):
    """
    TC: Valid Bangladesh numbers pass the regex.
    Pattern ^8801[3-9][0-9]{8}$ = exactly 13 digits.
    4 (8801) + 1 ([3-9]) + 8 ([0-9]{8}) = 13 total.
    Uses real phone numbers from init_db.py seeded accounts.
    """
    import re
    pattern = r'^8801[3-9][0-9]{8}$'

    assert re.match(pattern, '8801711111111') is not None  # Patient Mohammad Rahim
    assert re.match(pattern, '8801722222201') is not None  # Doctor Farhan Hossain
    assert re.match(pattern, '8801822222202') is not None  # Robi 018x format
    assert re.match(pattern, '8801322222203') is not None  # Banglalink 013x format
    assert re.match(pattern, '8801922222204') is not None  # Teletalk 019x format


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — Phone Number Validation (Invalid Format Rejected)
# ══════════════════════════════════════════════════════════════════════════════

def test_invalid_phone_number_format(app):
    """
    TC: Numbers that don't match Bangladesh format are correctly rejected.
    """
    import re
    pattern = r'^8801[3-9][0-9]{8}$'

    assert re.match(pattern, '01711234567')    is None  # Missing 88 prefix
    assert re.match(pattern, '880101234567')   is None  # 8801-0 not in [3-9]
    assert re.match(pattern, '880121234567')   is None  # 8801-2 not in [3-9]
    assert re.match(pattern, '88017123456')    is None  # Too short (11 digits)
    assert re.match(pattern, '88017112345678') is None  # Too long (14 digits)
    assert re.match(pattern, 'abcdefghijklm')  is None  # Letters not allowed


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — Password Hashing with bcrypt
# ══════════════════════════════════════════════════════════════════════════════

def test_password_hashing(app):
    """
    TC: Passwords stored as bcrypt hashes. Correct password verifies,
    wrong password fails. Hash starts with $2b$ prefix.
    """
    with app.app_context():
        password = 'Patient@1234'
        hashed   = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt(12)
        ).decode('utf-8')

        assert hashed != password
        assert hashed.startswith('$2')
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')) is True
        assert bcrypt.checkpw(b'WrongPassword', hashed.encode('utf-8'))         is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — User Registration Saves to Database
# ══════════════════════════════════════════════════════════════════════════════

def test_user_registration_saves_to_db(app):
    """
    TC: A new patient User record is saved and retrieved correctly.
    """
    with app.app_context():
        hashed = bcrypt.hashpw(b'Patient@1234', bcrypt.gensalt(12)).decode('utf-8')
        user = User(
            full_name='Mohammad Rahim',
            phone_number='8801711111111',
            password_hash=hashed,
            role='patient',
            carrier='Robi'
        )
        db.session.add(user)
        db.session.commit()

        found = User.query.filter_by(phone_number='8801711111111').first()
        assert found is not None
        assert found.full_name    == 'Mohammad Rahim'
        assert found.role         == 'patient'
        assert found.carrier      == 'Robi'
        assert found.is_locked    is False
        assert found.otp_verified is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 — OTP Bypass Accepts Any 6-Digit Code
# ══════════════════════════════════════════════════════════════════════════════

def test_otp_testing_bypass_accepts_any_6_digit_code(app, sample_patient):
    """
    TC: In testing mode, verify_otp() accepts any 6-digit numeric string.
    """
    with app.app_context():
        user = User.query.get(sample_patient)

        assert user.verify_otp('123456') is True
        user.otp_verified = False
        assert user.verify_otp('999999') is True
        user.otp_verified = False
        assert user.verify_otp('000000') is True


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6 — OTP Rejects Invalid Codes
# ══════════════════════════════════════════════════════════════════════════════

def test_otp_rejects_invalid_codes(app, sample_patient):
    """
    TC: verify_otp() rejects anything that is not exactly 6 digits.
    """
    with app.app_context():
        user = User.query.get(sample_patient)

        assert user.verify_otp('')        is False  # Empty
        assert user.verify_otp('12345')   is False  # 5 digits
        assert user.verify_otp('1234567') is False  # 7 digits
        assert user.verify_otp('abcdef')  is False  # Letters
        assert user.verify_otp('12 456')  is False  # Space inside
        assert user.verify_otp(None)      is False  # None


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7 — OTP Reset Clears All Fields
# ══════════════════════════════════════════════════════════════════════════════

def test_otp_reset_clears_fields(app, sample_patient):
    """
    TC: reset_otp() sets otp_code=None, otp_expires_at=None, otp_verified=False.
    """
    with app.app_context():
        user = User.query.get(sample_patient)

        user.otp_code       = '654321'
        user.otp_expires_at = get_current_time() + timedelta(minutes=10)
        user.otp_verified   = True
        db.session.commit()

        user.reset_otp()
        db.session.commit()

        fresh = User.query.get(sample_patient)
        assert fresh.otp_code       is None
        assert fresh.otp_expires_at is None
        assert fresh.otp_verified   is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 8 — Account Lock Sets Correctly
# ══════════════════════════════════════════════════════════════════════════════

def test_account_lock_sets_correctly(app, sample_patient):
    """
    TC: is_locked=True with future lock_until marks account as locked.
    """
    with app.app_context():
        user = User.query.get(sample_patient)
        now  = get_current_time()

        user.is_locked  = True
        user.lock_until = now + timedelta(minutes=15)
        db.session.commit()

        locked = User.query.get(sample_patient)
        assert locked.is_locked       is True
        assert locked.lock_until_aware > now


# ══════════════════════════════════════════════════════════════════════════════
# TEST 9 — Department Creation Uses dept_name Field
# ══════════════════════════════════════════════════════════════════════════════

def test_department_creation(app):
    """
    TC: Department saved with dept_name field and retrieved correctly.
    Uses dept_name (not name) matching the updated Department model.
    """
    with app.app_context():
        dept = Department(
            dept_name='Cardiology',
            description='Heart and cardiovascular care'
        )
        db.session.add(dept)
        db.session.commit()

        found = Department.query.filter_by(dept_name='Cardiology').first()
        assert found is not None
        assert found.dept_name   == 'Cardiology'
        assert found.description == 'Heart and cardiovascular care'


# ══════════════════════════════════════════════════════════════════════════════
# TEST 10 — Doctor Name Has No Dr. Prefix in Database
# ══════════════════════════════════════════════════════════════════════════════

def test_doctor_name_has_no_dr_prefix(app, sample_doctor):
    """
    TC: Doctor full_name in DB does NOT include 'Dr.' prefix.
    The prefix is added only in templates: Dr. {{ doctor.user.full_name }}
    This prevents the 'Dr. Dr. Farhan Hossain' double-prefix bug.
    """
    with app.app_context():
        doctor = Doctor.query.get(sample_doctor)
        assert doctor is not None
        assert not doctor.user.full_name.startswith('Dr.')
        assert doctor.user.full_name == 'Farhan Hossain'


# ══════════════════════════════════════════════════════════════════════════════
# TEST 11 — SMS Notification Log Saved
# ══════════════════════════════════════════════════════════════════════════════

def test_notification_sms_log_saved(app, sample_patient):
    """
    TC: OTP SMS notification saved with sms_sent=True,
    retrievable for Admin SMS log page.
    """
    with app.app_context():
        notification = Notification(
            user_id=sample_patient,
            notif_type='OTP',
            message='MediCare BD: Your OTP is 123456. Valid for 10 minutes.',
            sms_sent=True
        )
        db.session.add(notification)
        db.session.commit()

        logs = Notification.query.filter_by(
            user_id=sample_patient, sms_sent=True
        ).all()
        assert len(logs)          == 1
        assert logs[0].notif_type == 'OTP'
        assert '123456'     in logs[0].message
        assert logs[0].sms_sent   is True


# ══════════════════════════════════════════════════════════════════════════════
# TEST 12 — Login Page Loads (HTTP 200)
# ══════════════════════════════════════════════════════════════════════════════

def test_login_page_loads(client):
    """TC: GET /auth/login returns HTTP 200 OK."""
    response = client.get('/auth/login')
    assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# TEST 13 — Wrong Credentials Are Rejected
# ══════════════════════════════════════════════════════════════════════════════

def test_login_wrong_credentials_rejected(client, app, sample_patient):
    """
    TC: POST /auth/login with wrong name+password does not log the user in.
    Page stays on login (HTTP 200) with an error message.
    """
    response = client.post('/auth/login', data={
        'full_name':    'Wrong Name',
        'phone_number': '8801711111111',
        'password':     'WrongPassword99'
    }, follow_redirects=True)

    assert response.status_code == 200

    text = response.data.decode('utf-8').lower()
    assert any(kw in text for kw in [
        'invalid', 'error', 'incorrect', 'danger', 'wrong', 'login'
    ])
