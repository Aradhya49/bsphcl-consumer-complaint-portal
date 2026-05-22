"""
init_db.py
──────────
Run this once after setting up the project to:
  1. Create all database tables.
  2. Optionally seed one default admin account.

Usage:
    python init_db.py
"""

from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from utils import generate_consumer_id

app = create_app()

with app.app_context():
    db.create_all()
    print('[OK] All tables created.')

    # ── Seed default admin (only if no admin exists yet) ──────
    if not User.query.filter_by(role='admin').first():
        default_admin = User(
            name        = 'BSPHCL Admin',
            email       = 'admin@bsphcl.co.in',
            mobile      = '9000000000',
            password    = generate_password_hash('Admin@123'),
            consumer_id = 'ADMIN000001',
            role        = 'admin'
        )
        db.session.add(default_admin)
        db.session.commit()
        print('[OK] Default admin created.')
        print('     Email   : admin@bsphcl.co.in')
        print('     Password: Admin@123')
        print('     !! Change this password immediately after first login !!')
    else:
        print('[INFO] Admin already exists – skipping seed.')

    print('[DONE] Database initialisation complete.')
