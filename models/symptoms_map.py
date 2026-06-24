from extensions import db


class SymptomsMap(db.Model):
    __tablename__ = 'symptoms_map'
    
    symptom_id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(50), nullable=False)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    
    department = db.relationship('Department', backref='symptoms_map')
