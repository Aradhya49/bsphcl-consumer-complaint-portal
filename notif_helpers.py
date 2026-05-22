"""
notif_helpers.py
────────────────
Helper functions to create notifications.
Import and call these from main_app.py and admin_routes.py
whenever a relevant event occurs.
"""

from extensions import db
from models import Notification, User
from datetime import datetime


def _create(user_id, notif_type, title, message, complaint_id=None):
    """Internal: create and save one notification."""
    n = Notification(
        user_id      = user_id,
        complaint_id = complaint_id,
        notif_type   = notif_type,
        title        = title,
        message      = message,
        is_read      = False,
        created_at   = datetime.utcnow()
    )
    db.session.add(n)
    # commit is done by the caller after all db work


def notify_admins_new_complaint(complaint, consumer):
    """
    Called when a user files a new complaint.
    Sends notification to ALL admin users.
    """
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        _create(
            user_id      = admin.id,
            notif_type   = 'new_complaint',
            title        = f'New Complaint Filed – CMP{complaint.id:04d}',
            message      = (f'Consumer {consumer.name} ({consumer.consumer_id}) '
                            f'has filed a new {complaint.complaint_type} complaint. '
                            f'Complaint ID: CMP{complaint.id:04d}.'),
            complaint_id = complaint.id
        )


def notify_admins_user_reply(complaint, consumer):
    """
    Called when a user adds a reply/follow-up to their complaint.
    Sends notification to ALL admin users.
    """
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        _create(
            user_id      = admin.id,
            notif_type   = 'user_reply',
            title        = f'Consumer Reply – CMP{complaint.id:04d}',
            message      = (f'Consumer {consumer.name} ({consumer.consumer_id}) '
                            f'has added a follow-up message to '
                            f'CMP{complaint.id:04d} ({complaint.complaint_type}).'),
            complaint_id = complaint.id
        )


def notify_user_admin_reply(complaint, consumer):
    """
    Called when admin sends a reply to a complaint.
    Sends notification to the complaint owner (consumer).
    """
    _create(
        user_id      = consumer.id,
        notif_type   = 'admin_reply',
        title        = f'Admin Replied to Your Complaint – CMP{complaint.id:04d}',
        message      = (f'BSPHCL Admin has replied to your '
                        f'{complaint.complaint_type} complaint '
                        f'(CMP{complaint.id:04d}). '
                        f'Please check the complaint details for the response.'),
        complaint_id = complaint.id
    )


def notify_user_status_change(complaint, consumer, new_status):
    """
    Called when admin changes complaint status.
    Sends notification to the complaint owner.
    """
    status_msg = {
        'Pending':      'Your complaint has been reset to Pending status.',
        'Under Review': 'Your complaint is now Under Review by BSPHCL officials.',
        'Resolved':     'Your complaint has been marked as Resolved by BSPHCL. '
                        'Please check the complaint details.'
    }.get(new_status, f'Your complaint status has been updated to {new_status}.')

    _create(
        user_id      = consumer.id,
        notif_type   = 'status_update',
        title        = f'Complaint Status Updated – CMP{complaint.id:04d}',
        message      = (f'Status of your {complaint.complaint_type} complaint '
                        f'(CMP{complaint.id:04d}) has been changed to '
                        f'"{new_status}". {status_msg}'),
        complaint_id = complaint.id
    )


def notify_admins_new_user(new_user):
    """
    Called when a new consumer registers.
    Sends notification to ALL admin users.
    """
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        _create(
            user_id      = admin.id,
            notif_type   = 'new_user',
            title        = 'New Consumer Registered',
            message      = (f'A new consumer has registered on the portal. '
                            f'Name: {new_user.name}, '
                            f'Consumer ID: {new_user.consumer_id}, '
                            f'District: {new_user.district or "Not provided"}.'),
            complaint_id = None
        )


def get_unread_count(user_id):
    """Returns count of unread notifications for a user."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()
