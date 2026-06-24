-- DROP TABLE IF EXISTS statements in reverse dependency order
DROP TABLE IF EXISTS symptoms_map;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS consultation_notes;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS time_slots;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS users;

-- CREATE TABLE statements with InnoDB and utf8mb4 charset
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('patient', 'doctor', 'admin') DEFAULT 'patient' NOT NULL,
    carrier ENUM('Grameenphone', 'Robi', 'Banglalink', 'Teletalk', 'Airtel') NULL,
    otp_code VARCHAR(6) NULL,
    otp_expires_at DATETIME NULL,
    otp_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    lock_until DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    icon_name VARCHAR(50) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    dept_id INT NOT NULL,
    specialty VARCHAR(100) NULL,
    consultation_fee DECIMAL(10,2) NOT NULL,
    bio TEXT NULL,
    avg_rating DECIMAL(3,2) DEFAULT 0.00 NOT NULL,
    total_ratings INT DEFAULT 0 NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE time_slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT NOT NULL,
    slot_date DATE NOT NULL,
    slot_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    INDEX idx_slot_date (slot_date),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE appointments (
    appt_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    slot_id INT NOT NULL UNIQUE,
    reason_for_visit TEXT NULL,
    status ENUM('booked', 'confirmed', 'completed', 'cancelled') DEFAULT 'booked' NOT NULL,
    reminder_sent BOOLEAN DEFAULT FALSE NOT NULL,
    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_id (patient_id),
    FOREIGN KEY (patient_id) REFERENCES users(user_id),
    FOREIGN KEY (slot_id) REFERENCES time_slots(slot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE consultation_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    doctor_id INT NOT NULL,
    note_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appt_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ratings (
    rating_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_id INT NOT NULL UNIQUE,
    stars INT NOT NULL CHECK (stars >= 1 AND stars <= 5),
    review_text VARCHAR(300) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES users(user_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appt_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE notifications (
    notif_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    notif_type ENUM('OTP', 'booking', 'cancellation', 'reminder', 'completion') NOT NULL,
    message TEXT NOT NULL,
    sms_sent BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE symptoms_map (
    symptom_id INT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(50) NOT NULL,
    dept_id INT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- INSERT sample data
-- Departments
INSERT INTO departments (dept_name, description, icon_name) VALUES
('Medicine (General Physician)', 'General medical care and treatment for adults', 'general'),
('Cardiology', 'Heart and cardiovascular system treatment', 'heart'),
('Gynecology & Obstetrics', "Women's health, pregnancy, and childbirth", 'baby'),
('Pediatrics', 'Medical care for infants, children, and adolescents', 'child'),
('Orthopedics', 'Bone, joint, and muscle treatment', 'bone'),
('Dermatology', 'Skin, hair, and nail treatment', 'skin'),
('ENT', 'Ear, nose, and throat treatment', 'ear'),
('Neurology', 'Brain and nervous system treatment', 'brain'),
('Ophthalmology', 'Eye care and vision treatment', 'eye'),
('Dental', 'Dental and oral health care', 'tooth');

-- Admin user
INSERT INTO users (full_name, phone_number, password_hash, role) VALUES
('Admin User', '8801700000001', '$2b$12$pqSFnHboAfQl.2au7DrGQOwsT6nO/GPQaBsiA.VW52tWhjlZJhh8y', 'admin');

-- 5 patient accounts
INSERT INTO users (full_name, phone_number, password_hash, role, carrier) VALUES
('Muhammad Rahman', '8801712345678', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'patient', 'Grameenphone'),
('Fatima Akter', '8801812345678', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'patient', 'Robi'),
('Abdul Karim', '8801912345678', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'patient', 'Banglalink'),
('Ayesha Begum', '8801512345678', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'patient', 'Teletalk'),
('Hasan Ali', '8801612345678', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'patient', 'Airtel');

-- 10 doctor users
INSERT INTO users (full_name, phone_number, password_hash, role) VALUES
('Dr. Mohammad Hossain', '8801720000001', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Sarah Islam', '8801720000002', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Ali Reza', '8801720000003', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Nusrat Jahan', '8801720000004', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Kamal Uddin', '8801720000005', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Rina Khan', '8801720000006', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Shafiq Ahmed', '8801720000007', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Farzana Rahman', '8801720000008', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Ziaul Haque', '8801720000009', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor'),
('Dr. Sumaiya Akter', '8801720000010', '$2b$12$DABRHrRZRmh63oK33mWVZeeGj5kqNGIctC9zwxzZC/VPGfqIN2VTe', 'doctor');

-- 10 doctor profiles
INSERT INTO doctors (user_id, dept_id, specialty, consultation_fee, bio) VALUES
(2, 1, 'General Medicine', 500.00, '10 years experience in general practice'),
(3, 1, 'Internal Medicine', 600.00, 'Specialist in internal medicine and diagnostics'),
(4, 2, 'Cardiology', 1200.00, 'Heart specialist with 15 years experience'),
(5, 2, 'Interventional Cardiology', 1500.00, 'Expert in cardiac interventions'),
(6, 3, 'Gynecology', 800.00, 'Women''s health specialist'),
(7, 3, 'Obstetrics', 900.00, 'Pregnancy and childbirth care'),
(8, 4, 'Pediatrics', 700.00, 'Child health specialist'),
(9, 4, 'Pediatric Neurology', 1000.00, 'Specialist in pediatric neurological disorders'),
(10, 5, 'Orthopedics', 1100.00, 'Bone and joint specialist'),
(11, 5, 'Sports Medicine', 1000.00, 'Sports injury specialist');

-- 100 symptom keywords (10 per department)
INSERT INTO symptoms_map (keyword, dept_id) VALUES
-- Medicine (1)
('fever', 1),
('headache', 1),
('cough', 1),
('cold', 1),
('body pain', 1),
('fatigue', 1),
('nausea', 1),
('vomiting', 1),
('diarrhea', 1),
('loss of appetite', 1),
-- Cardiology (2)
('chest pain', 2),
('heart palpitations', 2),
('shortness of breath', 2),
('high blood pressure', 2),
('dizziness', 2),
('swelling', 2),
('irregular heartbeat', 2),
('fatigue', 2),
('chest tightness', 2),
('leg pain', 2),
-- Gynecology (3)
('pelvic pain', 3),
('menstrual cramps', 3),
('irregular periods', 3),
('vaginal discharge', 3),
('pregnancy', 3),
('breast pain', 3),
('menopause', 3),
('infertility', 3),
('painful intercourse', 3),
('heavy bleeding', 3),
-- Pediatrics (4)
('child fever', 4),
('child cough', 4),
('child diarrhea', 4),
('vomiting', 4),
('rash', 4),
('growth concern', 4),
('vaccination', 4),
('ear infection', 4),
('stomach ache', 4),
('allergies', 4),
-- Orthopedics (5)
('joint pain', 5),
('back pain', 5),
('arthritis', 5),
('fracture', 5),
('sports injury', 5),
('knee pain', 5),
('shoulder pain', 5),
('neck pain', 5),
('muscle strain', 5),
('bone pain', 5),
-- Dermatology (6)
('acne', 6),
('rash', 6),
('eczema', 6),
('psoriasis', 6),
('hair loss', 6),
('dandruff', 6),
('skin allergy', 6),
('itching', 6),
('skin infection', 6),
('nail problem', 6),
-- ENT (7)
('ear pain', 7),
('hearing loss', 7),
('tinnitus', 7),
('nose bleed', 7),
('sinusitis', 7),
('sore throat', 7),
('tonsillitis', 7),
('snoring', 7),
('nasal congestion', 7),
('hoarseness', 7),
-- Neurology (8)
('seizures', 8),
('migraine', 8),
('stroke', 8),
('memory loss', 8),
('numbness', 8),
('weakness', 8),
('paralysis', 8),
('tremor', 8),
('headache', 8),
('vertigo', 8),
-- Ophthalmology (9)
('blurred vision', 9),
('eye pain', 9),
('red eye', 9),
('dry eyes', 9),
('cataract', 9),
('glaucoma', 9),
('eye infection', 9),
('itchy eyes', 9),
('watery eyes', 9),
('vision loss', 9),
-- Dental (10)
('toothache', 10),
('gum pain', 10),
('cavity', 10),
('tooth sensitivity', 10),
('bleeding gums', 10),
('bad breath', 10),
('tooth decay', 10),
('wisdom tooth', 10),
('mouth ulcer', 10),
('teeth whitening', 10);

-- 5 sample time slots each for first 2 doctors (dates 3-7 days from now)
INSERT INTO time_slots (doctor_id, slot_date, slot_time) VALUES
-- Doctor 1 (Dr. Mohammad Hossain)
(1, DATE_ADD(CURRENT_DATE, INTERVAL 3 DAY), '09:00:00'),
(1, DATE_ADD(CURRENT_DATE, INTERVAL 3 DAY), '10:00:00'),
(1, DATE_ADD(CURRENT_DATE, INTERVAL 4 DAY), '09:00:00'),
(1, DATE_ADD(CURRENT_DATE, INTERVAL 5 DAY), '11:00:00'),
(1, DATE_ADD(CURRENT_DATE, INTERVAL 7 DAY), '10:00:00'),
-- Doctor 2 (Dr. Sarah Islam)
(2, DATE_ADD(CURRENT_DATE, INTERVAL 3 DAY), '14:00:00'),
(2, DATE_ADD(CURRENT_DATE, INTERVAL 4 DAY), '15:00:00'),
(2, DATE_ADD(CURRENT_DATE, INTERVAL 5 DAY), '14:00:00'),
(2, DATE_ADD(CURRENT_DATE, INTERVAL 6 DAY), '16:00:00'),
(2, DATE_ADD(CURRENT_DATE, INTERVAL 7 DAY), '15:00:00');
