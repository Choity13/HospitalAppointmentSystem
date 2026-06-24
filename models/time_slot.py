from extensions import db


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    
    slot_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id', ondelete='CASCADE'), nullable=False)
    slot_date = db.Column(db.Date, index=True, nullable=False)
    slot_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    
    doctor = db.relationship('Doctor', backref='time_slots')
