# ⚡ BSPHCL Consumer Complaint Analysis Portal

> A web-based complaint management system developed for **Bihar State Power Holding Company Limited (BSPHCL)** as part of a B.Tech CSE internship project.

---

## 🌐 Live Demo

The project is live and accessible at:

[Live Demo](https://bsphcl-portal.onrender.com)

> **Note:** This is hosted on Render free plan. The server may take 50–60 seconds to wake up on first visit if inactive. Please wait and refresh.


## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Running the Project](#running-the-project)
- [Default Credentials](#default-credentials)
- [Authors](#authors)

---

## About the Project

Traditional electricity complaint systems at BSPHCL relied on phone calls, handwritten registers, and office visits — making them slow, inefficient, and difficult to track. This portal digitizes the entire complaint lifecycle:

- Consumers can register, file complaints, attach documents, and track status online
- BSPHCL officials can manage, reply to, and resolve complaints from a central dashboard
- Notifications keep both parties informed at every step

---

## Features

### Consumer (User) Portal
- Register with district selection (Bihar districts only)
- Secure login with password show/hide
- File complaints with category, subcategory, and file attachments
- Track complaint status in real time
- View conversation thread with admin replies
- Download complaint receipt as PDF
- Profile management with profile picture upload
- In-app notifications (admin reply, status change)
- Help Desk with complaint tracker, FAQs, safety guidance

### Admin Portal
- Secure admin login (restricted access)
- Dashboard with complaint statistics and charts
- View, reply to, and update status of all complaints
- Manage consumer accounts (view complaints, delete)
- Staff management (add/remove staff members)
- In-app notifications (new complaint, new user, consumer reply)
- Admin profile management with profile picture

### Security
- Passwords hashed using Werkzeug (scrypt)
- Role-based access control (user / staff / admin)
- Session management with Flask
- File upload validation (type + size)
- Admin accounts protected from deletion/modification by other admins

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.0 |
| Database | MySQL 8.0, SQLAlchemy ORM |
| Frontend | HTML5, CSS3 (custom government theme) |
| Charts | Chart.js 3.9 |
| Email | Flask-Mail, Gmail SMTP |
| PDF | pdfkit + wkhtmltopdf |
| Migrations | Flask-Migrate |

---

## Project Structure

```
bsphcl_backend/
│
├── app.py                  ← Flask application factory
├── config.py               ← Configuration (DB, mail, keys)
├── extensions.py           ← Shared extensions (db, mail, migrate)
├── models.py               ← Database models
├── main_app.py             ← User-facing routes
├── admin_routes.py         ← Admin routes
├── notif_helpers.py        ← Notification helper functions
├── utils.py                ← PDF, OTP, file upload helpers
├── init_db.py              ← Database initialisation script
├── requirements.txt        ← Python dependencies
│
├── static/
│   ├── css/style.css       ← Government-style stylesheet
│   ├── js/main.js          ← Frontend interactions
│   └── uploads/
│       └── profiles/       ← Profile pictures
│
└── templates/
    ├── base.html           ← User base layout
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── complaint_form.html
    ├── complaint_history.html
    ├── complaint_detail.html
    ├── helpdesk.html
    ├── notifications.html
    ├── profile.html
    ├── receipt_template.html
    ├── forgot_password.html
    ├── verify_otp.html
    ├── reset_password.html
    └── admin/
        ├── base_admin.html
        ├── login_admin.html
        ├── dashboard_admin.html
        ├── all_complaints.html
        ├── complaint_detail_admin.html
        ├── manage_users.html
        ├── user_complaints.html
        ├── notifications_admin.html
        └── profile_admin.html
```

---

## Setup Instructions

### Prerequisites
- Python 3.10 or 3.11
- MySQL Server 8.0
- wkhtmltopdf (for PDF generation) — [Download here](https://wkhtmltopdf.org/downloads.html)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/bsphcl-complaint-portal.git
cd bsphcl-complaint-portal
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create MySQL Database

Open MySQL Workbench and run:

```sql
CREATE DATABASE consumer_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Configure the Application

Open `config.py` and update:

```python
# Database
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:YOUR_PASSWORD@localhost/consumer_portal'

# Gmail SMTP (use App Password, not regular password)
MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_gmail_app_password'

# Secret keys
SECRET_KEY    = 'your-secret-key'
ADMIN_SECRET  = 'BSPHCL-ADMIN-SECRET'
```

### 6. Initialise Database

```bash
python init_db.py
```

### 7. Run the Application

```bash
python app.py
```

Open browser: **http://127.0.0.1:5002**

---

## Running the Project

Every time you want to run the project:

```bash
cd bsphcl_backend
venv\Scripts\activate
python app.py
```

To stop the server: **Ctrl + C**

---

## Default Credentials

### Admin Login
```
URL      : http://127.0.0.1:5002/admin/login
Email    : Bsphcl_admin@bsphcl.co.in
Password : Admin@2025
```

### Consumer Login
Register first at: `http://127.0.0.1:5002/register`

---

## Database Models

| Table | Description |
|-------|-------------|
| `users` | Consumers, staff, and admin accounts |
| `complaints` | All complaints filed by consumers |
| `replies` | Conversation thread (admin ↔ consumer) |
| `notifications` | In-app notifications for all users |

---

## Key URLs

### User Portal
| URL | Description |
|-----|-------------|
| `/` | Home (redirects to login) |
| `/register` | Consumer registration |
| `/login` | Consumer login |
| `/dashboard` | Consumer dashboard |
| `/complaint` | File a new complaint |
| `/complaint-history` | View all complaints |
| `/helpdesk` | Help desk, FAQs, complaint tracker |
| `/notifications` | In-app notifications |
| `/profile` | User profile |

### Admin Portal
| URL | Description |
|-----|-------------|
| `/admin/login` | Admin login |
| `/admin/dashboard` | Admin dashboard |
| `/admin/complaints` | All complaints |
| `/admin/users` | Manage users and staff |
| `/admin/notifications` | Admin notifications |
| `/admin/profile` | Admin profile |

---

## Authors

Aradhya Priya