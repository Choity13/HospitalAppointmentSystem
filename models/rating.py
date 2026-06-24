from extensions import db
from datetime import datetime


class Rating(db.Model):
    __tablename__ = 'ratings'
    
    rating_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appt_id'), unique=True, nullable=False)
    stars = db.Column(db.Integer, db.CheckConstraint('stars >= 1 AND stars <= 5'), nullable=False)
    review_text = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='ratings')
    doctor = db.relationship('Doctor', backref='ratings')
    appointment = db.relationship('Appointment', backref=db.backref('rating', uselist=False))
