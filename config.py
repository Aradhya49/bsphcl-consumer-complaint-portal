import os

class Config:
    # ── Security ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bsphcl-secret-key-change-in-production')
    ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'BSPHCL-ADMIN-SECRET')

    # ── Database ──────────────────────────────────────────────
    # Format: mysql+pymysql://username:password@host/database_name
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:root@localhost/consumer_portal'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Email / SMTP ──────────────────────────────────────────
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'aradhyapriya1102@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'mgdjswpxzvalnvga')  # Gmail App Password
    MAIL_DEFAULT_SENDER = ('BSPHCL Portal', os.environ.get('MAIL_USERNAME', 'aradhyapriya1102@gmail.com'))

    # ── File Upload ───────────────────────────────────────────
    UPLOAD_FOLDER   = os.path.join(os.getcwd(), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

    # ── OTP ───────────────────────────────────────────────────
    OTP_EXPIRY_SECONDS = 300   # 5 minutes
