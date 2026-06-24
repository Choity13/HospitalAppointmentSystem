from extensions import db
from sqlalchemy import func


class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    doctor_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    specialty = db.Column(db.String(100), nullable=True)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avg_rating = db.Column(db.Numeric(3, 2), default=0.0, nullable=False)
    total_ratings = db.Column(db.Integer, default=0, nullable=False)
    
    user = db.relationship('User', backref=db.backref('doctor', uselist=False))
    department = db.relationship('Department', backref='doctors')
    
    def update_avg_rating(self):
        from models.rating import Rating
        
        ratings = Rating.query.filter_by(doctor_id=self.doctor_id).all()
        self.total_ratings = len(ratings)
        
        if self.total_ratings > 0:
            total_stars = sum(r.stars for r in ratings)
            self.avg_rating = round(total_stars / self.total_ratings, 2)
        else:
            self.avg_rating = 0.0
