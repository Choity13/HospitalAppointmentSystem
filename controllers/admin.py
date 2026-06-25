from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Doctor, Department, TimeSlot, Appointment, Notification
from utils.decorators import role_required
from datetime import datetime, timedelta
import pytz
import bcrypt

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
tz = pytz.timezone('Asia/Dhaka')


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    today = datetime.now(tz).date()

    total_patients     = User.query.filter_by(role='patient', is_active=True).count()
    total_doctors      = Doctor.query.join(User).filter(User.is_active == True).count()
    total_depts        = Department.query.count()
    total_appointments = Appointment.query.count()

    # Recent 10 appointments for the table (cross-role: shows all patients & doctors)
    recent_appointments = Appointment.query\
        .join(TimeSlot)\
        .order_by(TimeSlot.slot_date.desc(), TimeSlot.slot_time.desc())\
        .limit(10).all()

    return render_template('admin/dashboard.html',
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           total_depts=total_depts,
                           total_appointments=total_appointments,
                           recent_appointments=recent_appointments)


@admin_bp.route('/doctors', methods=['GET', 'POST'])
@role_required('admin')
def doctors():
    doctors     = Doctor.query.join(User).join(Department)\
                    .filter(User.is_active == True)\
                    .order_by(User.full_name).all()
    departments = Department.query.all()
    return render_template('admin/doctors.html',
                           doctors=doctors, departments=departments)


@admin_bp.route('/add-doctor', methods=['GET', 'POST'])
@role_required('admin')
def add_doctor():
    departments = Department.query.all()
    if request.method == 'POST':
        existing_user_id = request.form.get('existing_user_id', '').strip()
        if existing_user_id:
            user = User.query.get(int(existing_user_id))
            if not user or user.role != 'doctor':
                flash('Invalid user selected.', 'danger')
                return redirect(url_for('admin.add_doctor'))
        else:
            full_name = request.form.get('full_name').strip()
            phone     = request.form.get('phone').strip()
            password  = request.form.get('password')
            user = User(
                full_name=full_name,
                phone_number=phone,
                password_hash=bcrypt.hashpw(
                    password.encode('utf-8'), bcrypt.gensalt(12)
                ).decode('utf-8'),
                role='doctor'
            )
            db.session.add(user)
            db.session.commit()

        if Doctor.query.filter_by(user_id=user.user_id).first():
            flash('Doctor profile already exists for this user.', 'danger')
            return redirect(url_for('admin.add_doctor'))

        doctor = Doctor(
            user_id=user.user_id,
            dept_id=int(request.form.get('department')),
            specialty=request.form.get('specialty', '').strip(),
            consultation_fee=float(request.form.get('consultation_fee')),
            bio=request.form.get('bio', '').strip(),
            avg_rating=0.0,
            total_ratings=0
        )
        db.session.add(doctor)
        db.session.commit()
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin.doctors'))

    existing_doctor_users = User.query.filter_by(role='doctor', is_active=True)\
        .outerjoin(Doctor, Doctor.user_id == User.user_id)\
        .filter(Doctor.user_id.is_(None)).all()
    return render_template('admin/add_doctor.html',
                           departments=departments,
                           existing_doctor_users=existing_doctor_users)


@admin_bp.route('/edit-doctor/<int:doctor_id>', methods=['POST'])
@role_required('admin')
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.dept_id          = int(request.form.get('department'))
    doctor.specialty        = request.form.get('specialty', '').strip()
    doctor.consultation_fee = float(request.form.get('consultation_fee'))
    doctor.bio              = request.form.get('bio', '').strip()
    db.session.commit()
    flash('Doctor updated successfully!', 'success')
    return redirect(url_for('admin.doctors'))


@admin_bp.route('/delete-doctor/<int:doctor_id>', methods=['POST'])
@role_required('admin')
def delete_doctor(doctor_id):
    doctor      = Doctor.query.get_or_404(doctor_id)
    doctor.user.is_active = False
    db.session.commit()
    flash('Doctor deactivated successfully!', 'info')
    return redirect(url_for('admin.doctors'))


@admin_bp.route('/departments', methods=['GET', 'POST'])
@role_required('admin')
def departments():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            db.session.add(Department(
                dept_name=request.form.get('dept_name').strip(),
                description=request.form.get('description', '').strip(),
                icon_name=request.form.get('icon_name', '').strip()
            ))
            db.session.commit()
            flash('Department added successfully!', 'success')
        elif action == 'edit':
            dept = Department.query.get_or_404(int(request.form.get('dept_id')))
            dept.dept_name   = request.form.get('dept_name').strip()
            dept.description = request.form.get('description', '').strip()
            dept.icon_name   = request.form.get('icon_name', '').strip()
            db.session.commit()
            flash('Department updated successfully!', 'success')
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)


@admin_bp.route('/reports')
@role_required('admin')
def reports():
    return render_template('admin/reports.html')


@admin_bp.route('/sms-log')
@role_required('admin')
def sms_log():
    page       = request.args.get('page', 1, type=int)
    notif_type = request.args.get('type', '')
    search     = request.args.get('search', '').strip()
    query      = Notification.query.join(User, User.user_id == Notification.user_id)
    if notif_type:
        query = query.filter(Notification.notif_type == notif_type)
    if search:
        query = query.filter(User.phone_number.contains(search))
    pagination = query.order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/sms_log.html',
                           notifications=pagination.items,
                           pagination=pagination,
                           notif_type=notif_type,
                           search=search)


# ── API endpoints for Charts ────────────────────────────────────────────────

@admin_bp.route('/api/appointments-per-doctor')
@role_required('admin')
def api_appointments_per_doctor():
    thirty_days_ago = datetime.now(tz).date() - timedelta(days=30)
    results = db.session.query(
        User.full_name,
        db.func.count(Appointment.appt_id).label('count')
    ).join(Doctor, Doctor.user_id == User.user_id)\
     .join(TimeSlot, TimeSlot.doctor_id == Doctor.doctor_id)\
     .join(Appointment, Appointment.slot_id == TimeSlot.slot_id)\
     .filter(TimeSlot.slot_date >= thirty_days_ago)\
     .group_by(User.user_id).all()
    return jsonify({'labels': [r.full_name for r in results],
                    'data':   [r.count     for r in results]})


@admin_bp.route('/api/daily-flow')
@role_required('admin')
def api_daily_flow():
    end_date   = datetime.now(tz).date()
    start_date = end_date - timedelta(days=13)
    results = db.session.query(
        TimeSlot.slot_date,
        db.func.count(Appointment.appt_id).label('count')
    ).join(Appointment, Appointment.slot_id == TimeSlot.slot_id)\
     .filter(TimeSlot.slot_date >= start_date)\
     .group_by(TimeSlot.slot_date)\
     .order_by(TimeSlot.slot_date).all()
    date_counts  = {r.slot_date: r.count for r in results}
    labels, data = [], []
    cur = start_date
    while cur <= end_date:
        labels.append(cur.strftime('%d %b'))
        data.append(date_counts.get(cur, 0))
        cur += timedelta(days=1)
    return jsonify({'labels': labels, 'data': data})


@admin_bp.route('/api/status-breakdown')
@role_required('admin')
def api_status_breakdown():
    statuses = ['booked', 'confirmed', 'completed', 'cancelled']
    data     = [Appointment.query.filter_by(status=s).count() for s in statuses]
    return jsonify({'labels': statuses, 'data': data})


@admin_bp.route('/api/dept-distribution')
@role_required('admin')
def api_dept_distribution():
    results = db.session.query(
        Department.dept_name,
        db.func.count(db.func.distinct(Appointment.patient_id)).label('count')
    ).join(Doctor, Doctor.dept_id == Department.dept_id)\
     .join(TimeSlot, TimeSlot.doctor_id == Doctor.doctor_id)\
     .join(Appointment, Appointment.slot_id == TimeSlot.slot_id)\
     .group_by(Department.dept_id).all()
    return jsonify({'labels': [r.dept_name for r in results],
                    'data':   [r.count     for r in results]})
