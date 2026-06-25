from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Doctor, Department, TimeSlot, Appointment, Rating
from utils.recommender import get_recommended_department
from utils.notifications import notify_booking, notify_cancellation, notify_completion
from utils.decorators import role_required
from datetime import datetime, timedelta
import pytz

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')
tz = pytz.timezone('Asia/Dhaka')


@patient_bp.route('/dashboard')
@role_required('patient')
def dashboard():
    # Upcoming appointments (list for display)
    upcoming_list = Appointment.query.filter(
        Appointment.patient_id == current_user.user_id,
        Appointment.status.in_(['booked', 'confirmed'])
    ).join(TimeSlot).order_by(TimeSlot.slot_date, TimeSlot.slot_time).all()

    upcoming_count    = len(upcoming_list)
    completed_count   = Appointment.query.filter(
        Appointment.patient_id == current_user.user_id,
        Appointment.status == 'completed'
    ).count()
    total_count       = Appointment.query.filter(
        Appointment.patient_id == current_user.user_id
    ).count()
    ratings_given     = Rating.query.filter(
        Rating.patient_id == current_user.user_id
    ).count()

    return render_template('patient/dashboard.html',
                           appointments=upcoming_list,
                           upcoming_count=upcoming_count,
                           completed_count=completed_count,
                           total_count=total_count,
                           ratings_given=ratings_given)


@patient_bp.route('/browse-doctors')
@role_required('patient')
def browse_doctors():
    dept_id     = request.args.get('dept_id', type=int)
    departments = Department.query.all()
    query       = Doctor.query.join(User).join(Department)
    if dept_id:
        query = query.filter(Doctor.dept_id == dept_id)
    doctors = query.order_by(Doctor.avg_rating.desc()).all()
    return render_template('patient/browse_doctors.html',
                           doctors=doctors,
                           departments=departments,
                           selected_dept=dept_id)


@patient_bp.route('/recommend', methods=['POST'])
@role_required('patient')
def recommend():
    data         = request.get_json()
    symptom_text = data.get('symptom_text', '')
    result       = get_recommended_department(symptom_text)
    return jsonify(result if result else {'dept_id': None})


@patient_bp.route('/calendar/<int:doctor_id>')
@role_required('patient')
def calendar(doctor_id):
    doctor     = Doctor.query.get_or_404(doctor_id)
    start_date = datetime.now(tz).date()
    end_date   = start_date + timedelta(days=14)

    slots = TimeSlot.query.filter(
        TimeSlot.doctor_id == doctor_id,
        TimeSlot.slot_date >= start_date,
        TimeSlot.slot_date <= end_date
    ).all()

    booked_slot_ids = [
        a.slot_id for a in Appointment.query.filter(
            Appointment.slot_id.in_([s.slot_id for s in slots])
        ).all()
    ]

    calendar_data = {}
    for slot in slots:
        date_str = slot.slot_date.isoformat()
        if date_str not in calendar_data:
            calendar_data[date_str] = []
        calendar_data[date_str].append({
            'slot_id':      slot.slot_id,
            'slot_time':    slot.slot_time.strftime('%I:%M %p'),
            'is_available': slot.is_available,
            'is_booked':    slot.slot_id in booked_slot_ids
        })

    if request.headers.get('Accept') == 'application/json':
        return jsonify(calendar_data)
    return render_template('patient/calendar.html', doctor=doctor)


@patient_bp.route('/book/<int:slot_id>', methods=['POST'])
@role_required('patient')
def book(slot_id):
    slot = TimeSlot.query.get_or_404(slot_id)
    if not slot.is_available:
        flash('This slot is no longer available.', 'danger')
        return redirect(url_for('patient.browse_doctors'))

    reason = request.form.get('reason_for_visit', '')
    appt   = Appointment(
        patient_id=current_user.user_id,
        slot_id=slot_id,
        reason_for_visit=reason,
        status='booked',
        booked_at=datetime.now(tz)
    )
    slot.is_available = False
    db.session.add(appt)
    db.session.commit()

    doctor = slot.doctor
    notify_booking(current_user, doctor.user, slot.slot_date,
                   slot.slot_time, doctor.user.full_name)
    flash('Appointment booked successfully!', 'success')
    return redirect(url_for('patient.dashboard'))


@patient_bp.route('/cancel/<int:appt_id>', methods=['POST'])
@role_required('patient')
def cancel(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.patient_id != current_user.user_id:
        flash('You cannot cancel this appointment.', 'danger')
        return redirect(url_for('patient.appointments'))
    if not appt.can_cancel():
        flash('Cannot cancel — appointment is less than 24 hours away.', 'danger')
        return redirect(url_for('patient.appointments'))

    appt.status              = 'cancelled'
    appt.time_slot.is_available = True
    db.session.commit()

    doctor = appt.time_slot.doctor
    notify_cancellation(current_user, doctor.user,
                        appt.time_slot.slot_date, appt.time_slot.slot_time)
    flash('Appointment cancelled successfully.', 'info')
    return redirect(url_for('patient.appointments'))


@patient_bp.route('/appointments')
@role_required('patient')
def appointments():
    upcoming = Appointment.query.filter(
        Appointment.patient_id == current_user.user_id,
        Appointment.status.in_(['booked', 'confirmed'])
    ).join(TimeSlot).order_by(TimeSlot.slot_date, TimeSlot.slot_time).all()

    past = Appointment.query.filter(
        Appointment.patient_id == current_user.user_id,
        Appointment.status.in_(['completed', 'cancelled'])
    ).join(TimeSlot).order_by(
        TimeSlot.slot_date.desc(), TimeSlot.slot_time.desc()
    ).all()

    return render_template('patient/appointments.html',
                           upcoming=upcoming, past=past)


@patient_bp.route('/rate/<int:appt_id>', methods=['POST'])
@role_required('patient')
def rate(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.patient_id != current_user.user_id:
        return jsonify({'success': False, 'error': 'Not your appointment'}), 403
    if appt.status != 'completed':
        return jsonify({'success': False, 'error': 'Cannot rate uncompleted appointment'}), 400
    if Rating.query.filter_by(appointment_id=appt_id).first():
        return jsonify({'success': False, 'error': 'Already rated'}), 400

    data   = request.get_json()
    rating = Rating(
        patient_id=current_user.user_id,
        doctor_id=appt.time_slot.doctor_id,
        appointment_id=appt_id,
        stars=data.get('stars', 5),
        review_text=data.get('review_text', '')
    )
    db.session.add(rating)
    db.session.commit()

    doctor = appt.time_slot.doctor
    doctor.update_avg_rating()
    db.session.commit()
    return jsonify({'success': True, 'new_avg_rating': float(doctor.avg_rating)})
