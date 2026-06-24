from extensions import db


class Department(db.Model):
    __tablename__ = 'departments'
    
    dept_id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon_name = db.Column(db.String(50), nullable=True)
