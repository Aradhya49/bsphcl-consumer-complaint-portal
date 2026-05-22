from extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(150), unique=True, nullable=False)
    mobile      = db.Column(db.String(15),  unique=True, nullable=False)
    password    = db.Column(db.String(256), nullable=False)
    consumer_id = db.Column(db.String(20),  unique=True, nullable=False)
    role        = db.Column(db.String(20),  default='user')
    district    = db.Column(db.String(100), nullable=True)
    address     = db.Column(db.Text,        nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)   # NEW
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    complaints    = db.relationship('Complaint',    backref='user', lazy=True, cascade='all, delete-orphan')
    replies       = db.relationship('Reply',        backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.consumer_id} – {self.name}>'


class Complaint(db.Model):
    __tablename__ = 'complaints'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    complaint_type = db.Column(db.String(100))
    subcategory    = db.Column(db.String(100))
    description    = db.Column(db.Text)
    status         = db.Column(db.String(50), default='Pending')
    priority       = db.Column(db.String(20), default='Medium')
    attachment     = db.Column(db.String(255))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    date_submitted = db.synonym('created_at')
    replies        = db.relationship('Reply', backref='complaint', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Complaint CMP{self.id:04d}>'


class Reply(db.Model):
    __tablename__ = 'replies'

    id           = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=False)
    message      = db.Column(db.Text, nullable=False)
    role         = db.Column(db.String(20))
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reply by {self.role} on Complaint {self.complaint_id}>'


class OTP(db.Model):
    __tablename__ = 'otp'

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(150), nullable=False)
    otp        = db.Column(db.String(6),   nullable=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        return f'<OTP for {self.email}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id           = db.Column(db.Integer,     primary_key=True)
    user_id      = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)
    complaint_id = db.Column(db.Integer,     nullable=True)
    notif_type   = db.Column(db.String(50),  nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    message      = db.Column(db.Text,        nullable=False)
    is_read      = db.Column(db.Boolean,     default=False)
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification [{self.notif_type}] user={self.user_id}>'
