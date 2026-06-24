from extensions import db
from datetime import datetime


class ConsultationNote(db.Model):
    __tablename__ = 'consultation_notes'
    
    note_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appt_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    appointment = db.relationship('Appointment', backref='consultation_notes')
    doctor = db.relationship('Doctor', backref='consultation_notes')
    patient = db.relationship('User', foreign_keys=[patient_id])
