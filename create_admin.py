from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Find any admin user
    admin = User.query.filter_by(role='admin').first()
    
    if admin:
        print(f'Found admin: {admin.email}')
        admin.password = generate_password_hash('Admin@2024')
        db.session.commit()
        print(f'Password reset! Login with: {admin.email} / Admin@2024')
    else:
        print('No admin found!')