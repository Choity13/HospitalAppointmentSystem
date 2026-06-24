from flask import Flask, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from extensions import db, login_manager
from models import User
import os
from dotenv import load_dotenv

scheduler = BackgroundScheduler()


def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from controllers.auth import auth_bp
    from controllers.patient import patient_bp
    from controllers.doctor import doctor_bp
    from controllers.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    @app.route('/')
    def home():
        return redirect('/auth/login')
    
    from utils.notifications import check_reminders
    
    if not scheduler.running:
        scheduler.add_job(
            func=check_reminders,
            trigger='interval',
            minutes=30,
            timezone='Asia/Dhaka'
        )
        scheduler.start()
    
    return app
