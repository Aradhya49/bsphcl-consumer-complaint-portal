import os
from flask import Flask
from config import Config
from extensions import db, mail, migrate
from main_app import main_bp
from admin_routes import admin_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER',
                os.path.join(os.getcwd(), 'static', 'uploads')),
                exist_ok=True)

    # Initialise extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Inject current year into all templates
    @app.context_processor
    def inject_year():
        from datetime import datetime
        return {'current_year': datetime.utcnow().year}

    return app


# ── Load .env file for local development ─────────────────────
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ.setdefault(key.strip(), value.strip())


load_env()
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('[BSPHCL] Database tables created.')
    app.run(debug=True, host='0.0.0.0', port=5000)
