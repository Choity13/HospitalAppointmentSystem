from extensions import db
from flask_login import UserMixin
import bcrypt
from datetime import datetime, timedelta
from utils.date_utils import make_tz_aware, get_current_time


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('patient', 'doctor', 'admin', name='user_roles'), default='patient', nullable=False)
    carrier = db.Column(db.Enum('Grameenphone', 'Robi', 'Banglalink', 'Teletalk', 'Airtel', name='carriers'), nullable=True)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    lock_until = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time)
    
    @property
    def otp_expires_at_aware(self):
        return make_tz_aware(self.otp_expires_at)
    
    @property
    def lock_until_aware(self):
        return make_tz_aware(self.lock_until)
    
    @property
    def created_at_aware(self):
        return make_tz_aware(self.created_at)
    
    def get_id(self):
        return str(self.user_id)
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def verify_otp(self, code):
        """
        TESTING MODE: Accept any 6-digit number as a valid OTP.
        
        To switch back to PRODUCTION (strict matching), replace this
        entire method body with:
        
            now = get_current_time()
            if (self.otp_code and
                    code == self.otp_code and
                    self.otp_expires_at_aware > now):
                self.otp_verified = True
                return True
            return False
        """
        # --- TESTING BYPASS: accept any 6-digit code ---
        if code and len(code) == 6 and code.isdigit():
            self.otp_verified = True
            return True
        return False
    
    def reset_otp(self):
        self.otp_code = None
        self.otp_expires_at = None
        self.otp_verified = False
