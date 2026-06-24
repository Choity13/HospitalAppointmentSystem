from extensions import db
from datetime import datetime
from utils.date_utils import make_tz_aware, get_current_time


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notif_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), index=True, nullable=False)
    notif_type = db.Column(db.Enum('OTP', 'booking', 'cancellation', 'reminder', 'completion', name='notif_types'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sms_sent = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time)
    
    user = db.relationship('User', backref='notifications')
    
    @property
    def created_at_aware(self):
        return make_tz_aware(self.created_at)
