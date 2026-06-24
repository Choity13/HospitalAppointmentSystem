# 🏥 Bangladesh Hospital Appointment Scheduling System

A full-stack web application built with **Flask** and **SQLAlchemy** for scheduling hospital appointments in Bangladesh. The system supports OTP-based two-factor authentication, a visual weekly calendar for slot booking, a keyword-based symptom recommender, and a comprehensive admin panel with analytics.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Bangladesh Localization](#bangladesh-localization)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Test Accounts](#test-accounts)
- [Directory Structure](#directory-structure)
- [Departments](#departments)
- [Database Schema](#database-schema)
- [API Routes Overview](#api-routes-overview)
- [Development Notes](#development-notes)

---

## ✨ Features

### Core Functional Features

| Feature | Description |
|---|---|
| 📱 OTP 2FA Authentication | Phone-based login with 6-digit OTP, 10-minute expiry, 3-attempt lockout |
| 📅 Visual Weekly Calendar | Interactive grid for browsing and booking available time slots |
| 🔍 Symptom Recommender | Keyword-based engine maps patient symptoms to the correct department |
| 👨‍⚕️ Doctor Management | Admin can add doctors, assign departments, manage availability |
| 📋 Appointment Lifecycle | Book → Confirm → Complete → Rate flow with cancellation support |
| 📝 Consultation Notes | Doctors can write structured notes per appointment |
| ⭐ Doctor Ratings | Patients rate doctors (1–5 stars) after completed consultations |
| 📊 Admin Analytics | Chart.js dashboards for appointments, departments, and revenue (৳) |
| 📲 SMS Notification Log | All simulated SMS messages stored and viewable in Admin panel |
| ⏰ Appointment Reminders | APScheduler sends reminders 24 hours before appointments |

### Security Features

- bcrypt password hashing (cost factor 12)
- Account lockout after 3 failed OTP attempts (15-minute lock)
- Session-based authentication via Flask-Login
- Role-based access control (patient / doctor / admin)

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Flask 3.1.3 |
| Database ORM | Flask-SQLAlchemy 3.1.1 |
| Database Driver | PyMySQL 1.2.0 |
| Authentication | Flask-Login 0.6.3 + bcrypt 5.0.0 |
| Task Scheduler | APScheduler 3.11.2 |
| Frontend Charts | Chart.js (CDN) |
| Timezone | pytz 2026.2 — Asia/Dhaka (UTC+6) |
| Environment | python-dotenv 1.2.2 |
| Template Engine | Jinja2 3.1.6 |

---

## 🇧🇩 Bangladesh Localization

This system is fully localized for Bangladesh:

| Element | Detail |
|---|---|
| Currency | Bangladeshi Taka ৳ (BDT) used in all billing and analytics |
| Phone Format | `8801XXXXXXXXX` — e.g. `880171XXXXXXX`, `880191XXXXXXX` |
| Phone Regex | `^8801[3-9][0-9]{8}$` (13-digit national format) |
| Timezone | `Asia/Dhaka` (UTC+6), all timestamps stored and displayed in BDT |
| Mobile Carriers | Grameenphone, Robi, Banglalink, Teletalk, Airtel |
| OTP Message | Delivered via simulated carrier SMS with carrier name |
| Calendar | Displays Bangladeshi public holidays (configurable) |

---

## ⚙️ Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Tested on 3.12 |
| MySQL | 8.0+ | Or MariaDB 10.5+ |
| pip | Latest | Comes with Python |
| Git | Any | For cloning the repository |
| Web Browser | Modern | Chrome, Firefox, Edge |

---

## 🚀 Installation

Follow these steps exactly, one at a time.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Choity13/HospitalAppointmentSystem.git
cd HospitalAppointmentSystem
```

### Step 2 — Create and Activate a Virtual Environment

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables

Copy the example file and edit it:

```bash
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
```

Then open `.env` and fill in your values (see [Configuration](#configuration) below).

### Step 5 — Initialize the Database

```bash
python init_db.py
```

This creates all tables and seeds demo data including departments, doctors, and test accounts.

### Step 6 — Run the Application

```bash
python run.py
```

Open your browser and navigate to: **http://127.0.0.1:5000**

---

## 🔧 Configuration

Edit the `.env` file in the project root:

```env
# Required: Change this to a long random string in production
SECRET_KEY=your-secret-key-here-change-in-production

# Required: Your MySQL connection string
# Format: mysql+pymysql://username:password@host:port/database_name
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/hospital_db

# Timezone (do not change)
TIMEZONE=Asia/Dhaka
```

> ⚠️ **Never commit your `.env` file to Git.** It is already listed in `.gitignore`.

---

## 🗄️ Database Setup

The system uses a 9-table relational schema:

| Table | Purpose |
|---|---|
| `users` | All users (patients, doctors, admins) with OTP and lock fields |
| `departments` | Hospital departments (Cardiology, Neurology, etc.) |
| `doctors` | Doctor profiles linked to users and departments |
| `time_slots` | Available appointment slots per doctor per day |
| `appointments` | Booked appointments linking patients to time slots |
| `consultation_notes` | Doctor notes per completed appointment |
| `ratings` | Patient ratings (1–5 stars) per appointment |
| `notifications` | All SMS notification logs (OTP, booking, reminder, etc.) |
| `symptoms_map` | Keyword-to-department mapping for the recommender engine |

To view the full schema SQL, see `database/schema.sql`.

---

## 🧪 Test Accounts

Use these accounts to test all three user roles after running `init_db.py`:

| Role | Full Name | Phone Number | Password | Notes |
|---|---|---|---|---|
| **Admin** | System Admin | `880171000000` | `Admin@1234` | Full access to dashboard, doctors, reports, SMS log |
| **Patient** | Mohammad Rahim | `880171000001` | `Patient@1234` | Can book appointments, use symptom recommender, rate doctors |
| **Doctor** | Dr. Ayesha Khan | `880171000002` | `Doctor@1234` | Can manage schedule, view appointments, write consultation notes |

> 💡 **OTP Testing Note:** The system is currently in **testing mode**. After logging in with the correct phone number and password, enter **any 6-digit number** (e.g. `123456`) on the OTP screen. The system will accept it and complete the login.
>
> To view the real generated OTP, check your terminal/console — it is printed as:
> `=== OTP for [Name] ([Phone]): XXXXXX ===`

---

## 📁 Directory Structure

```
hospital-appointment-system/
│
├── app.py                    # Flask app factory and blueprint registration
├── run.py                    # Entry point — python run.py to start server
├── config.py                 # Configuration class (reads from .env)
├── extensions.py             # db and login_manager instances
├── init_db.py                # Creates tables and seeds demo data
├── generate_hashes.py        # Utility to pre-hash test passwords
├── requirements.txt          # All pip dependencies with pinned versions
├── .env                      # Environment variables (DO NOT commit)
├── .gitignore                # Excludes venv, .env, __pycache__, etc.
│
├── controllers/              # Flask Blueprints (MVC Controllers)
│   ├── auth.py               # Register, Login, OTP verify, Logout
│   ├── patient.py            # Patient dashboard, booking, history, ratings
│   ├── doctor.py             # Doctor dashboard, schedule, slots, notes
│   └── admin.py              # Admin dashboard, doctors, departments, reports
│
├── models/                   # SQLAlchemy ORM Models
│   ├── __init__.py           # Exports all models
│   ├── user.py               # User model with OTP and lock logic
│   ├── department.py         # Department model
│   ├── doctor.py             # Doctor profile model
│   ├── time_slot.py          # Time slot model
│   ├── appointment.py        # Appointment model
│   ├── consultation_note.py  # Consultation notes model
│   ├── rating.py             # Rating model
│   ├── notification.py       # Notification/SMS log model
│   └── symptoms_map.py       # Symptom-to-department keyword model
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Base layout with navbar and flash messages
│   ├── includes/
│   │   └── sidebar_nav.html  # Shared sidebar navigation
│   ├── auth/
│   │   ├── login.html        # Login form (phone + name + password)
│   │   ├── register.html     # Registration form
│   │   └── verify_otp.html   # 6-box OTP entry with countdown timer
│   ├── patient/
│   │   ├── dashboard.html    # Patient home with upcoming appointments
│   │   ├── calendar.html     # Visual weekly slot booking calendar
│   │   ├── browse_doctors.html # Doctor listing with symptom recommender
│   │   └── appointments.html # Patient appointment history
│   ├── doctor/
│   │   ├── dashboard.html    # Doctor home with today's schedule
│   │   ├── slots.html        # Manage available time slots
│   │   ├── schedule.html     # Weekly schedule view
│   │   ├── appointment_detail.html  # Single appointment + write notes
│   │   └── patient_history.html     # Past appointments for a patient
│   └── admin/
│       ├── dashboard.html    # KPI cards + Chart.js analytics
│       ├── doctors.html      # Doctor list and management
│       ├── add_doctor.html   # Add new doctor form
│       ├── departments.html  # Department management
│       ├── reports.html      # Downloadable reports
│       └── sms_log.html      # All SMS notification history
│
├── static/                   # Static assets
│   ├── css/                  # Stylesheets
│   └── js/
│       ├── otp.js            # OTP input auto-advance, paste, countdown
│       └── calendar.js       # Visual weekly calendar grid logic
│
├── utils/                    # Utility modules
│   ├── notifications.py      # SMS simulation: OTP, booking, reminder, cancel
│   ├── recommender.py        # Keyword-based symptom-to-department engine
│   ├── date_utils.py         # Timezone-aware datetime helpers (Asia/Dhaka)
│   └── decorators.py        # Role-based access decorators (@patient_required etc.)
│
├── database/
│   └── schema.sql            # Full MySQL schema DDL
│
├── tests/                    # Test files (to be populated)
│
└── instance/
    └── hospital.db           # SQLite DB file (if using SQLite in dev)
```

---

## 🏥 Departments

The system includes 10 hospital departments:

| # | Department | Example Symptoms |
|---|---|---|
| 1 | Cardiology | chest pain, heart palpitations, shortness of breath |
| 2 | Neurology | headache, dizziness, numbness, seizures |
| 3 | Orthopedics | joint pain, back pain, fracture, bone ache |
| 4 | Pediatrics | child fever, infant rash, growth concerns |
| 5 | Gynecology | menstrual pain, pregnancy, women's health |
| 6 | Dermatology | skin rash, acne, eczema, hair loss |
| 7 | Ophthalmology | eye pain, blurred vision, eye infection |
| 8 | ENT | ear pain, throat infection, sinus, hearing loss |
| 9 | Gastroenterology | stomach pain, nausea, diarrhea, acidity |
| 10 | Psychiatry | anxiety, depression, stress, sleep disorder |

---

## 🔌 API Routes Overview

| Blueprint | Prefix | Key Routes |
|---|---|---|
| `auth` | `/auth` | `GET/POST /login`, `GET/POST /register`, `GET/POST /verify-otp`, `POST /resend-otp`, `GET /logout` |
| `patient` | `/patient` | `GET /dashboard`, `GET /calendar/<doctor_id>`, `POST /book`, `GET /appointments`, `POST /cancel/<id>`, `POST /rate/<id>` |
| `doctor` | `/doctor` | `GET /dashboard`, `GET/POST /slots`, `GET /schedule`, `GET /appointment/<id>`, `POST /complete/<id>`, `POST /notes/<id>` |
| `admin` | `/admin` | `GET /dashboard`, `GET /doctors`, `GET/POST /add-doctor`, `GET /departments`, `GET /reports`, `GET /sms-log` |

---

## 🔬 Development Notes

### OTP Verification Modes

The `verify_otp()` method in `models/user.py` has two modes:

**Testing Mode (current):** Accepts any 6-digit number.
```python
def verify_otp(self, code):
    if code and len(code) == 6 and code.isdigit():
        self.otp_verified = True
        return True
    return False
```

**Production Mode:** Enforces strict OTP code matching with expiry check.
```python
def verify_otp(self, code):
    now = get_current_time()
    if (self.otp_code and
            code == self.otp_code and
            self.otp_expires_at_aware > now):
        self.otp_verified = True
        return True
    return False
```

To see the real OTP during testing, check your terminal output for:
```
=== OTP for [Full Name] ([Phone Number]): 123456 ===
```

### APScheduler

The reminder scheduler runs every 30 minutes and sends reminders to patients whose appointments are 23–25 hours away. It starts automatically when the Flask app is created.

### SMS Simulation

No real SMS provider is used. All notifications are stored in the `notifications` table with `sms_sent=True` and printed to the console. Admins can view the full SMS log at `/admin/sms-log`.

---

## 📄 License

This project is an academic submission for university coursework. All rights reserved.

---

*Built for Bangladesh 🇧🇩 — Developed by Choity13*
