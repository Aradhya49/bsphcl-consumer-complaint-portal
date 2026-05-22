"""
update_admin_password.py
─────────────────────────
Run this ONCE from VS Code terminal to set the admin password properly.

Usage:
    cd bsphcl_backend
    venv\Scripts\activate
    python update_admin_password.py
"""

from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    admin = User.query.filter_by(role='admin').first()

    if admin:
        admin.password    = generate_password_hash('Admin@2025')
        admin.name        = 'BSPHCL Admin'
        admin.email       = 'Bsphcl_admin@bsphcl.co.in'
        admin.consumer_id = 'BSPHCL_ADMIN'
        db.session.commit()
        print('[OK] Admin credentials updated successfully.')
        print('     Login Email : Bsphcl_admin@bsphcl.co.in')
        print('     Password    : Admin@2025')
    else:
        print('[ERROR] No admin found in database. Run init_db.py first.')
