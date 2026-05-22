import os
import random
from datetime import datetime
from collections import Counter

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, g, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User, Complaint, Reply, Notification
from utils import generate_consumer_id
from notif_helpers import (notify_user_admin_reply, notify_user_status_change,
                            get_unread_count)
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

PROFILE_PIC_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
ALLOWED_PIC_EXT    = {'png', 'jpg', 'jpeg'}


# ── Before request ───────────────────────────────────────────
@admin_bp.before_app_request
def load_logged_in_admin():
    admin_id       = session.get('admin_id')
    g.admin        = User.query.get(admin_id) if admin_id else None
    g.admin_unread = get_unread_count(admin_id) if admin_id else 0


def _require_admin():
    if not g.admin or g.admin.role != 'admin':
        flash('Administrator login required.', 'warning')
        return redirect(url_for('admin.admin_login'))
    return None


# ── Admin Login ──────────────────────────────────────────────
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_id'):
        return redirect(url_for('admin.admin_dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email',    '').strip().lower()
        password = request.form.get('password', '').strip()
        admin    = User.query.filter_by(email=email, role='admin').first()
        if admin and check_password_hash(admin.password, password):
            session.clear()
            session['admin_id']   = admin.id
            session['admin_name'] = admin.name
            flash(f'Welcome, {admin.name}!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin/login_admin.html')


# ── Admin Register ───────────────────────────────────────────
@admin_bp.route('/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name        = request.form.get('name',        '').strip()
        email       = request.form.get('email',       '').strip().lower()
        mobile      = request.form.get('mobile',      '').strip()
        password    = request.form.get('password',    '').strip()
        secret_code = request.form.get('secret_code', '').strip()

        if secret_code != Config.ADMIN_SECRET:
            flash('Invalid Admin Secret Code.', 'danger')
            return render_template('admin/register_admin.html')
        if not all([name, email, mobile, password]):
            flash('All fields are required.', 'warning')
            return render_template('admin/register_admin.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return render_template('admin/register_admin.html')
        if User.query.filter_by(mobile=mobile).first():
            flash('Mobile already registered.', 'warning')
            return render_template('admin/register_admin.html')

        new_admin = User(
            name        = name,
            email       = email,
            mobile      = mobile,
            password    = generate_password_hash(password),
            consumer_id = generate_consumer_id('admin'),
            role        = 'admin'
        )
        try:
            db.session.add(new_admin)
            db.session.commit()
            flash('Admin registered successfully.', 'success')
            return redirect(url_for('admin.admin_login'))
        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. Email or mobile already exists.', 'danger')

    return render_template('admin/register_admin.html')


# ── Admin Logout ─────────────────────────────────────────────
@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin_id',   None)
    session.pop('admin_name', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin.admin_login'))


# ── Admin Profile ─────────────────────────────────────────────
@admin_bp.route('/profile')
def admin_profile():
    redir = _require_admin()
    if redir: return redir
    return render_template('admin/profile_admin.html')


# ── Admin Edit Profile ───────────────────────────────────────
@admin_bp.route('/edit-profile', methods=['POST'])
def admin_edit_profile():
    redir = _require_admin()
    if redir: return redir

    new_name   = request.form.get('name',   '').strip()
    new_email  = request.form.get('email',  '').strip().lower()
    new_mobile = request.form.get('mobile', '').strip()

    if User.query.filter(User.email == new_email, User.id != g.admin.id).first():
        flash('That email is already in use.', 'danger')
        return redirect(url_for('admin.admin_profile'))
    if User.query.filter(User.mobile == new_mobile, User.id != g.admin.id).first():
        flash('That mobile is already in use.', 'danger')
        return redirect(url_for('admin.admin_profile'))

    g.admin.name   = new_name
    g.admin.email  = new_email
    g.admin.mobile = new_mobile

    try:
        db.session.commit()
        session['admin_name'] = g.admin.name
        flash('Profile updated successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not update profile.', 'danger')

    return redirect(url_for('admin.admin_profile'))


# ── Admin Change Password ────────────────────────────────────
@admin_bp.route('/change-password', methods=['POST'])
def admin_change_password():
    redir = _require_admin()
    if redir: return redir

    old_pw  = request.form.get('old_password',        '').strip()
    new_pw  = request.form.get('new_password',         '').strip()
    confirm = request.form.get('confirm_new_password', '').strip()

    if not check_password_hash(g.admin.password, old_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('admin.admin_profile'))
    if len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('admin.admin_profile'))
    if new_pw != confirm:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('admin.admin_profile'))

    g.admin.password = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return redirect(url_for('admin.admin_profile'))


# ── Upload Profile Picture ───────────────────────────────────
@admin_bp.route('/upload-pic', methods=['POST'])
def admin_upload_pic():
    redir = _require_admin()
    if redir: return redir

    file = request.files.get('profile_pic')
    if not file or not file.filename:
        flash('No file selected.', 'warning')
        return redirect(url_for('admin.admin_profile'))

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_PIC_EXT:
        flash('Only JPG and PNG images are allowed.', 'danger')
        return redirect(url_for('admin.admin_profile'))

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        flash('File size must be under 2 MB.', 'danger')
        return redirect(url_for('admin.admin_profile'))

    os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)

    if g.admin.profile_pic:
        old = os.path.join(PROFILE_PIC_FOLDER, g.admin.profile_pic)
        if os.path.exists(old):
            os.remove(old)

    filename = f'admin_{g.admin.id}_{int(datetime.utcnow().timestamp())}.{ext}'
    file.save(os.path.join(PROFILE_PIC_FOLDER, filename))
    g.admin.profile_pic = filename
    db.session.commit()
    flash('Profile picture updated.', 'success')
    return redirect(url_for('admin.admin_profile'))


# ── Remove Profile Picture ───────────────────────────────────
@admin_bp.route('/remove-pic', methods=['POST'])
def admin_remove_pic():
    redir = _require_admin()
    if redir: return redir

    if g.admin.profile_pic:
        old = os.path.join(PROFILE_PIC_FOLDER, g.admin.profile_pic)
        if os.path.exists(old):
            os.remove(old)
        g.admin.profile_pic = None
        db.session.commit()
        flash('Profile picture removed.', 'info')
    else:
        flash('No profile picture to remove.', 'warning')
    return redirect(url_for('admin.admin_profile'))


# ── Admin Dashboard ──────────────────────────────────────────
@admin_bp.route('/dashboard')
def admin_dashboard():
    redir = _require_admin()
    if redir: return redir

    total        = Complaint.query.count()
    pending      = Complaint.query.filter_by(status='Pending').count()
    resolved     = Complaint.query.filter_by(status='Resolved').count()
    under_review = Complaint.query.filter_by(status='Under Review').count()
    recent       = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
    rows         = Complaint.query.with_entities(Complaint.complaint_type).all()
    type_counts  = Counter(r[0] for r in rows if r[0])

    return render_template(
        'admin/dashboard_admin.html',
        admin=g.admin, total=total, pending=pending,
        resolved=resolved, under_review=under_review,
        recent_complaints=recent, type_counts=type_counts
    )


# ── Admin Notifications ──────────────────────────────────────
@admin_bp.route('/notifications')
def admin_notifications():
    redir = _require_admin()
    if redir: return redir

    notifs = Notification.query.filter_by(user_id=g.admin.id)\
                                .order_by(Notification.created_at.desc()).all()
    Notification.query.filter_by(user_id=g.admin.id, is_read=False)\
                      .update({'is_read': True})
    db.session.commit()
    return render_template('admin/notifications_admin.html', notifications=notifs)


# ── Admin Unread Count API ───────────────────────────────────
@admin_bp.route('/api/unread-count')
def admin_api_unread():
    if not g.admin:
        return jsonify({'count': 0})
    count = Notification.query.filter_by(user_id=g.admin.id, is_read=False).count()
    return jsonify({'count': count})


# ── All Complaints ───────────────────────────────────────────
@admin_bp.route('/complaints')
def all_complaints():
    redir = _require_admin()
    if redir: return redir
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('admin/all_complaints.html', complaints=complaints, now=datetime.utcnow())

# ── Complaint Detail ─────────────────────────────────────────
@admin_bp.route('/complaint/<int:complaint_id>')
def complaint_detail_admin(complaint_id):
    redir = _require_admin()
    if redir: return redir
    c = Complaint.query.get_or_404(complaint_id)
    return render_template('admin/complaint_detail_admin.html', complaint=c)


# ── Admin Reply ──────────────────────────────────────────────
@admin_bp.route('/complaint/<int:complaint_id>/reply', methods=['POST'])
def admin_reply(complaint_id):
    redir = _require_admin()
    if redir: return redir

    message = request.form.get('message', '').strip()
    if not message:
        flash('Reply cannot be empty.', 'warning')
        return redirect(url_for('admin.complaint_detail_admin', complaint_id=complaint_id))

    c = Complaint.query.get_or_404(complaint_id)
    reply = Reply(
        complaint_id = complaint_id,
        user_id      = g.admin.id,
        message      = message,
        role         = 'admin',
        timestamp    = datetime.utcnow()
    )
    db.session.add(reply)
    db.session.flush()

    consumer = User.query.get(c.user_id)
    if consumer:
        notify_user_admin_reply(c, consumer)

    db.session.commit()
    flash('Reply sent to consumer.', 'success')
    return redirect(url_for('admin.complaint_detail_admin', complaint_id=complaint_id))


# ── Update Status ────────────────────────────────────────────
@admin_bp.route('/complaint/<int:complaint_id>/status', methods=['POST'])
def update_status(complaint_id):
    redir = _require_admin()
    if redir: return redir

    new_status = request.form.get('status', '').strip()
    if new_status not in ['Pending', 'Under Review', 'Resolved']:
        flash('Invalid status.', 'warning')
        return redirect(url_for('admin.complaint_detail_admin', complaint_id=complaint_id))

    c = Complaint.query.get_or_404(complaint_id)
    c.status = new_status
    db.session.flush()

    consumer = User.query.get(c.user_id)
    if consumer:
        notify_user_status_change(c, consumer, new_status)

    db.session.commit()
    flash(f'Status updated to "{new_status}".', 'success')
    return redirect(url_for('admin.complaint_detail_admin', complaint_id=complaint_id))


# ── Manage Users ─────────────────────────────────────────────
@admin_bp.route('/users')
def manage_users():
    redir = _require_admin()
    if redir: return redir

    search = request.args.get('search', '').strip()
    if search:
        users = User.query.filter(
            (User.name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.consumer_id.ilike(f'%{search}%'))
        ).all()
    else:
        users = User.query.filter_by(role='admin').order_by(User.id).all()

    return render_template('admin/manage_users.html', users=users, search=search)


# ── View Complaints by User ──────────────────────────────────
@admin_bp.route('/user/<int:user_id>/complaints')
def user_complaints(user_id):
    redir = _require_admin()
    if redir: return redir

    # Block viewing another admin's complaints
    user = User.query.get_or_404(user_id)
    if user.role == 'admin' and user.id != g.admin.id:
        flash('You cannot view another administrator\'s data.', 'danger')
        return redirect(url_for('admin.manage_users'))

    complaints = Complaint.query.filter_by(user_id=user_id)\
                                .order_by(Complaint.created_at.desc()).all()
    return render_template('admin/user_complaints.html', user=user, complaints=complaints)


# ── Delete User ──────────────────────────────────────────────
@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    redir = _require_admin()
    if redir: return redir

    user = User.query.get_or_404(user_id)

    # Cannot delete own account
    if user_id == g.admin.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))

    # Cannot delete another admin
    if user.role == 'admin':
        flash('You cannot delete another administrator account.', 'danger')
        return redirect(url_for('admin.manage_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.name}" deleted successfully.', 'info')
    return redirect(url_for('admin.manage_users'))


# ── Add Staff Member ─────────────────────────────────────────
# Paste this route inside admin_routes.py
# Place it after the manage_users route

@admin_bp.route('/add-staff', methods=['POST'])
def add_staff():
    redir = _require_admin()
    if redir: return redir

    name     = request.form.get('name',     '').strip()
    email    = request.form.get('email',    '').strip().lower()
    mobile   = request.form.get('mobile',   '').strip()
    password = request.form.get('password', '').strip()
    role     = request.form.get('role',     '').strip()

    # Validations
    if not all([name, email, mobile, password, role]):
        flash('All fields are required.', 'warning')
        return redirect(url_for('admin.manage_users'))

    if role not in ['staff']:
        flash('Invalid role selected.', 'danger')
        return redirect(url_for('admin.manage_users'))

    if len(mobile) != 10 or not mobile.isdigit():
        flash('Enter a valid 10-digit mobile number.', 'danger')
        return redirect(url_for('admin.manage_users'))

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect(url_for('admin.manage_users'))

    if User.query.filter_by(email=email).first():
        flash(f'Email "{email}" is already registered.', 'warning')
        return redirect(url_for('admin.manage_users'))

    if User.query.filter_by(mobile=mobile).first():
        flash(f'Mobile number "{mobile}" is already registered.', 'warning')
        return redirect(url_for('admin.manage_users'))

    new_staff = User(
        name        = name,
        email       = email,
        mobile      = mobile,
        password    = generate_password_hash(password),
        consumer_id = generate_consumer_id('staff'),
        role        = 'staff'
    )

    try:
        db.session.add(new_staff)
        db.session.commit()
        flash(f'Staff member "{name}" added successfully. '
              f'Staff ID: {new_staff.consumer_id}', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Failed to add staff. Email or mobile may already exist.', 'danger')

    return redirect(url_for('admin.manage_users'))
