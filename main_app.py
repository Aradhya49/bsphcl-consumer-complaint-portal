import os
import io
from collections import Counter
from datetime import datetime, timedelta

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, send_file, g, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User, Complaint, Reply, OTP, Notification
from utils import (allowed_file, make_unique_filename, generate_consumer_id,
                   generate_otp, verify_otp as check_otp,
                   send_otp_email, generate_pdf)
from notif_helpers import (notify_admins_new_complaint, notify_admins_user_reply,
                            notify_admins_new_user, get_unread_count)
from config import Config

main_bp = Blueprint('main_bp', __name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')


# ── Before request ───────────────────────────────────────────
@main_bp.before_app_request
def load_logged_in_user():
    user_id        = session.get('user_id')
    g.user         = User.query.get(user_id) if user_id else None
    g.unread_count = get_unread_count(user_id) if user_id else 0


# ── Home ─────────────────────────────────────────────────────
@main_bp.route('/')
def home():
    if session.get('user_id'):
        return redirect(url_for('main_bp.dashboard'))
    return redirect(url_for('main_bp.login'))


# ── Register ─────────────────────────────────────────────────
BIHAR_DISTRICTS = {
    "Araria","Arwal","Aurangabad","Banka","Begusarai","Bhagalpur",
    "Bhojpur","Buxar","Darbhanga","East Champaran","Gaya","Gopalganj",
    "Jamui","Jehanabad","Kaimur","Katihar","Khagaria","Kishanganj",
    "Lakhisarai","Madhepura","Madhubani","Munger","Muzaffarpur","Nalanda",
    "Nawada","Patna","Purnia","Rohtas","Saharsa","Samastipur","Saran",
    "Sheikhpura","Sheohar","Sitamarhi","Siwan","Supaul","Vaishali",
    "West Champaran"
}

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('main_bp.dashboard'))

    if request.method == 'POST':
        name     = request.form.get('name',     '').strip()
        email    = request.form.get('email',    '').strip().lower()
        mobile   = request.form.get('mobile',   '').strip()
        password = request.form.get('password', '').strip()
        confirm  = request.form.get('confirm_password', '').strip()
        district = request.form.get('district', '').strip()
        address  = request.form.get('address',  '').strip()

        if not all([name, email, mobile, password, district]):
            flash('All required fields must be filled in.', 'warning')
            return render_template('register.html')
        if district not in BIHAR_DISTRICTS:
            flash('Invalid district. Please select a valid Bihar district from the dropdown.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Password and Confirm Password do not match. Please try again.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if len(mobile) != 10 or not mobile.isdigit():
            flash('Enter a valid 10-digit mobile number.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('This email is already registered.', 'warning')
            return render_template('register.html')
        if User.query.filter_by(mobile=mobile).first():
            flash('This mobile number is already registered.', 'warning')
            return render_template('register.html')

        new_user = User(
            name        = name,
            email       = email,
            mobile      = mobile,
            password    = generate_password_hash(password),
            consumer_id = generate_consumer_id('user'),
            role        = 'user',
            district    = district,
            address     = address or None
        )
        try:
            db.session.add(new_user)
            db.session.flush()
            notify_admins_new_user(new_user)
            db.session.commit()
            flash(f'Registration successful! Your Consumer ID is {new_user.consumer_id}.', 'success')
            return redirect(url_for('main_bp.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. Email or mobile may already be registered.', 'danger')

    return render_template('register.html')


# ── Login ────────────────────────────────────────────────────
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('main_bp.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email',    '').strip().lower()
        password = request.form.get('password', '').strip()
        user     = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['name']    = user.name
            session['role']    = user.role
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('main_bp.dashboard'))
        flash('Invalid email or password.', 'danger')

    return render_template('login.html')


# ── Logout ───────────────────────────────────────────────────
@main_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main_bp.login'))


# ── Forgot Password ──────────────────────────────────────────
@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()
        if user:
            code = generate_otp(email)
            sent = send_otp_email(email, code, purpose='reset')
            session['reset_email'] = email
            if sent:
                flash(f'OTP sent to {email}.', 'info')
            else:
                flash(f'Email sending failed. DEV OTP: {code}', 'warning')
            return redirect(url_for('main_bp.verify_otp'))
        flash('No account found with that email.', 'danger')
    return render_template('forgot_password.html')


# ── Verify OTP ───────────────────────────────────────────────
@main_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('reset_email')
    if not email:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('main_bp.forgot_password'))
    if request.method == 'POST':
        code = request.form.get('otp', '').strip()
        if check_otp(email, code):
            session['otp_verified'] = True
            flash('OTP verified. Set your new password.', 'success')
            return redirect(url_for('main_bp.reset_password'))
        flash('Invalid or expired OTP.', 'danger')
    return render_template('verify_otp.html')


# ── Reset Password ───────────────────────────────────────────
@main_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('otp_verified') or not session.get('reset_email'):
        flash('Please start the reset process again.', 'danger')
        return redirect(url_for('main_bp.forgot_password'))
    if request.method == 'POST':
        new_pw  = request.form.get('new_password',     '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if new_pw != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html')
        if len(new_pw) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('reset_password.html')
        email = session.pop('reset_email')
        session.pop('otp_verified', None)
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_pw)
            db.session.commit()
            flash('Password updated. Please login.', 'success')
            return redirect(url_for('main_bp.login'))
        flash('User not found.', 'danger')
        return redirect(url_for('main_bp.login'))
    return render_template('reset_password.html')


# ── Dashboard ────────────────────────────────────────────────
@main_bp.route('/dashboard')
def dashboard():
    if not g.user:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('main_bp.login'))

    uid          = g.user.id
    total        = Complaint.query.filter_by(user_id=uid).count()
    resolved     = Complaint.query.filter_by(user_id=uid, status='Resolved').count()
    pending      = Complaint.query.filter_by(user_id=uid, status='Pending').count()
    under_review = Complaint.query.filter_by(user_id=uid, status='Under Review').count()
    last_7_days  = Complaint.query.filter(
        Complaint.user_id    == uid,
        Complaint.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    with_attachments = Complaint.query.filter(
        Complaint.user_id    == uid,
        Complaint.attachment != None,
        Complaint.attachment != ''
    ).count()
    types = Complaint.query.with_entities(Complaint.complaint_type).filter_by(user_id=uid).all()
    complaint_types   = Counter(t[0] for t in types if t[0])
    recent_complaints = Complaint.query.filter_by(user_id=uid)\
                                       .order_by(Complaint.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total=total, resolved=resolved, pending=pending, under_review=under_review,
        last_7_days=last_7_days, with_attachments=with_attachments,
        complaint_types=complaint_types, recent_complaints=recent_complaints
    )


# ── Help Desk Page ────────────────────────────────
@main_bp.route('/helpdesk')
def helpdesk():
    if not g.user:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('main_bp.login'))
    return render_template('helpdesk.html')



# ── Notifications ────────────────────────────────────────────
@main_bp.route('/notifications')
def notifications():
    if not g.user:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('main_bp.login'))
    notifs = Notification.query.filter_by(user_id=g.user.id)\
                                .order_by(Notification.created_at.desc()).all()
    Notification.query.filter_by(user_id=g.user.id, is_read=False)\
                      .update({'is_read': True})
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)


# ── Mark Read ────────────────────────────────────────────────
@main_bp.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
def mark_read(notif_id):
    if not g.user:
        return jsonify({'ok': False})
    n = Notification.query.get(notif_id)
    if n and n.user_id == g.user.id:
        n.is_read = True
        db.session.commit()
    return jsonify({'ok': True})


# ── Unread Count API ─────────────────────────────────────────
@main_bp.route('/api/unread-count')
def api_unread_count():
    if not g.user:
        return jsonify({'count': 0})
    count = Notification.query.filter_by(user_id=g.user.id, is_read=False).count()
    return jsonify({'count': count})


# ── Complaint Tracking API ───────────────────────────────────
@main_bp.route('/api/track')
def api_track():
    if not g.user:
        return jsonify({'found': False})
    cid_raw  = request.args.get('cid', '').strip()
    consumer = request.args.get('consumer', '').strip().upper()
    try:
        cid = int(cid_raw)
    except ValueError:
        return jsonify({'found': False})
    c = Complaint.query.get(cid)
    if not c:
        return jsonify({'found': False})
    owner = User.query.get(c.user_id)
    if not owner or owner.consumer_id.upper() != consumer:
        return jsonify({'found': False})
    return jsonify({
        'found': True, 'id': c.id,
        'type': c.complaint_type, 'subcategory': c.subcategory,
        'status': c.status,
        'date': c.created_at.strftime('%d %b %Y, %I:%M %p') if c.created_at else '—'
    })


# ── File a Complaint ─────────────────────────────────────────
@main_bp.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if not g.user:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('main_bp.login'))

    if request.method == 'POST':
        complaint_type = request.form.get('complaint_type', '').strip() or 'Others'
        subcategory    = request.form.get('subcategory',    '').strip()
        description    = request.form.get('description',   '').strip()

        if not description or len(description) < 20:
            flash('Please provide a detailed description (minimum 20 characters).', 'warning')
            return render_template('complaint_form.html')

        filename = None
        file = request.files.get('attachment')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Invalid file type. Only JPG, PNG, and PDF allowed.', 'danger')
                return render_template('complaint_form.html')
            filename = make_unique_filename(secure_filename(file.filename))
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        new_complaint = Complaint(
            user_id=g.user.id, complaint_type=complaint_type,
            subcategory=subcategory, description=description,
            attachment=filename, status='Pending', created_at=datetime.utcnow()
        )
        db.session.add(new_complaint)
        db.session.flush()
        notify_admins_new_complaint(new_complaint, g.user)
        db.session.commit()
        flash(f'Complaint submitted! ID: CMP{new_complaint.id:04d}.', 'success')
        return redirect(url_for('main_bp.complaint_history'))

    return render_template('complaint_form.html')


# ── Complaint History ────────────────────────────────────────
@main_bp.route('/complaint-history')
def complaint_history():
    if not g.user:
        flash('Please login.', 'warning')
        return redirect(url_for('main_bp.login'))
    complaints = Complaint.query.filter_by(user_id=g.user.id)\
                                .order_by(Complaint.created_at.desc()).all()
    return render_template('complaint_history.html', complaints=complaints)


# ── Complaint Detail ─────────────────────────────────────────
@main_bp.route('/complaint/<int:complaint_id>')
def complaint_detail(complaint_id):
    if not g.user:
        flash('Please login.', 'warning')
        return redirect(url_for('main_bp.login'))
    c = Complaint.query.get_or_404(complaint_id)
    if c.user_id != g.user.id:
        flash('Unauthorised access.', 'danger')
        return redirect(url_for('main_bp.complaint_history'))
    return render_template('complaint_detail.html', complaint=c)


# ── Download Receipt ─────────────────────────────────────────
@main_bp.route('/complaint/<int:complaint_id>/receipt')
def download_receipt(complaint_id):
    if not g.user:
        return redirect(url_for('main_bp.login'))
    c = Complaint.query.get_or_404(complaint_id)
    if c.user_id != g.user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('main_bp.dashboard'))
    pdf_bytes = generate_pdf('receipt_template.html', {'complaint': c, 'user': g.user})
    return send_file(io.BytesIO(pdf_bytes),
                     download_name=f'BSPHCL_Complaint_{complaint_id:04d}.pdf',
                     as_attachment=True, mimetype='application/pdf')


# ── Close Complaint ──────────────────────────────────────────
@main_bp.route('/complaint/<int:complaint_id>/close', methods=['POST'])
def close_complaint(complaint_id):
    if not g.user:
        return redirect(url_for('main_bp.login'))
    c = Complaint.query.get_or_404(complaint_id)
    if c.user_id == g.user.id:
        c.status = 'Resolved'
        db.session.commit()
        flash('Complaint marked as Resolved.', 'success')
    return redirect(url_for('main_bp.complaint_detail', complaint_id=complaint_id))


# ── Reopen Complaint ─────────────────────────────────────────
@main_bp.route('/complaint/<int:complaint_id>/reopen', methods=['POST'])
def reopen_complaint(complaint_id):
    if not g.user:
        return redirect(url_for('main_bp.login'))
    c = Complaint.query.get_or_404(complaint_id)
    if c.user_id == g.user.id:
        c.status = 'Pending'
        db.session.commit()
        flash('Complaint reopened.', 'warning')
    return redirect(url_for('main_bp.complaint_detail', complaint_id=complaint_id))


# ── Add Reply ────────────────────────────────────────────────
@main_bp.route('/complaint/<int:complaint_id>/reply', methods=['POST'])
def add_complaint_info(complaint_id):
    if not g.user:
        return redirect(url_for('main_bp.login'))
    c = Complaint.query.get_or_404(complaint_id)
    if c.user_id != g.user.id:
        flash('Unauthorised reply.', 'danger')
        return redirect(url_for('main_bp.complaint_history'))
    message = request.form.get('message', '').strip()
    if message:
        reply = Reply(complaint_id=complaint_id, user_id=g.user.id,
                      message=message, role='user', timestamp=datetime.utcnow())
        db.session.add(reply)
        db.session.flush()
        notify_admins_user_reply(c, g.user)
        db.session.commit()
        flash('Your reply has been added.', 'success')
    else:
        flash('Reply cannot be empty.', 'warning')
    return redirect(url_for('main_bp.complaint_detail', complaint_id=complaint_id))


# ── Profile ──────────────────────────────────────────────────
@main_bp.route('/profile')
def profile():
    if not g.user:
        flash('Please login.', 'warning')
        return redirect(url_for('main_bp.login'))
    return render_template('profile.html', user=g.user)


@main_bp.route('/edit-profile', methods=['POST'])
def edit_profile():
    if not g.user:
        return redirect(url_for('main_bp.login'))
    new_name     = request.form.get('name',     '').strip()
    new_email    = request.form.get('email',    '').strip().lower()
    new_mobile   = request.form.get('mobile',   '').strip()
    new_district = request.form.get('district', '').strip()
    new_address  = request.form.get('address',  '').strip()

    if User.query.filter(User.email == new_email, User.id != g.user.id).first():
        flash('That email is already in use.', 'danger')
        return redirect(url_for('main_bp.profile'))
    if User.query.filter(User.mobile == new_mobile, User.id != g.user.id).first():
        flash('That mobile is already in use.', 'danger')
        return redirect(url_for('main_bp.profile'))

    g.user.name     = new_name
    g.user.email    = new_email
    g.user.mobile   = new_mobile
    g.user.district = new_district or None
    g.user.address  = new_address  or None

    try:
        db.session.commit()
        session['name'] = g.user.name
        flash('Profile updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not update profile.', 'danger')
    return redirect(url_for('main_bp.profile'))


# ── Change Password (with confirm) ───────────────────────────
@main_bp.route('/change-password', methods=['POST'])
def change_password():
    if not g.user:
        return redirect(url_for('main_bp.login'))

    old_pw  = request.form.get('old_password',        '').strip()
    new_pw  = request.form.get('new_password',         '').strip()
    confirm = request.form.get('confirm_new_password', '').strip()

    if not check_password_hash(g.user.password, old_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('main_bp.profile'))

    if len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('main_bp.profile'))

    if new_pw != confirm:
        flash('New passwords do not match. Please try again.', 'danger')
        return redirect(url_for('main_bp.profile'))

    g.user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return redirect(url_for('main_bp.profile'))

# ── Upload Profile Picture (User) ───────────────────────────
# Add this import at the top of main_app.py if not already there:
# import os
# from werkzeug.utils import secure_filename

PROFILE_PIC_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
ALLOWED_PIC_EXT    = {'png', 'jpg', 'jpeg'}

def allowed_pic(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PIC_EXT


@main_bp.route('/upload-profile-pic', methods=['POST'])
def upload_profile_pic():
    if not g.user:
        return redirect(url_for('main_bp.login'))

    file = request.files.get('profile_pic')
    if not file or not file.filename:
        flash('No file selected.', 'warning')
        return redirect(url_for('main_bp.profile'))

    if not allowed_pic(file.filename):
        flash('Only JPG and PNG images are allowed.', 'danger')
        return redirect(url_for('main_bp.profile'))

    # Check file size (2 MB max)
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        flash('File size must be under 2 MB.', 'danger')
        return redirect(url_for('main_bp.profile'))

    os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)

    # Delete old picture if exists
    if g.user.profile_pic:
        old_path = os.path.join(PROFILE_PIC_FOLDER, g.user.profile_pic)
        if os.path.exists(old_path):
            os.remove(old_path)

    # Save new picture with unique name
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f'user_{g.user.id}_{int(datetime.utcnow().timestamp())}.{ext}'
    file.save(os.path.join(PROFILE_PIC_FOLDER, filename))

    g.user.profile_pic = filename
    db.session.commit()
    flash('Profile picture updated successfully.', 'success')
    return redirect(url_for('main_bp.profile'))


@main_bp.route('/remove-profile-pic', methods=['POST'])
def remove_profile_pic():
    if not g.user:
        return redirect(url_for('main_bp.login'))

    if g.user.profile_pic:
        old_path = os.path.join(PROFILE_PIC_FOLDER, g.user.profile_pic)
        if os.path.exists(old_path):
            os.remove(old_path)
        g.user.profile_pic = None
        db.session.commit()
        flash('Profile picture removed.', 'info')
    else:
        flash('No profile picture to remove.', 'warning')

    return redirect(url_for('main_bp.profile'))
