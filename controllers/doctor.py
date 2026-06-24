from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Doctor, TimeSlot, Appointment, ConsultationNote
from utils.notifications import notify_completion, notify_booking, notify_cancellation
from utils.decorators import role_required
from datetime import datetime, timedelta
import pytz

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')
tz = pytz.timezone('Asia/Dhaka')

# Helper to get current doctor
def get_current_doctor():
    return Doctor.query.filter_by(user_id=current_user.user_id).first_or_404()

@doctor_bp.route('/dashboard')
@role_required('doctor')
def dashboard():
    doctor = get_current_doctor()
    
    # Today's date
    today = datetime.now(tz).date()
    
    # Today's appointments count
    today_appointments = Appointment.query.join(TimeSlot) \
        .filter(TimeSlot.doctor_id == doctor.doctor_id,
                TimeSlot.slot_date == today,
                Appointment.status.in_(['booked', 'confirmed'])) \
        .count()
    
    # Total unique patients count
    total_patients = db.session.query(Appointment.patient_id) \
        .join(TimeSlot) \
        .filter(TimeSlot.doctor_id == doctor.doctor_id) \
        .distinct() \
        .count()
    
    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         today_appointments=today_appointments,
                         total_patients=total_patients)

@doctor_bp.route('/schedule')
@role_required('doctor')
def schedule():
    doctor = get_current_doctor()
    today = datetime.now(tz).date()
    
    # Get upcoming appointments
    upcoming = Appointment.query.join(TimeSlot) \
        .filter(TimeSlot.doctor_id == doctor.doctor_id,
                TimeSlot.slot_date >= today,
                Appointment.status.in_(['booked', 'confirmed'])) \
        .order_by(TimeSlot.slot_date, TimeSlot.slot_time) \
        .all()
    
    # Get past appointments
    past = Appointment.query.join(TimeSlot) \
        .filter(TimeSlot.doctor_id == doctor.doctor_id,
                TimeSlot.slot_date < today) \
        .order_by(TimeSlot.slot_date.desc(), TimeSlot.slot_time.desc()) \
        .all()
    
    return render_template('doctor/schedule.html',
                         doctor=doctor,
                         upcoming=upcoming,
                         past=past)

@doctor_bp.route('/slots')
@role_required('doctor')
def slots():
    doctor = get_current_doctor()
    start_date = datetime.now(tz).date()
    end_date = start_date + timedelta(days=14)
    
    # Get slots for next 14 days
    slots = TimeSlot.query.filter(
        TimeSlot.doctor_id == doctor.doctor_id,
        TimeSlot.slot_date >= start_date,
        TimeSlot.slot_date <= end_date
    ).order_by(TimeSlot.slot_date, TimeSlot.slot_time).all()
    
    # Group by date
    slots_by_date = {}
    for slot in slots:
        date_key = slot.slot_date
        if date_key not in slots_by_date:
            slots_by_date[date_key] = []
        slots_by_date[date_key].append(slot)
    
    return render_template('doctor/slots.html',
                         doctor=doctor,
                         slots_by_date=slots_by_date,
                         start_date=start_date,
                         end_date=end_date)

@doctor_bp.route('/toggle-slot/<int:slot_id>', methods=['POST'])
@role_required('doctor')
def toggle_slot(slot_id):
    doctor = get_current_doctor()
    slot = TimeSlot.query.get_or_404(slot_id)
    
    # Verify slot belongs to doctor
    if slot.doctor_id != doctor.doctor_id:
        return jsonify({'success': False, 'message': 'This slot does not belong to you'}), 403
    
    # Check for active appointment
    active_appt = Appointment.query.filter_by(slot_id=slot_id, status='booked').first()
    if active_appt:
        return jsonify({'success': False, 'message': 'Cannot toggle slot with active booking'}), 400
    
    # Toggle availability
    slot.is_available = not slot.is_available
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_available': slot.is_available,
        'message': f"Slot {'available' if slot.is_available else 'unavailable'} now"
    })

@doctor_bp.route('/add-slots', methods=['POST'])
@role_required('doctor')
def add_slots():
    doctor = get_current_doctor()
    data = request.get_json()
    
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    times = data.get('times', [])
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    if not times:
        return jsonify({'success': False, 'message': 'No times provided'}), 400
    
    created_count = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Skip weekends (Saturday=5, Sunday=6)
        if current_date.weekday() not in [5, 6]:
            for time_str in times:
                try:
                    # Convert time string to time object
                    slot_time = datetime.strptime(time_str, '%H:%M').time()
                except ValueError:
                    continue
                
                # Check if slot already exists
                existing = TimeSlot.query.filter_by(
                    doctor_id=doctor.doctor_id,
                    slot_date=current_date,
                    slot_time=slot_time
                ).first()
                
                if not existing:
                    new_slot = TimeSlot(
                        doctor_id=doctor.doctor_id,
                        slot_date=current_date,
                        slot_time=slot_time,
                        is_available=True
                    )
                    db.session.add(new_slot)
                    created_count += 1
        
        current_date += timedelta(days=1)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'created_count': created_count,
        'message': f'Successfully created {created_count} new slots!'
    })

@doctor_bp.route('/appointment/<int:appt_id>')
@role_required('doctor')
def appointment_detail(appt_id):
    doctor = get_current_doctor()
    appointment = Appointment.query.get_or_404(appt_id)
    
    # Verify appointment belongs to doctor
    if appointment.time_slot.doctor_id != doctor.doctor_id:
        flash('This appointment does not belong to you.', 'danger')
        return redirect(url_for('doctor.schedule'))
    
    # Get previous notes for this patient by this doctor
    previous_notes = ConsultationNote.query \
        .filter_by(doctor_id=doctor.doctor_id, patient_id=appointment.patient_id) \
        .order_by(ConsultationNote.created_at.desc()) \
        .all()
    
    return render_template('doctor/appointment_detail.html',
                         doctor=doctor,
                         appointment=appointment,
                         previous_notes=previous_notes)

@doctor_bp.route('/add-note/<int:appt_id>', methods=['POST'])
@role_required('doctor')
def add_note(appt_id):
    doctor = get_current_doctor()
    appointment = Appointment.query.get_or_404(appt_id)
    
    # Verify appointment belongs to doctor
    if appointment.time_slot.doctor_id != doctor.doctor_id:
        flash('This appointment does not belong to you.', 'danger')
        return redirect(url_for('doctor.schedule'))
    
    note_text = request.form.get('note_text', '').strip()
    if note_text:
        new_note = ConsultationNote(
            appointment_id=appt_id,
            doctor_id=doctor.doctor_id,
            patient_id=appointment.patient_id,
            note_text=note_text
        )
        db.session.add(new_note)
    
    # Mark appointment as completed
    appointment.status = 'completed'
    db.session.commit()
    
    # Send notification
    notify_completion(appointment.patient, doctor.user.full_name)
    
    flash('Consultation note added and appointment marked as completed!', 'success')
    return redirect(url_for('doctor.schedule'))

@doctor_bp.route('/patient-history/<int:patient_id>')
@role_required('doctor')
def patient_history(patient_id):
    doctor = get_current_doctor()
    
    # Get all past appointments with this patient
    past_appointments = Appointment.query.join(TimeSlot) \
        .filter(TimeSlot.doctor_id == doctor.doctor_id,
                Appointment.patient_id == patient_id,
                Appointment.status.in_(['completed', 'cancelled'])) \
        .order_by(TimeSlot.slot_date.desc()) \
        .all()
    
    # Get all consultation notes
    notes = ConsultationNote.query.filter_by(
        doctor_id=doctor.doctor_id,
        patient_id=patient_id
    ).order_by(ConsultationNote.created_at.desc()).all()
    
    return render_template('doctor/patient_history.html',
                         doctor=doctor,
                         patient_id=patient_id,
                         past_appointments=past_appointments,
                         notes=notes)
