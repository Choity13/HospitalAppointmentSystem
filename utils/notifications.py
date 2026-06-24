from models import Notification, Appointment
from extensions import db
from datetime import datetime, timedelta
from utils.date_utils import make_tz_aware, get_current_time, tz


def create_notification(user_id, notif_type, message):
    """
    Creates a Notification record with sms_sent=True and Asia/Dhaka timestamp.
    """
    notification = Notification(
        user_id=user_id,
        notif_type=notif_type,
        message=message,
        sms_sent=True
    )
    db.session.add(notification)
    db.session.commit()


def notify_otp(user, otp_code):
    """
    Sends OTP notification to user.
    """
    print(f"=== OTP for {user.full_name} ({user.phone_number}): {otp_code} ===")
    message = f"Bangladesh Hospital System: Your login verification code is {otp_code}. Valid for 10 minutes. Do not share this code."
    create_notification(user.user_id, 'OTP', message)


def notify_booking(patient_user, doctor_user, slot_date, slot_time, doctor_name):
    """
    Sends booking notifications to both patient and doctor.
    """
    # Patient notification
    patient_message = f"Appointment confirmed at Bangladesh Hospital. Dr. {doctor_name} on {slot_date.strftime('%d %b %Y')} at {slot_time.strftime('%I:%M %p')}. Please arrive 15 minutes early."
    create_notification(patient_user.user_id, 'booking', patient_message)
    
    # Doctor notification
    doctor_message = f"New appointment: Patient {patient_user.full_name} on {slot_date.strftime('%d %b %Y')} at {slot_time.strftime('%I:%M %p')}."
    create_notification(doctor_user.user_id, 'booking', doctor_message)


def notify_cancellation(patient_user, doctor_user, slot_date, slot_time):
    """
    Sends cancellation notifications to both patient and doctor.
    """
    # Patient notification
    patient_message = f"Your appointment at Bangladesh Hospital on {slot_date.strftime('%d %b %Y')} at {slot_time.strftime('%I:%M %p')} has been cancelled."
    create_notification(patient_user.user_id, 'cancellation', patient_message)
    
    # Doctor notification
    doctor_message = f"Appointment with patient {patient_user.full_name} on {slot_date.strftime('%d %b %Y')} at {slot_time.strftime('%I:%M %p')} was cancelled."
    create_notification(doctor_user.user_id, 'cancellation', doctor_message)


def notify_completion(patient_user, doctor_name):
    """
    Sends completion notification to patient only.
    """
    message = f"Your consultation with Dr. {doctor_name} at Bangladesh Hospital is complete. Thank you for visiting. Please rate your experience in the app."
    create_notification(patient_user.user_id, 'completion', message)


def notify_reminder(patient_user, doctor_name, slot_date, slot_time):
    """
    Sends reminder notification to patient.
    """
    message = f"Reminder: You have an appointment with Dr. {doctor_name} at Bangladesh Hospital tomorrow on {slot_date.strftime('%d %b %Y')} at {slot_time.strftime('%I:%M %p')}. Please bring your medical records."
    create_notification(patient_user.user_id, 'reminder', message)


def check_reminders():
    """
    Called by APScheduler every 30 minutes to check for upcoming appointments that need reminders.
    """
    now = get_current_time()
    # Calculate time window: between 23 and 25 hours from now
    window_start = now + timedelta(hours=23)
    window_end = now + timedelta(hours=25)
    
    # Fetch qualifying appointments
    appointments = Appointment.query.join(
        Appointment.time_slot
    ).filter(
        Appointment.status.in_(['booked', 'confirmed']),
        Appointment.reminder_sent.is_(False)
    ).all()
    
    for appointment in appointments:
        slot = appointment.time_slot
        # Combine date and time and localize
        slot_datetime = tz.localize(datetime.combine(slot.slot_date, slot.slot_time))
        
        # Check if slot is within the reminder window
        if window_start <= slot_datetime <= window_end:
            # Send reminder
            notify_reminder(
                appointment.patient,
                slot.doctor.user.full_name,
                slot.slot_date,
                slot.slot_time
            )
            # Mark as sent
            appointment.reminder_sent = True
            db.session.commit()
