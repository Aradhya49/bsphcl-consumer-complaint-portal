import os

class Config:
    SECRET_KEY   = os.environ.get('SECRET_KEY', 'change-this-in-production')
    ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'BSPHCL-ADMIN-SECRET')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER         = 'smtp.gmail.com'
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = ('BSPHCL Portal', os.environ.get('MAIL_USERNAME', ''))

    UPLOAD_FOLDER      = os.path.join(os.getcwd(), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

    OTP_EXPIRY_SECONDS = 300