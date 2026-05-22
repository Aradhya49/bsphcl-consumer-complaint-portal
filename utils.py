import os
import io
import random
import string
from datetime import datetime, timedelta

from flask import current_app, render_template
from flask_mail import Message
from extensions import mail, db
from models import OTP


# ─────────────────────────────────────────────
#  File Upload Helpers
# ─────────────────────────────────────────────

def allowed_file(filename):
    """Return True if the file extension is in the allowed set."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'pdf'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def make_unique_filename(filename):
    """Prefix the filename with a random 8-char string to avoid collisions."""
    ext    = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin'
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    safe   = ''.join(c if c.isalnum() or c in ('_', '-') else '_'
                     for c in filename.rsplit('.', 1)[0])[:40]
    return f'{prefix}_{safe}.{ext}'


# ─────────────────────────────────────────────
#  Consumer ID Generator
# ─────────────────────────────────────────────

def generate_consumer_id(role='user'):
    """
    Generate a unique consumer / staff / admin ID.
    Examples: CNSMR000001, STAFF000002, ADMIN10432
    """
    from models import User
    last = User.query.order_by(User.id.desc()).first()
    seq  = (last.id + 1) if last else 1

    prefix = {'user': 'CNSMR', 'staff': 'STAFF', 'admin': 'ADMIN'}.get(role, 'CNSMR')
    return f'{prefix}{seq:06d}'


# ─────────────────────────────────────────────
#  OTP Helpers
# ─────────────────────────────────────────────

def generate_otp(email):
    """
    Delete any old OTP for this email and create a fresh one.
    Returns the 6-digit OTP string.
    """
    OTP.query.filter_by(email=email).delete()
    db.session.commit()

    code = str(random.randint(100000, 999999))
    db.session.add(OTP(email=email, otp=code))
    db.session.commit()
    return code


def verify_otp(email, code):
    """
    Check whether the given OTP is valid and not expired.
    Returns True/False.  Deletes the OTP after a successful match.
    """
    record = OTP.query.filter_by(email=email, otp=code).first()
    if not record:
        return False

    expiry_seconds = current_app.config.get('OTP_EXPIRY_SECONDS', 300)
    age = (datetime.utcnow() - record.created_at).total_seconds()
    if age > expiry_seconds:
        db.session.delete(record)
        db.session.commit()
        return False

    db.session.delete(record)
    db.session.commit()
    return True


# ─────────────────────────────────────────────
#  Email Sender
# ─────────────────────────────────────────────

def send_otp_email(email, otp_code, purpose='login'):
    """Send an OTP email.  purpose = 'login' | 'reset'."""
    subject_map = {
        'login': 'BSPHCLApp – Your Login OTP',
        'reset': 'BSPHCLApp – Password Reset OTP',
    }
    subject = subject_map.get(purpose, 'BSPHCLApp – OTP')

    body = (
        f"Dear BSPHCL Portal User,\n\n"
        f"Your One-Time Password (OTP) for {'login' if purpose == 'login' else 'password reset'} is:\n\n"
        f"    {otp_code}\n\n"
        f"This OTP is valid for 5 minutes. Do not share it with anyone.\n\n"
        f"If you did not request this OTP, please ignore this email.\n\n"
        f"Regards,\n"
        f"Consumer Complaint Portal\n"
        f"Bihar State Power Holding Company Limited\n"
        f"Helpline: 1912 | www.bsphcl.co.in"
    )

    try:
        msg = Message(subject=subject, recipients=[email], body=body)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Email send failed to {email}: {e}')
        return False


# ─────────────────────────────────────────────
#  PDF Receipt Generator
# ─────────────────────────────────────────────

def generate_pdf(template_name, context):
    """
    Render an HTML template and convert it to PDF bytes using pdfkit.
    Falls back to raw HTML bytes if pdfkit / wkhtmltopdf is unavailable.

    Usage:
        pdf_bytes = generate_pdf('receipt_template.html', {'complaint': c, 'user': u})
        return send_file(io.BytesIO(pdf_bytes), download_name='receipt.pdf',
                         as_attachment=True, mimetype='application/pdf')
    """
    html = render_template(template_name, **context)

    try:
        import pdfkit
        options = {
            'page-size':     'A4',
            'margin-top':    '15mm',
            'margin-right':  '15mm',
            'margin-bottom': '15mm',
            'margin-left':   '15mm',
            'encoding':      'UTF-8',
            'no-outline':    None,
        }
        config = pdfkit.configuration(
            wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        )

        pdf_bytes = pdfkit.from_string(
            html,
            False,
            options=options,
            configuration=config
        )

        return pdf_bytes
    except Exception as e:
        current_app.logger.warning(
            f'pdfkit unavailable ({e}). Returning raw HTML as fallback.'
        )
        # Return HTML bytes so the download still works (browser will show the page)
        return html.encode('utf-8')
