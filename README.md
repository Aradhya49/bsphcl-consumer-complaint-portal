
# ⚡ BSPHCL Consumer Complaint Analysis Portal

> A web-based complaint management system developed for **Bihar State Power Holding Company Limited (BSPHCL)** as part of a B.Tech CSE internship project.

---

# 🌐 Live Demo

🚀 Click here to open the live website:

## 👉 [BSPHCL Portal Live Demo](https://bsphcl-portal.onrender.com)

> **Note:** This project is hosted on Render free plan.  
> The server may take 50–60 seconds to wake up on first visit if inactive.  
> Please wait and refresh if the site takes time to load.

---

# 📋 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Running the Project](#running-the-project)
- [Default Credentials](#default-credentials)
- [Database Models](#database-models)
- [Key URLs](#key-urls)
- [Authors](#authors)

---

# About the Project

Traditional electricity complaint systems at BSPHCL relied on phone calls, handwritten registers, and office visits — making them slow, inefficient, and difficult to track.

This portal digitizes the entire complaint lifecycle:

- Consumers can register, file complaints, attach documents, and track status online
- BSPHCL officials can manage, reply to, and resolve complaints from a central dashboard
- Notifications keep both parties informed at every step

---

# Features

## Consumer (User) Portal

- Register with district selection (Bihar districts only)
- Secure login with password show/hide
- File complaints with category, subcategory, and file attachments
- Track complaint status in real time
- View conversation thread with admin replies
- Download complaint receipt as PDF
- Profile management with profile picture upload
- In-app notifications (admin reply, status change)
- Help Desk with complaint tracker, FAQs, safety guidance

---

## Admin Portal

- Secure admin login (restricted access)
- Dashboard with complaint statistics and charts
- View, reply to, and update status of all complaints
- Manage consumer accounts (view complaints, delete)
- Staff management (add/remove staff members)
- In-app notifications (new complaint, new user, consumer reply)
- Admin profile management with profile picture

---

## Security

- Passwords hashed using Werkzeug (scrypt)
- Role-based access control (user / staff / admin)
- Session management with Flask
- File upload validation (type + size)
- Admin accounts protected from deletion/modification by other admins

---

# Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, Flask 3.0 |
| Database | PostgreSQL (Supabase), SQLAlchemy ORM |
| Frontend | HTML5, CSS3 |
| Charts | Chart.js |
| Email | Flask-Mail |
| PDF | pdfkit + wkhtmltopdf |
| Deployment | Render |
| ORM | SQLAlchemy |

---

# Project Structure

```bash
bsphcl_backend/
│
├── app.py
├── config.py
├── extensions.py
├── models.py
├── main_app.py
├── admin_routes.py
├── notif_helpers.py
├── utils.py
├── requirements.txt
│
├── static/
├── templates/
└── venv/
```

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone https://github.com/Aradhya49/bsphcl-consumer-complaint-portal.git
cd bsphcl-consumer-complaint-portal
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate:

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## 3. Install Requirements

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Update your database and mail credentials.

---

## 5. Run the Project

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---


# Database Models

| Table | Description |
|------|-------------|
| users | Consumer, staff, admin accounts |
| complaints | Consumer complaints |
| replies | Complaint conversation |
| notifications | Notification system |

---

# Key URLs

## User Portal

| URL | Description |
|-----|-------------|
| `/register` | Consumer registration |
| `/login` | User login |
| `/dashboard` | User dashboard |
| `/complaint-history` | Complaint history |
| `/profile` | User profile |

---

## Admin Portal

| URL | Description |
|-----|-------------|
| `/admin/login` | Admin login |
| `/admin/dashboard` | Admin dashboard |
| `/admin/complaints` | Complaint management |

---

# Authors

### Aradhya Priya

