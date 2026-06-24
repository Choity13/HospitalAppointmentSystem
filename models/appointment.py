from extensions import db
from datetime import datetime, timedelta
from utils.date_utils import make_tz_aware, get_current_time, tz


class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    appt_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), index=True, nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.slot_id'), unique=True, nullable=False)
    reason_for_visit = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('booked', 'confirmed', 'completed', 'cancelled', name='appt_status'), default='booked', nullable=False)
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)
    booked_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='appointments')
    time_slot = db.relationship('TimeSlot', backref=db.backref('appointment', uselist=False))
    
    @property
    def booked_at_aware(self):
        return make_tz_aware(self.booked_at)
    
    @property
    def updated_at_aware(self):
        return make_tz_aware(self.updated_at)
    
    def can_cancel(self):
        now = get_current_time()
        
        slot_datetime = datetime.combine(
            self.time_slot.slot_date, 
            self.time_slot.slot_time
        )
        slot_datetime = tz.localize(slot_datetime)
        
        return (slot_datetime - now) > timedelta(hours=24)
